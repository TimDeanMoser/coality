"""Coality - Web frontend functionality"""
import json
import random
import string
import subprocess
import glob
from datetime import datetime
from flask import Flask
from flask import render_template, request, flash, send_file
from git import Repo, rmtree
from json_extract import json_extractor, get_files

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters + string.digits, k=12))

@app.route("/")
@app.route("/home")
def home():
    """Initial page rendering"""
    return render_template(
        "index.html",
        json_files=glob.glob1("outputs/", "*.json")
        )

@app.route("/result", methods=["POST"])
def create_result():
    """Handles form submission + sending the JSON output data to the results page"""
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
        subprocess.run(f"""python3 quality_assessment/src/main.py {project_path}
        outputs/{repo_name}_{timestamp}.json
        models/
        --label {comment_label}
        --language {comment_language}""".split(),
        check=True)
    except subprocess.CalledProcessError:
        flash("An error occurred. Try checking your project path.")
    # Delete the cloned repo once finished
    rmtree(project_path)
    # Load the JSON output and send it to the results page
    filename = f"{repo_name}_{timestamp}.json"
    with open(f"outputs/{filename}", encoding="utf-8") as json_data:
        json_output = json.load(json_data)
    return render_template(
        "results.html",
        json_data=json.dumps(json_output),
        json_file_name=filename,
        total_files=len(get_files(json_output, "name")),
        all_files = get_files(json_output, "name"),
        fox_index = json_output["fi"],
        frel = json_output["frel"],
        fkgls = json_output["fkgls"],
        total_comments=len(json_extractor(json_output, "text"))
        )

@app.route("/result/<filename>", methods=["GET"])
def result_fetch(filename):
    """Retrieve the data of a specified JSON file and render it in the results page"""
    with open(f"outputs/{filename}", encoding="utf-8") as json_data:
        json_output = json.load(json_data)
    return render_template(
        "results.html",
        json_data=json.dumps(json_output),
        json_file_name=filename,
        total_files=len(get_files(json_output, "name")),
        all_files = get_files(json_output, "name"),
        fox_index = json_output["fi"],
        frel = json_output["frel"],
        fkgls = json_output["fkgls"],
        total_comments=len(json_extractor(json_output, "text"))
        )

@app.route("/result/download/<filename>", methods=["GET", "POST"])
def download_json(filename):
    """Simple download file function"""
    return send_file(f"outputs/{filename}", as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
