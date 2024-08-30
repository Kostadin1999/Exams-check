from flask import Flask, render_template, redirect, request, flash
import requests
from functionality import load_exam
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["SECRET_KEY"] = "exam_preparation_elena"
app.config["UPLOAD_FOLDER"] = "static/"

@app.route(rule='/')
def index():
    return render_template('base.html')


@app.route(rule='/define_exam', methods=["GET", "POST"])
def define_exam_page():
    if request.method == "POST":
        exam_name = request.form.get("exam_name")
        exam_file = request.files['sel_exam']
        filename = secure_filename(exam_file.filename)
        exam_path = app.config["UPLOAD_FOLDER"] + filename
        exam_file.save(exam_path)
        flash(f"Num of rows in dt is : {load_exam(exam_path)}. The name of the exam is {exam_name}", "success")
    return render_template('define_exam.html')


if __name__ == "__main__":
    app.run()