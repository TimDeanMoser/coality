from flask import Flask, render_template, request, flash
from datetime import datetime
from git import Repo, rmtree
import random
import string
import subprocess

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters + string.digits, k=12))

@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/result", methods=["post"])
def result():
    # First obtain guaranteed form data
    comment_label = request.form["comment_label"]
    comment_language = request.form["language"]
    # Check if a specific project path is specified; redundant feature?
    if "project_path" in request.form:
        project_path = request.form["project_path"]
        repo_name = project_path.split("/")[-1]
    # Otherwise clone the repo
    else:
        timestamp = datetime.now()
        timestamp = timestamp.strftime("%Y%m%d%H%M%S")
        project_path = f"projects/temp{timestamp}"
        repo = Repo.clone_from(request.form["git_url"], project_path)
        repo_name = repo.remotes.origin.url.split(".git")[0].split("/")[-1]
    # Run the main.py script to generate the output as a json file - has to be this way on Ubuntu server
    try:
        subprocess.run(f"python3 quality_assessment/src/main.py {project_path} outputs/{repo_name}_{timestamp}.json models/ --label {comment_label} --language {comment_language}",
        shell=True)
    except subprocess.CalledProcessError:
        flash("An error occurred. Try checking your project path.")
    # Delete the cloned repo once finished
    rmtree(project_path)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
