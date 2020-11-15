import tweepy
import csv
import pandas as pd
import os
import sys
import json

from twitter_age.aws import demo
from twitter_age.csv.make_rev import make_rev, get_csv_files

CSV_BASE_DIR = os.path.abspath('./csv')


def check_user_list_file(df, USER_LIST_CSV_DIR):
    """
        user list 파일 유무 체크
        - 없는 경우
            > 새로운 user list 파일 생성 후 초기화
        - 있는 경우
            > 새로운 user 가 있는지 확인 후, 있으면 추가 및 초기화
    """
    # user list file 이 없는 경우
    if not os.path.exists(USER_LIST_CSV_DIR):
        # 새로 생성하고 Screen Name, Age 헤더 추가
        with open(USER_LIST_CSV_DIR, 'w+', encoding="utf-8") as user_list_file:
            csv_writer = csv.writer(user_list_file)
            csv_writer.writerow(['Screen Name', 'Age'])
        # pandas로 read
        user_list_df = pd.read_csv(USER_LIST_CSV_DIR, engine='python', header=0)
        # 중복 제거한 user list
        user_list = list(set(df['Author']))
        # Screen Name, Age 초기화
        user_list_df['Screen Name'] = user_list
        user_list_df['Age'] = [str(0) for _ in range(len(user_list))]
        # 다시 write
        user_list_df.to_csv(USER_LIST_CSV_DIR, index=False, columns=['Screen Name', 'Age'])
    # user list file 이 있는 경우
    else:
        # pandas로 read
        user_list_df = pd.read_csv(USER_LIST_CSV_DIR, engine='python', header=0)
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
        user_list_df.to_csv(USER_LIST_CSV_DIR, index=False, columns=['Screen Name', 'Age'])


def set_twitter_auth():
    """
        twitter api auth 설정
    """
    BASE_DIR = os.path.abspath('.')
    SECRETS_DIR = BASE_DIR + '/secrets.json'
    # 암호키 load
    with open(SECRETS_DIR) as json_file:
        secrets = json.load(json_file)
    # 트위터 앱의 Keys and Access Tokens 탭 참조(자신의 설정 값을 넣어준다)
    consumer_key = secrets['TWITTER_CONSUMER_KEY']
    consumer_secret = secrets['TWITTER_CONSUMER_SECRET_KEY']

    # 1. 인증요청(1차) : 개인 앱 정보
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

    access_token = secrets['TWITTER_ACCESS_TOKEN']
    access_token_secret= secrets['TWITTER_ACCESS_SECRET_TOKEN']

    # 2. access 토큰 요청(2차) - 인증요청 참조변수 이용
    auth.set_access_token(access_token, access_token_secret)

    # 3. twitter API 생성
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    return api


def tweepy_function():
    """
        1. "../csv/metions_rev" 에 있는 csv 파일들 load
        2. (1.) 에서 불러온 각 csv 파일 마다 아래 step 진행
            - Author(Screen Name) list 가져오기
            - tweepy api 를 통해 각 Screen name 에 해당하는 profile image url 가져오기
            - aws rekognition api 를 통해 profile image url 에 해당하는 사진 정보 분석
            - user_list.csv 업데이트
        3. (2.) 가 끝나면 ~_rev_result.csv 업데이트
    """
    # set twitter api auth
    api = set_twitter_auth()
    # pandas 경고 메세지 안뜨게 설정
    pd.set_option('mode.chained_assignment', None)
    # user list file 이름
    USER_LIST_CSV_DIR = os.path.abspath('twitter') + "/mentions_user_list.csv"
    # csv 파일들 가져오기
    CSV_DIR = '/mentions_rev/'
    csv_title_list = get_csv_files(CSV_DIR)
    for csv_title in csv_title_list:
        # 원본 파일 read
        DIR = CSV_BASE_DIR + "{}/{}.csv".format(CSV_DIR, csv_title)
        origin_df = pd.read_csv(DIR, engine='python')
        origin_df.rename(columns = {'Unnamed: 0' : ''}, inplace = True)
        result_csv_title = "/{}_result.csv".format(csv_title)
        result_csv_title = os.path.abspath('twitter') + result_csv_title
        # print(result_csv_title)
        # sys.exit()
        origin_df.to_csv(result_csv_title, index=False)
        
        # pandas로 read
        df = pd.read_csv(result_csv_title, engine='python', encoding='utf-8')

        # check user list file
        check_user_list_file(df, USER_LIST_CSV_DIR)

        # user list 파일 pandas로 read
        user_list_df = pd.read_csv(USER_LIST_CSV_DIR, engine='python')
        # Screen Name을 key 값으로 하는 dict 생성
        user_dict = { item[0]: str(item[1]) for item in user_list_df.values.tolist() }
        # 복사본 생성
        copied_df = df[:].copy()

        try:
            age_ranges = copied_df["Age"]
        except KeyError:
            copied_df["Age"] = ['Not yet' for _ in range(len(copied_df))]

        total_len = len(copied_df["Author"])
        for idx, author in enumerate(copied_df["Author"]):
            print("--- {} ({} / {}) ---".format(csv_title, idx+1, total_len))
            print("screen_name >> {}".format(author))
            # 아직 처리가 안된 row인 경우
            if copied_df.loc[idx]['Age'] == 'Not yet':
                # 사진 분석이 안된 경우
                if user_dict[author] == '0':
                    # screen name 으로 twitter api 에서 해당 user info 가져옴
                    try:
                        user = api.get_user(screen_name=author)
                    except Exception as e:
                        print(e)
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

                # user_list.csv 업데이트
                new_user_list_df = pd.read_csv(USER_LIST_CSV_DIR, engine='python', header=0)
                new_user_list_df['Screen Name'] = list(user_dict.keys())
                new_user_list_df['Age'] = list(user_dict.values())
                new_user_list_df.to_csv(USER_LIST_CSV_DIR, index=False, encoding="utf-8")

        # ~_rev_result.csv 업데이트
        copied_df.to_csv(result_csv_title, encoding="utf-8", index=False)

    print("Finished tweepy_test.py")

if __name__ == '__main__':
    tweepy_function()