import tweepy
import csv
import pandas as pd
import os
import sys

import twitter_age.aws.demo as demo

def check_user_list_file(df, user_list_csv_title):
    # user list file 이 없는 경우
    if not os.path.exists(user_list_csv_title):
        # 새로 생성하고 Screen Name, Age 헤더 추가
        with open(user_list_csv_title, 'w+', encoding="utf-8") as user_list_file:
            csv_writer = csv.writer(user_list_file)
            csv_writer.writerow(['Screen Name', 'Age'])
        # pandas로 read
        user_list_df = pd.read_csv(user_list_csv_title, engine='python', header=0)
        # 중복 제거한 user list
        user_list = list(set(df['Author']))
        # Screen Name, Age 초기화
        user_list_df['Screen Name'] = user_list
        user_list_df['Age'] = [str(0) for _ in range(len(user_list))]
        # 다시 write
        user_list_df.to_csv(user_list_csv_title, index=False, columns=['Screen Name', 'Age'])
    # user list file 이 있는 경우
    else:
        # pandas로 read
        user_list_df = pd.read_csv(user_list_csv_title, engine='python', header=0)
        # 기존에 존재하는 user list
        prev_user_list = user_list_df['Screen Name'].tolist()
        # 중복 제거한 현재 user list
        current_user_list = list(set(df['Author']))
        # 기존 + 현재 user list
        new_user_list = list(set(current_user_list) - set(prev_user_list))
        new_user_dict = {
            "Screen Name": new_user_list,
            "Age": [0 for _ in range(len(new_user_list))]
        }
        new_user_df = pd.DataFrame(new_user_dict)
        user_list_df=user_list_df.append(new_user_df, ignore_index=True)
        # 다시 write
        user_list_df.to_csv(user_list_csv_title, index=False, columns=['Screen Name', 'Age'])


def tweepy_function():
    # 트위터 앱의 Keys and Access Tokens 탭 참조(자신의 설정 값을 넣어준다)
    consumer_key = ""
    consumer_secret = ""

    # 1. 인증요청(1차) : 개인 앱 정보
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

    access_token = ""
    access_token_secret= ""

    # 2. access 토큰 요청(2차) - 인증요청 참조변수 이용
    auth.set_access_token(access_token, access_token_secret)

    # 3. twitter API 생성
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    # 4. with pandas
    # pandas 경고 메세지 안뜨게 설정
    pd.set_option('mode.chained_assignment', None)
    # csv 파일들 가져오기
    csv_directory = os.listdir('../csv/mentions/')
    csv_title_list = []
    for f in csv_directory:
        if ('.csv' in f) and ('mentions' in f):
            csv_title_list.append(f.replace('.csv', ''))
    # user list file 이름
    user_list_csv_title = "mentions_user_list.csv"
    for csv_title in csv_title_list:
        # 원본 파일 read
        origin_df = pd.read_csv("../csv/mentions/{}.csv".format(csv_title), engine='python', header=8)
        origin_df.rename(columns = {'Unnamed: 0' : ''}, inplace = True)
        result_csv_title = "{}_result.csv".format(csv_title)
        origin_df.to_csv(result_csv_title, index=False)
        
        # pandas로 read
        df = pd.read_csv(result_csv_title, engine='python', encoding='utf-8')

        # check user list file
        check_user_list_file(df, user_list_csv_title)

        # user list 파일 pandas로 read
        user_list_df = pd.read_csv(user_list_csv_title, engine='python')
        # Screen Name을 key 값으로 하는 dict 생성
        user_dict = { item[0]: str(item[1]) for item in user_list_df.values.tolist() }
        # 복사본 생성
        copied_df = df[:].copy()

        try:
            age_ranges = copied_df["Age"]
        except KeyError:
            copied_df["Age"] = ['Not yet' for _ in range(len(copied_df))]

        # current_cursor = int(current_cursor)
        total_len = len(copied_df["Author"])
        for idx, author in enumerate(copied_df["Author"]):
            print("--- ({} / {}) ---".format(idx+1, total_len))
            print("screen_name >> {}".format(author))
            # 아직 처리가 안된 row인 경우
            if copied_df.loc[idx]['Age'] == 'Not yet':
                # 사진 분석이 안된 경우
                if user_dict[author] == '0':
                    # screen name 으로 twitter api 에서 해당 user info 가져옴
                    try:
                        user = api.get_user(screen_name=author)
                    except:
                        age_range_info = 'unknown'
                        copied_df.loc[:, "Age"][idx] = age_range_info
                        user_dict[author] = age_range_info
                        print("Not found User")
                        print()
                        continue
                    # profile image url 로 aws api 에서 사진 분석 정보 가져옴 
                    profile_image_url = user.profile_image_url.replace('_normal.', '_bigger.')
                    try:
                        result = demo.usage_demo(profile_image_url)
                    except:
                        age_range_info = 'unknown'
                        copied_df.loc[:, "Age"][idx] = age_range_info
                        user_dict[author] = age_range_info
                        print("Invalid Image")
                        print()
                        continue
                    # 만약 사람 얼굴 사진인 경우
                    if result:
                        user_info = result[0]
                        age_range_info = user_info.age_range
                        copied_df.loc[:, "Age"][idx] = user_info.age_range
                        user_dict[author] = user_info.age_range
                        print(profile_image_url)
                        print("age >> {}".format(user_info.age_range))
                        print("gender >> {}".format(user_info.gender))
                        print()
                    # 프로필 사진이 없거나 사람 얼굴 사진이 아닌 경우
                    else:
                        age_range_info = 'unknown'
                        copied_df.loc[:, "Age"][idx] = age_range_info
                        user_dict[author] = age_range_info
                        print("No Profile Image")
                        print()
                # 사진 분석이 되어있는 경우
                else:
                    age_range_info = user_dict[author]
                    copied_df.loc[:, "Age"][idx] = age_range_info
                    print("{} : Already analyzed".format(author))
                    print("age : {}".format(age_range_info))
                    print()

                new_user_list_df = pd.read_csv(user_list_csv_title, engine='python', header=0)
                new_user_list_df['Screen Name'] = list(user_dict.keys())
                new_user_list_df['Age'] = list(user_dict.values())
                new_user_list_df.to_csv(user_list_csv_title, index=False)

        copied_df.to_csv(result_csv_title, encoding="utf-8", index=False)

tweepy_function()