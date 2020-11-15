import csv
import pandas as pd
import os
import sys


CSV_BASE_DIR = os.path.abspath('./csv')


def get_csv_files(CSV_DIR):
    CSV_DIR = CSV_BASE_DIR + CSV_DIR
    csv_directory = os.listdir(CSV_DIR)
    csv_title_list = []
    for f in csv_directory:
        if ('.csv' in f) and ('mentions' in f):
            csv_title_list.append(f.replace('.csv', ''))

    return csv_title_list


def make_rev():
    """
        원본 csv 파일에서 필요한 column 만 간추린 rev csv 파일 생성 함수
    """
    # 원본 mentions 파일 목록 가져오기
    CSV_DIR = '/mentions/'
    csv_title_list = get_csv_files(CSV_DIR)

    # header index 체크
    for csv_idx, csv_title in enumerate(csv_title_list):
        with open(CSV_BASE_DIR + "/mentions/{}.csv".format(csv_title), 'r', encoding='utf-8') as csv_file:
            lines = csv_file.readlines()
            for line_idx, line in enumerate(lines):
                if len(line) == 1:
                    csv_title_list[csv_idx] = [csv_title_list[csv_idx]] + [line_idx]
                    break

    # 필요한 column list
    selected_columns = ['Query Id', 'Query Name', 'Date', 'Title', 'Url', \
                        'Sentiment', 'Language', 'Country', 'Author', 'Full Name', 'Gender']
    # 필요한 column 만 뽑아낸 ~_rev.csv 파일 생성
    for csv_title in csv_title_list:
        title, header = csv_title
        rev_title = CSV_BASE_DIR + "/mentions_rev/{}_rev.csv".format(title)
        # 해당 ~_rev.csv 파일이 없으면 생성
        if not os.path.exists(rev_title):
            origin_df = pd.read_csv(CSV_BASE_DIR + "/mentions/{}.csv".format(title), engine='python', header=header, encoding='utf-8')
            rev_df = origin_df[selected_columns]
            rev_df.to_csv(rev_title, index=False)

    print("Finished make_rev.py")


if __name__ == '__main__':
    make_rev()