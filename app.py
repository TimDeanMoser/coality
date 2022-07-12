import os
import shutil
import requests
import stat
from datetime import datetime

from flask import Flask, request
from git import Repo
from waitress import serve

from quality_assessment.src.main import main as evaluate

app = Flask(__name__)

class CloneException(Exception):
    pass


def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def delete_repo(repo_path):
    # print("deleting")
    # pass
    # uncomment for windows
    # for i in os.listdir(repo_path):
    #     if i.endswith('git'):
    #         tmp = os.path.join(repo_path, i)
    #         while True:
    #             call(['attrib', '-H', tmp])
    #             break
    #         shutil.rmtree(tmp, onerror=on_rm_error)
    shutil.rmtree(repo_path)


@app.route('/rate', methods=['GET'])
def rate():
    if 'git' in request.args:
        git = str(request.args['git'])
    else:
        return "Error: No git field provided. Please specify a git-hub url for cloning.", 400

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        repo_name = git.split("/")[-1].replace(".git", "")
        git_user = git.split("/")[-2]

        r = requests.get(url=f"https://api.github.com/repos/{git_user}/{repo_name}")
        repo_info = r.json()
        print(repo_info)
    except:
        return "Error: Repository not found. Invalid link or lacking permission", 404

    try:
        repo_size = repo_info["size"]
    except KeyError:
        return "Error: could not determine repo size", 404

    if repo_size > 500000:
        return "Error: Repo larger than 500MB", 400

    project_path = f"projects/{repo_name}_{timestamp}"
    try:
        try:
            Repo.clone_from(git, project_path, depth=1)
        except:
            raise CloneException
        res = evaluate(project_path, './outputs/example_output.json', "./quality_assessment/data/models", "", "")
    except CloneException as ce:
        return "Error: Could not clone your repository, invalid link or lacking permissions", 400
    except Exception as e:
        return "Error, could not evaluate your repo", 500
    else:
        return res
    finally:
        delete_repo(project_path)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Flask development server
    # app.run(debug=True, host='0.0.0.0', port=port)
    # Production server
    serve(app, listen=f"*:{port}")
