from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import pandas as pd
import os
from dotenv import load_dotenv
import chardet

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

exam_name = ""


def load_exam_answers(exam_csv):
    with open(exam_csv, 'rb') as f:
        result = chardet.detect(f.read())
    exam_answers = pd.read_csv(filepath_or_buffer=exam_csv, encoding=result['encoding'])
    class_name = request.form.get('class_name')
    global exam_name
    cursor = mysql.connection.cursor()
    cursor.execute('''INSERT INTO exams(exam_name, class) VALUES(%s, %s) ''', (exam_name, class_name,))
    cursor.execute('''SELECT id FROM exams WHERE exam_name = %s''', (exam_name,))
    result = cursor.fetchall()[0][0]
    for index, curr_row in exam_answers.iterrows():
        cursor.execute('''INSERT INTO exam_questions( exam_id, question_type, question_number) 
                          VALUES(%s, %s, %s)''',
                       (result, curr_row['Тип въпрос'], curr_row['Въпрос'],))
        cursor.execute('''SELECT id 
                          FROM exam_questions 
                          WHERE exam_id = %s
                          AND question_type = %s
                          AND question_number = %s''',
                       (result, curr_row['Тип въпрос'], curr_row['Въпрос'],))
        question_id = cursor.fetchall()[0][0]
        cursor.execute('''INSERT INTO exams_answers(answer, exam_id, question_id, points)
                          VALUES(%s, %s, %s, %s)''',
                       (curr_row['Отговор'], result, question_id, curr_row['Точки']))

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


def load_final_report(student_class, student_num, student_name, exam_title):
    cursor = mysql.connection.cursor()
    cursor.execute("""select ex.id
                                from exams ex
                                where ex.exam_name = %s
                                and ex.class = %s""",
                   (exam_title, student_class))
    student_ex = cursor.fetchall()[0][0]
    cursor.execute("""INSERT INTO students_results_report(student_id, exam_id, 
                                                                  final_grade, student_name)
                              VALUES(%s, %s, %s, %s)""",
                   (student_num, student_ex, -1, student_name))

    mysql.connection.commit()
    cursor.close()


def get_qst_answer_info(question_number, exam, student_class):
    cursor = mysql.connection.cursor()
    cursor.execute("""select ans.answer,
                             ans.points,
                            qst.question_type
                      from exams_answers ans
                      join exams ex on ex.id = ans.exam_id
                      join exam_questions qst on qst.id = ans.question_id
                      join students_results_report rp on rp.exam_id = ex.id
                      where ex.exam_name = %s
                        and ex.class = %s
                        and qst.question_number = %s""",
                   (exam, student_class, question_number,))
    result = cursor.fetchall()
    question_answer, points, question_type = result[0]
    return question_answer, points, question_type


def check_select_answer(question_number, exam, student_class, student_answer, subsection):
    question_answer, points, question_type = get_qst_answer_info(question_number, exam, student_class)

    question_answer = question_answer.split(';')

    question_answer = [item.split('-') for item in question_answer]

    for curr in question_answer:
        new_arr = []
        for el in curr:
            new_el = el.strip()
            new_arr.append(new_el)
        if new_arr[0] == subsection and new_arr[1] != student_answer:
            return False

    return True


def check_one_choice_answer(question_number, exam, student_class, student_answer):
    question_answer, points, question_type = get_qst_answer_info(question_number, exam, student_class)

    question_answer = question_answer.strip()

    if question_answer != student_answer:
        return False

    return True


def check_multiple_choice_answer(question_number, exam, student_class, student_answer):
    question_answer, points, question_type = get_qst_answer_info(question_number, exam, student_class)

    question_answer = question_answer.split(';')
    question_answer = [item.strip() for item in question_answer]

    if len(question_answer) != len(student_answer) or question_answer == student_answer:
        return False

    return True


def final_mark_update(exam_title, student_num, student_name, student_class, final_points):
    cursor = mysql.connection.cursor()
    cursor.execute("""update students_results_report rep
                              join exams ex on ex.id = rep.exam_id
                              join exam_marks_scale scl on scl.exam_id = ex.id
                              set rep.final_grade = scl.mark
                              where ex.exam_name = %s
                              and rep.student_id = %s
                              and rep.student_name = %s
                              and ex.class = %s
                              and %s between scl.from_points and scl.to_points;""",
                   (exam_title, student_num, student_name, student_class, final_points))

    mysql.connection.commit()
    cursor.close()


@app.route(rule='/')
def index():
    return render_template('base.html')


@app.route(rule='/define_exam', methods=["GET", "POST"])
def define_exam_page():
    if request.method == "POST":
        global exam_name
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
        student_num = request.form.get('stud_num')
        student_name = request.form.get('stud_name')
        student_class = request.form.get('stud_class')
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
        exam_title = request.form.get('entry_lvl')

        load_final_report(student_class=student_class, student_num=student_num,
                          student_name=student_name, exam_title=exam_title)

        final_points = 0

        """Проверка на въпрос 1"""
        paper_answer_res = check_select_answer(1, exam_title,
                                               student_class, q1_paper_answer, 'А')
        metal_answer_res = check_select_answer(1, exam_title,
                                               student_class, q1_metal_answer, 'Б')
        plastic_answer_res = check_select_answer(1, exam_title,
                                                 student_class, q1_plastic_answer, 'В')
        wood_answer_res = check_select_answer(1, exam_title,
                                              student_class, q1_wood_answer, 'Г')

        if paper_answer_res is True \
                and metal_answer_res is True \
                and plastic_answer_res is True \
                and wood_answer_res is True:
            question_answer, points, question_type = get_qst_answer_info(1,
                                                                         exam_title, student_class)
            final_points += points

        """Проверка на въпрос 2"""
        cylinder_answer = check_select_answer(2, exam_title, student_class,
                                              q2_cylinder_answer, 'а')
        pyramid_answer = check_select_answer(2, exam_title, student_class,
                                             q2_pyramid_answer, 'б')
        tent_answer = check_select_answer(2, exam_title, student_class,
                                          q2_tent_answer, 'в')
        cube_answer = check_select_answer(2, exam_title, student_class,
                                          q2_cube_answer, 'г')

        if cylinder_answer is True \
                and pyramid_answer is True \
                and tent_answer is True \
                and cube_answer is True:
            question_answer, points, question_type = get_qst_answer_info(2, exam_title,
                                                                         student_class)
            final_points += points

        """Проверка на въпрос 3"""
        will_last_answer = check_one_choice_answer(3, exam_title, student_class,
                                                   q3_will_last_answer)

        if will_last_answer is True:
            question_answer, points, question_type = get_qst_answer_info(3, exam_title,
                                                                         student_class)
            final_points += points

        """Проверка на въпрос 4"""
        most_resistant_answer = check_one_choice_answer(4, exam_title, student_class,
                                                        q4_most_resistant_answer)

        if most_resistant_answer is True:
            question_answer, points, question_type = get_qst_answer_info(4, exam_title,
                                                                         student_class)
            final_points += points

        """Проверка на въпрос 5"""
        metal_property_answer = check_select_answer(5, exam_title, student_class,
                                                    q5_metal_property_answer, 'А')
        rubber_band_property_answer = check_select_answer(5, exam_title, student_class,
                                                          q5_rubber_band_property_answer, 'Б')
        paper_property_answer = check_select_answer(5, exam_title, student_class,
                                                    q5_paper_property_answer, 'В')

        if metal_property_answer is True \
                and rubber_band_property_answer is True \
                and paper_property_answer is True:
            question_answer, points, question_type = get_qst_answer_info(5, exam_title,
                                                                         student_class)
            final_points += points

        """Проверка на въпрос 6"""
        drawing_instrument_answer = check_select_answer(6, exam_title, student_class,
                                                        q6_drawing_instrument_answer, 'а')
        bigovane_instrument_answer = check_select_answer(6, exam_title, student_class,
                                                         q6_bigovane_instrument_answer, 'б')
        drilling_instrument_answer = check_select_answer(6, exam_title, student_class,
                                                         q6_drilling_instrument_answer, 'в')
        cut_instrument_answer = check_select_answer(6, exam_title, student_class,
                                                    q6_cut_instrument_answer, 'г')

        if drawing_instrument_answer is True \
                and bigovane_instrument_answer is True \
                and drilling_instrument_answer is True \
                and cut_instrument_answer is True:
            question_answer, points, question_type = get_qst_answer_info(6, exam_title,
                                                                         student_class)
            final_points += points

        """Проверка на въпрос 7"""
        stocks_list = check_multiple_choice_answer(7, exam_title,
                                                   student_class, q7_stocks_list)
        if stocks_list is True:
            question_answer, points, question_type = get_qst_answer_info(7, exam_title,
                                                                         student_class)
            final_points += points

        """Проверка на въпрос 8"""
        correct_word = check_multiple_choice_answer(8, exam_title,
                                                    student_class, q8_correct_word)
        if correct_word is True:
            question_answer, points, question_type = get_qst_answer_info(8, exam_title,
                                                                         student_class)
            final_points += points

        final_mark_update(exam_title=exam_title,student_num=student_num,
                          student_name=student_name, student_class=student_class,
                          final_points=final_points)

        flash(f"Вашите отговори бяха успешно записани. Очаквайте вашата оценка в сайта на МОН",
              "success")

    return render_template('first_exam.html')


@app.route(rule='/first_exam_six_grade', methods=["GET", "POST"])
def first_exam_six_grade_page():
    if request.method == 'POST':
        q1_missing_view = request.form.get('missing_view')
        q2_graphical_image = request.form.get('graphical_image')
        q2_not_nature_subjects = request.form.get('not_nature_subjects')
        q3_caliper = request.form.get('caliper')
        q3_scales = request.form.get('scales')
        q3_thermometer = request.form.get('thermometer')
        q4_approp_word_first = request.form.get('approp_word_first')
        q4_approp_word_sec = request.form.get('approp_word_sec')
        q4_approp_word_third = request.form.get('approp_word_third')
        q4_approp_word_fourth = request.form.get('approp_word_fourth')
        q5_prep_operations_group = request.form.getlist('prep_operations_group')
        q5_in_proc_operations_group = request.form.getlist('in_proc_operations_group')
        q5_conn_operations_group = request.form.getlist('conn_operations_group')
        q6_mach_comp_of_first = request.form.getlist('mach_comp_of_first')
        q6_mach_comp_of_sec = request.form.getlist('mach_comp_of_sec')
        q6_mech_comp_of = request.form.getlist('mech_comp_of')
        q7_baking_is = request.form.getlist('baking_is')
        q8_visual_voice_comm = request.form.get('visual_voice_comm')
        q9_econ_problem_main = request.form.get('econ_problem_main')
        q9_econ_act_main_first = request.form.get('econ_act_main_first')
        q9_econ_act_main_sec = request.form.get('econ_act_main_sec')
        q9_econ_act_main_third = request.form.get('econ_act_main_third')
        q9_cash_acc_first = request.form.get('cash_acc_first')
        q9_cash_acc_sec = request.form.get('cash_acc_sec')
        q9_cash_acc_third = request.form.get('cash_acc_third')
        q10_soil_prep_val = request.form.get('soil_prep_val')
        q10_seeds_distrib_val = request.form.get('seeds_distrib_val')
        q10_moistening_val = request.form.get('moistening_val')
        q10_cover_with_soil_val = request.form.get('cover_with_soil_val')
        q10_seed_prep_val = request.form.get('seed_prep_val')
        q10_blackout_val = request.form.get('blackout_val')
        q11_animals_main_cares = request.form.get('animals_main_cares')
    return render_template('first_exam_6_grade.html')


@app.route(rule='/design_and_construction', methods=["GET", "POST"])
def design_and_construction_page():
    return render_template('design_and_construction.html')


if __name__ == "__main__":
    app.run()
