from flask import Flask, render_template, url_for, request
import subprocess

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template("index.html")


@app.route('/result',methods=['POST', 'GET'])
def result():
    subprocess.call(['./quality_assessment/src/main.py', './caffe-master', 'output_c.json', './classification/src/classifiers/models'])
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)