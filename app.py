import os
import shutil
import stat
from datetime import datetime
from subprocess import call

from flask import Flask, request
from git import Repo

from quality_assessment.src.main import main as evaluate

app = Flask(__name__)


def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def delete_repo(repo_path):
    for i in os.listdir(repo_path):
        if i.endswith('git'):
            tmp = os.path.join(repo_path, i)
            while True:
                call(['attrib', '-H', tmp])
                break
            shutil.rmtree(tmp, onerror=on_rm_error)
    shutil.rmtree(repo_path)


@app.route('/rate', methods=['GET'])
def rate():
    if 'git' in request.args:
        git = str(request.args['git'])
    else:
        return "Error: No git field provided. Please specify a git url."

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    repo_name = git.split("/")[-1]
    project_path = f"projects/{repo_name}_{timestamp}"
    Repo.clone_from(git, project_path, depth=1)
    res = evaluate(project_path, './outputs/example_output.json', "./quality_assessment/data/models", "", "")
    delete_repo(project_path)
    return res


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
