from flask import Flask, render_template, url_for, request, flash
import subprocess
import random
import string

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")


@app.route('/result',methods=['POST'])
def result():
    project_path = request.form['project_path']
    try:
        stdout = subprocess.run(f"python quality_assessment/src/main.py {project_path} outputs/output.json models/ --label {request.form['comment_label']} --language {request.form['language']}", check=True, capture_output=True, text=True).stdout
        flash(stdout)
    except subprocess.CalledProcessError:
        flash('An error occurred. Try checking your project path.')
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
