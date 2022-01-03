from flask import Flask, render_template, request, flash
import json
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
    # First process certain form data and create timestamp
    comment_label = request.form["comment_label"]
    comment_language = request.form["language"]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # Check if a valid project path is specified; redundant feature?
    if "project_path" in request.form and request.form["project_path"].strip() != "":
        project_path = request.form["project_path"]
        repo_name = project_path.split("/")[-1]
    # Check if valid git URL provided
    elif "git_url" in request.form and request.form["git_url"].strip() != "":
        repo_name = request.form["git_url"].split("/")[-1]
        project_path = f"projects/{repo_name}_{timestamp}"
        Repo.clone_from(request.form["git_url"], project_path)
    else:
        flash("Error: No git URL or project path specified.")
        return render_template("index.html")
    # Run the main.py script to generate the output as a json file
    try:
        # Using .split() solves the bug where the Python shell is opened if we pass the function a list
        subprocess.run(f"python3 quality_assessment/src/main.py {project_path} outputs/{repo_name}_{timestamp}.json models/ --label {comment_label} --language {comment_language}".split())
    except subprocess.CalledProcessError:
        flash("An error occurred. Try checking your project path.")
    # Delete the cloned repo once finished
    rmtree(project_path)
    # Load the JSON output and send it to the results page
    json_output = json.load(open(f"outputs/{repo_name}_{timestamp}.json"))
    return render_template(
        "results.html",
        response=json.dumps(json_output, indent=2)
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
