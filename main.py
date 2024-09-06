from flask import Flask, render_template, redirect, request, flash
import requests
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import pandas as pd
import os
from dotenv import load_dotenv

app = Flask(__name__)

mysql = MySQL(app)

path_to_env_file = '.env'

load_dotenv(path_to_env_file)

SECRET_KEY = os.getenv('SECRET_KEY')
USER = os.getenv('DATABASE_USER')
PASSWORD = os.getenv('DATABASE_PASSWORD')
HOST = os.getenv('DATABASE_HOST')
SCHEMA = os.getenv('DATABASE_SCHEMA')

app.config["SECRET_KEY"] = SECRET_KEY
app.config["UPLOAD_FOLDER"] = "static/"
app.config['MYSQL_HOST'] = HOST
app.config['MYSQL_USER'] = USER
app.config['MYSQL_PASSWORD'] = PASSWORD
app.config['MYSQL_DB'] = SCHEMA

key = os.environ.get('dbsecretkey')


def load_exam_answers(exam_csv):
    exam_answers = pd.read_csv(filepath_or_buffer=exam_csv)
    class_name = request.form.get('class_name')
    exam_name = request.form.get('exam_name')
    cursor = mysql.connection.cursor()
    cursor.execute('''INSERT INTO exams(exam_name, class) VALUES(%s, %s) ''', (exam_name, class_name, ))
    cursor.execute('''SELECT id FROM exams WHERE exam_name = %s''', (exam_name, ))
    result = cursor.fetchall()[0][0]
    for index, curr_row in exam_answers.iterrows():
        cursor.execute('''INSERT INTO exam_questions( available_answers, exam_id
                        , question_type, question_number) VALUES(%s, %s, %s, %s)''',
                       ('NA', result, curr_row['Тип въпрос'], curr_row['Въпрос'], ))
        cursor.execute('''SELECT id 
                          FROM exam_questions 
                          WHERE exam_id = %s
                          AND question_type = %s
                          AND question_number = %s''', (result, curr_row['Тип въпрос'], curr_row['Въпрос'], ))
        question_id = cursor.fetchall()[0][0]
        cursor.execute('''INSERT INTO exams_answers(answer, exam_id, question_id, points)
                          VALUES(%s, %s, %s, %s)''', (curr_row['Въпрос'], result, question_id, curr_row['Точки']))

    mysql.connection.commit()
    cursor.close()

    return result


def load_assessment_scale(id_of_exam):
    lower_bound_2 = int(request.form.get('lower_bound_2'))
    upper_bound_2 = int(request.form.get('upper_bound_2'))
    lower_bound_3 = int(request.form.get('lower_bound_3'))
    upper_bound_3 = int(request.form.get('upper_bound_3'))
    lower_bound_4 = int(request.form.get('lower_bound_4'))
    upper_bound_4 = int(request.form.get('upper_bound_4'))
    lower_bound_5 = int(request.form.get('lower_bound_5'))
    upper_bound_5 = int(request.form.get('upper_bound_5'))
    lower_bound_6 = int(request.form.get('lower_bound_6'))
    upper_bound_6 = int(request.form.get('upper_bound_6'))
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO exam_marks_scale VALUES(%s, %s, %s, %s)',
                   (2, lower_bound_2, upper_bound_2, id_of_exam))

    cursor.execute('INSERT INTO exam_marks_scale VALUES(%s, %s, %s, %s)',
                   (3, lower_bound_3, upper_bound_3, id_of_exam))

    cursor.execute('INSERT INTO exam_marks_scale VALUES(%s, %s, %s, %s)',
                   (4, lower_bound_4, upper_bound_4, id_of_exam))

    cursor.execute('INSERT INTO exam_marks_scale VALUES(%s, %s, %s, %s)',
                   (5, lower_bound_5, upper_bound_5, id_of_exam))

    cursor.execute('INSERT INTO exam_marks_scale VALUES(%s, %s, %s, %s)',
                   (6, lower_bound_6, upper_bound_6, id_of_exam))

    mysql.connection.commit()
    cursor.close()


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
        id_of_exam = load_exam_answers(exam_path)
        load_assessment_scale(id_of_exam)
        flash(f"Отговорите за контролно \"{exam_name}\" са успешно заредени", "success")
    return render_template('define_exam.html')


@app.route(rule='/exams', methods=["GET", "POST"])
def exams_page():
    return render_template('exams.html')


@app.route(rule='/exams_results', methods=["GET", "POST"])
def exams_results_page():
    return render_template('exams_results.html')

@app.route(rule='/entry_level', methods=["GET", "POST"])
def entry_level_page():
    if request.method == "POST":
        student_num = request.form.get('student_number')
        student_name = request.form.get('student_name')
        q1_paper_answer = request.form.get('paper_answer')
        q1_metal_answer = request.form.get('metal_answer')
        q1_plastic_answer = request.form.get('plastic_answer')
        q1_wood_answer = request.form.get('wood_answer')
        q2_cylinder_answer = request.form.get('cylinder_answer')
        q2_pyramid_answer = request.form.get('pyramid_answer')
        q2_tent_answer = request.form.get('tent_answer')
        q2_cube_answer = request.form.get('cube_answer')
        q3_will_last_answer = request.form.get('will_last_answer')
        q4_most_resistant_answer = request.form.get('most_resistant_answer')
        q5_paper_property_answer = request.form.get('paper_property_answer')
        q5_metal_property_answer = request.form.get('metal_property_answer')
        q5_rubber_band_property_answer = request.form.get('rubber_band_property_answer')
        q6_cut_instrument_answer = request.form.get('cut_instrument_answer')
        q6_drawing_instrument_answer = request.form.get('drawing_instrument_answer')
        q6_bigovane_instrument_answer = request.form.get('bigovane_instrument_answer')
        q6_drilling_instrument_answer = request.form.get('drilling_instrument_answer')
        q7_stocks_list = request.form.getlist('stocks_list')
        q8_correct_word = request.form.getlist('correct_word')
        q9_call_a_friend = request.form.getlist('call_a_friend')
        print(q1_paper_answer,
                q1_metal_answer,
                q1_plastic_answer,
                q1_wood_answer,
                q2_cylinder_answer,
              q8_correct_word)
    return render_template('first_exam.html')


if __name__ == "__main__":
    app.run()