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


def load_exam_answers(exam_csv):
    with open(exam_csv, 'rb') as f:
        result = chardet.detect(f.read())
    exam_answers = pd.read_csv(filepath_or_buffer=exam_csv, encoding=result['encoding'])
    class_name = request.form.get('class_name')
    exam_name = request.form.get('exam_name')
    print(f'Exam name: {exam_name}')
    cursor = mysql.connection.cursor()
    cursor.execute('''INSERT INTO exams(exam_name, class) VALUES(%s, %s) ''', (exam_name, class_name,))
    cursor.execute('''SELECT id FROM exams 
                      WHERE exam_name = %s
                      AND class = %s''', (exam_name, class_name,))
    result = cursor.fetchall()[0][0]
    print(f'Exam id: {result}')
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
    print(f'id of exam: {id_of_exam}')
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
    class_unit = int(student_class[0])
    cursor = mysql.connection.cursor()
    cursor.execute("""select ex.id
                                from exams ex
                                where ex.exam_name = %s
                                and ex.class = %s""",
                   (exam_title, class_unit))
    student_ex = cursor.fetchall()[0][0]
    cursor.execute("""INSERT INTO students_results_report(student_id, exam_id, 
                                                          final_grade, student_name,
                                                          student_class)
                              VALUES(%s, %s, %s, %s, %s)""",
                   (student_num, student_ex, -1, student_name, student_class))

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
                      left join students_results_report rp on rp.exam_id = ex.id
                      where ex.exam_name = %s
                        and ex.class = %s
                        and qst.question_number = %s""",
                   (exam, student_class, question_number,))
    result = cursor.fetchall()
    question_answer, points, question_type = result[0]
    return question_answer, points, question_type


def check_select_answer(question_number, exam, student_class, student_answer, subsection):
    if student_answer is None:
        return False, 0

    question_answer, points, question_type = get_qst_answer_info(question_number, exam, student_class)

    question_answer = question_answer.split(';')

    question_answer = [item.split('-') for item in question_answer]

    for curr in question_answer:
        new_arr = []
        for el in curr:
            new_el = el.strip()
            new_arr.append(new_el)
        if new_arr[0] == subsection and new_arr[1] != student_answer:
            return False, 0
    return True, points


def check_one_choice_answer(question_number, exam, student_class, student_answer):
    if student_answer is None:
        return False, 0

    question_answer, points, question_type = get_qst_answer_info(question_number, exam, student_class)

    question_answer = question_answer.strip()

    if question_answer != student_answer:
        return False, 0

    return True, points


def check_list_of_answers(question_number, exam, student_class, student_answer):
    if student_answer is None:
        return False, 0

    question_answer, points, question_type = get_qst_answer_info(question_number, exam, student_class)

    question_answer = question_answer.split(';')
    question_answer = [item.strip() for item in question_answer]

    if len(question_answer) != len(student_answer) or question_answer != student_answer:
        return False, 0

    return True, points


def diff_num_ans_per_subsection(question_number, exam, student_class, student_answer, subsection):
    if student_answer is None:
        return False, 0

    question_answer, points, question_type = get_qst_answer_info(question_number, exam, student_class)

    question_answer = question_answer.split(';')
    question_answer = [item.split('-') for item in question_answer]

    for curr in question_answer:
        ans = None
        subs = curr[0].strip()
        if subs == subsection:
            if curr[1].find(',') != -1:
                ans = curr[1].split(',')
                ans = [item.strip() for item in ans]
            else:
                ans = curr[1].strip()
            if ans != student_answer:
                return False, 0
            else:
                return True, points


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
        class_unit = int(student_class[0])

        load_final_report(student_class=student_class, student_num=student_num,
                          student_name=student_name, exam_title=exam_title)

        final_points = 0

        """Проверка на въпрос 1"""
        paper_answer_res, question_points = check_select_answer(1, exam_title,
                                                                class_unit, q1_paper_answer, 'А')
        metal_answer_res, question_points = check_select_answer(1, exam_title,
                                                                class_unit, q1_metal_answer, 'Б')
        plastic_answer_res, question_points = check_select_answer(1, exam_title,
                                                                  class_unit, q1_plastic_answer, 'В')
        wood_answer_res, question_points = check_select_answer(1, exam_title,
                                                               class_unit, q1_wood_answer, 'Г')

        if {paper_answer_res, metal_answer_res, plastic_answer_res, wood_answer_res} == {True}:
            final_points += question_points

        """Проверка на въпрос 2"""
        cylinder_answer, question_points = check_select_answer(2, exam_title, class_unit,
                                                               q2_cylinder_answer, 'а')
        pyramid_answer, question_points = check_select_answer(2, exam_title, class_unit,
                                                              q2_pyramid_answer, 'б')
        tent_answer, question_points = check_select_answer(2, exam_title, class_unit,
                                                           q2_tent_answer, 'в')
        cube_answer, question_points = check_select_answer(2, exam_title, class_unit,
                                                           q2_cube_answer, 'г')

        if {cylinder_answer, pyramid_answer, tent_answer, cube_answer} == {True}:
            final_points += question_points

        """Проверка на въпрос 3"""
        will_last_answer, question_points = check_one_choice_answer(3, exam_title, class_unit,
                                                                    q3_will_last_answer)

        if will_last_answer is True:
            final_points += question_points

        """Проверка на въпрос 4"""
        most_resistant_answer, question_points = check_one_choice_answer(4, exam_title, class_unit,
                                                                         q4_most_resistant_answer)

        if most_resistant_answer is True:
            final_points += question_points

        """Проверка на въпрос 5"""
        metal_property_answer, question_points = check_select_answer(5, exam_title, class_unit,
                                                                     q5_metal_property_answer, 'А')
        rubber_band_property_answer, question_points = check_select_answer(5, exam_title, class_unit,
                                                                           q5_rubber_band_property_answer, 'Б')
        paper_property_answer, question_points = check_select_answer(5, exam_title, class_unit,
                                                                     q5_paper_property_answer, 'В')

        if {metal_property_answer, rubber_band_property_answer, paper_property_answer} == {True}:
            final_points += question_points

        """Проверка на въпрос 6"""
        drawing_instrument_answer, question_points = check_select_answer(6, exam_title, class_unit,
                                                                         q6_drawing_instrument_answer, 'а')
        bigovane_instrument_answer, question_points = check_select_answer(6, exam_title, class_unit,
                                                                          q6_bigovane_instrument_answer, 'б')
        drilling_instrument_answer, question_points = check_select_answer(6, exam_title, class_unit,
                                                                          q6_drilling_instrument_answer, 'в')
        cut_instrument_answer, question_points = check_select_answer(6, exam_title, class_unit,
                                                                     q6_cut_instrument_answer, 'г')

        if {drawing_instrument_answer,
            bigovane_instrument_answer,
            drilling_instrument_answer,
            cut_instrument_answer} == {True}:
            final_points += question_points

        """Проверка на въпрос 7"""
        stocks_list, question_points = check_list_of_answers(7, exam_title,
                                                             class_unit, q7_stocks_list)
        if stocks_list is True:
            final_points += question_points

        """Проверка на въпрос 8"""
        correct_word, question_points = check_list_of_answers(8, exam_title,
                                                              class_unit, q8_correct_word)
        if correct_word is True:
            final_points += question_points

        """Проверка на въпрос 9"""
        call_a_friend, question_points = check_one_choice_answer(question_number=9,
                                                                 exam=exam_title,
                                                                 student_class=class_unit,
                                                                 student_answer=q9_call_a_friend)

        if call_a_friend is True:
            final_points += question_points

        final_mark_update(exam_title=exam_title, student_num=student_num,
                          student_name=student_name, student_class=student_class,
                          final_points=final_points)

        flash(f"Вашите отговори бяха успешно записани. Очаквайте вашата оценка в сайта на МОН",
              "success")

    return render_template('first_exam.html')


@app.route(rule='/first_exam_six_grade', methods=["GET", "POST"])
def first_exam_six_grade_page():
    if request.method == 'POST':
        student_num = request.form.get('stud_num')
        student_name = request.form.get('stud_name')
        student_class = request.form.get('stud_class')
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
        q6_mach_comp_of_first = request.form.get('mach_comp_of_first')
        q6_mach_comp_of_sec = request.form.get('mach_comp_of_sec')
        q6_mach_comp_of_third = request.form.get('mach_comp_of_third')
        q7_baking_is = request.form.get('baking_is')
        q8_visual_voice_comm = request.form.getlist('visual_voice_comm')
        q9_econ_problem_main = request.form.get('econ_problem_main')
        q9_econ_act_main_first = request.form.get('econ_act_main_first')
        q9_econ_act_main_sec = request.form.get('econ_act_main_sec')
        q9_econ_act_main_third = request.form.get('econ_act_main_third')
        q9_cash_acc_first = request.form.get('cash_acc_first')
        q9_cash_acc_sec = request.form.get('cash_acc_sec')
        q9_cash_acc_third = request.form.get('cash_acc_third')
        q10_first_action = request.form.get('first_action')
        q10_second_action = request.form.get('second_action')
        q10_third_action = request.form.get('third_action')
        q10_fourth_action = request.form.get('fourth_action')
        q10_fifth_action = request.form.get('fifth_action')
        q10_sixth_action = request.form.get('sixth_action')
        q11_animals_main_cares = request.form.getlist('animals_main_cares')
        exam_title = request.form.get('entry_lvl_6')
        class_unit = int(student_class[0])
        print(f'student_cl: {class_unit}, exam_title: {exam_title}, question_number: {q2_graphical_image}')

        load_final_report(student_class=student_class, student_num=student_num,
                          student_name=student_name, exam_title=exam_title)

        final_points = 0
        """Проверка за въпрос 1"""
        print(q1_missing_view)
        missing_view, question_points = check_one_choice_answer(1, exam_title,
                                                                class_unit, q1_missing_view)
        if missing_view is True:
            final_points += question_points

        print(f'final points after question 1: {final_points}')

        """Проверка за въпрос 2"""
        graphical_image, question_points = check_select_answer(2, exam_title, class_unit,
                                                               q2_graphical_image, 'А')
        not_nature_subjects, question_points = check_select_answer(2, exam_title, class_unit,
                                                                   q2_not_nature_subjects, 'Б')
        if {graphical_image, not_nature_subjects} == {True}:
            final_points += question_points

        print(f'final points after question 2: {final_points}')

        """Проверка за въпрос 3"""
        caliper, question_points = check_select_answer(3, exam_title, class_unit,
                                                       q3_caliper, 'А')
        scales, question_points = check_select_answer(3, exam_title, class_unit,
                                                      q3_scales, 'Б')
        thermometer, question_points = check_select_answer(3, exam_title, class_unit,
                                                           q3_thermometer, 'В')
        if {caliper, scales, thermometer} == {True}:
            final_points += question_points

        print(f'final points after question 3: {final_points}')

        """Проверка за въпрос 4"""
        appropriate_words = []
        appropriate_words.extend([q4_approp_word_first, q4_approp_word_sec,
                                  q4_approp_word_third, q4_approp_word_fourth])
        question_4, question_points = check_list_of_answers(question_number=4,
                                                            exam=exam_title,
                                                            student_class=class_unit,
                                                            student_answer=appropriate_words)
        if question_4 is True:
            final_points += question_points

        print(f'final points after question 4: {final_points}')

        """Проверка за въпрос 5"""
        prep_operations_group, question_points = check_list_of_answers(5, exam_title, class_unit,
                                                                       q5_prep_operations_group)
        in_proc_operations_group, question_points = check_list_of_answers(5, exam_title, class_unit,
                                                                          q5_in_proc_operations_group)
        conn_operations_group, question_points = check_list_of_answers(5, exam_title, class_unit,
                                                                       q5_conn_operations_group)
        if {prep_operations_group, in_proc_operations_group, conn_operations_group} == {True}:
            final_points += question_points

        print(f'final points after question 5: {final_points}')

        """Проверка за въпрос 6"""
        first_sentence = [q6_mach_comp_of_first, q6_mach_comp_of_sec]

        first_sentence_answer, question_points = diff_num_ans_per_subsection(question_number=6,
                                                                             exam=exam_title,
                                                                             student_class=class_unit,
                                                                             student_answer=first_sentence,
                                                                             subsection='А')

        second_sentence_answer, question_points = diff_num_ans_per_subsection(question_number=6,
                                                                              exam=exam_title,
                                                                              student_class=class_unit,
                                                                              student_answer=q6_mach_comp_of_third,
                                                                              subsection='Б')

        if {first_sentence_answer, second_sentence_answer} == {True}:
            final_points += question_points

        print(f'final points after question 6: {final_points}')
        """Проверка за въпрос 7"""
        baking_is, question_points = check_one_choice_answer(question_number=7,
                                                             exam=exam_title,
                                                             student_class=class_unit,
                                                             student_answer=q7_baking_is)
        if baking_is is True:
            final_points += question_points

        print(f'final points after question 7: {final_points}')
        """Проверка за въпрос 8"""
        visual_voice_comm, question_points = check_list_of_answers(question_number=8,
                                                                   exam=exam_title,
                                                                   student_class=class_unit,
                                                                   student_answer=q8_visual_voice_comm)
        if visual_voice_comm is True:
            final_points += question_points

        print(f'final points after question 8: {final_points}')
        """Проверка за въпрос 9"""
        first_sentence_q9, question_points = diff_num_ans_per_subsection(question_number=9,
                                                                         exam=exam_title,
                                                                         student_class=class_unit,
                                                                         student_answer=q9_econ_problem_main,
                                                                         subsection='А')

        second_sentence_q9_answer = [q9_econ_act_main_first,
                                     q9_econ_act_main_sec,
                                     q9_econ_act_main_third]
        second_sentence_q9, question_points = diff_num_ans_per_subsection(question_number=9,
                                                                          exam=exam_title,
                                                                          student_class=class_unit,
                                                                          student_answer=second_sentence_q9_answer,
                                                                          subsection='Б')

        third_sentence_q9_answer = [q9_cash_acc_first,
                                    q9_cash_acc_sec,
                                    q9_cash_acc_third]

        third_sentence_q9, question_points = diff_num_ans_per_subsection(question_number=9,
                                                                         exam=exam_title,
                                                                         student_class=class_unit,
                                                                         student_answer=third_sentence_q9_answer,
                                                                         subsection='В')

        if {first_sentence_q9, second_sentence_q9, third_sentence_q9} == {True}:
            final_points += question_points

        print(f'final points after question 9: {final_points}')
        """Проверка за въпрос 10"""
        question_10_answer = [q10_first_action, q10_second_action, q10_third_action,
                              q10_fourth_action, q10_fifth_action, q10_sixth_action]
        question_10, question_points = check_list_of_answers(question_number=10,
                                                             exam=exam_title,
                                                             student_class=class_unit,
                                                             student_answer=question_10_answer)
        if question_10 is True:
            final_points += question_points

        print(f'final points after question 10: {final_points}')
        """Проверка за въпрос 11"""
        animals_main_cares, question_points = check_list_of_answers(question_number=11,
                                                                    exam=exam_title,
                                                                    student_class=class_unit,
                                                                    student_answer=q11_animals_main_cares)
        if animals_main_cares is True:
            final_points += question_points

        print(f'final points after question 11: {final_points}')

        final_mark_update(exam_title=exam_title, student_num=student_num,
                          student_name=student_name, student_class=student_class,
                          final_points=final_points)

        flash(f"Вашите отговори бяха успешно записани. Очаквайте вашата оценка в сайта на МОН",
              "success")

    return render_template('first_exam_6_grade.html')


@app.route(rule='/design_and_construction', methods=["GET", "POST"])
def design_and_construction_page():
    return render_template('design_and_construction.html')


if __name__ == "__main__":
    app.run()
