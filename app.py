from flask import Flask, render_template, url_for, request
import subprocess

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")


@app.route('/result',methods=['POST'])
def result():
    project_path = request.form['project_path']
    print(project_path)
    subprocess.run(f"python3 quality_assessment/src/main.py {project_path} outputs/output.json models/ --label {request.form['comment_label']} --language {request.form['language']}", shell=True)
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
