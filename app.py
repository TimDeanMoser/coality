from flask import Flask, render_template, url_for, request, flash
from git import Repo, rmtree
import random
import string
import subprocess

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")

@app.route('/result',methods=['POST'])
def result():
    if 'project_path' in request.form:
        path = request.form['project_path']
    else:
        Repo.clone_from(request.form['git_url'], 'projects/temp')
        path = 'projects/temp'
    try:
        stdout = subprocess.run(f"python quality_assessment/src/main.py {path} outputs/output.json models/ --label {request.form['comment_label']} --language {request.form['language']}", check=True, capture_output=True, text=True).stdout
        flash(stdout)
    except subprocess.CalledProcessError:
        flash('An error occurred. Try checking your project path.')
    rmtree('projects/temp')
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
