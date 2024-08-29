from flask import Flask, render_template, redirect
import requests

app = Flask(__name__)

app.config["SECRET_KEY"] = "exam_preparation_elena"


@app.route(rule='/')
def index():
    return render_template('base.html')


@app.route(rule='/define_exam')
def define_exam_page():
    return render_template('define_exam.html')


if __name__ == "__main__":
    app.run()