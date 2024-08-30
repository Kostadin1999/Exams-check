import pandas as pd

def load_exam(exam_csv):
    exam_answers = pd.read_csv(filepath_or_buffer=exam_csv)
    print(exam_answers.size)
