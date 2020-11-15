# Content

- Twitter Screen Name 목록을 기반으로, 프로필 사진을 통해 각 유저들의 연령 추정

# Requirements

- 분석할 Twitter Screen Name 목록 csv
- Twitter Developer 계정 생성 및 Token
- AWS IAM 생성 및 Token
  - S3FullAccess
  - RekognitionFullAccess

# Install

```
    # 가상환경 생성
    virtualenv 가상환경_이름

    # 가상환경으로 cd
    cd 가상환경_디렉토리

    # git clone
    git clone https://github.com/SimJunSik/twitter_age.git

    # clone 받은 프로젝트 폴더로 cd
    cd twitter_age

    # 가상환경 activate
    [Windows] .\Scripts\activate
    [Linux] source .\bin\activate

    # dependency 설치
    pip install -r requirements.txt
```

# Key & Token Setting

```
    1. twitter_age 디렉토리 안에 아래와 같은 내용으로 secrets.json 생성

    2. 각자 할당 받은 key, token 값 대입
    {
        "AWS_ACCESS_KEY":"",
        "AWS_SECRET_ACCESS_KEY":"",
        "TWITTER_CONSUMER_KEY":"",
        "TWITTER_CONSUMER_SECRET_KEY":"",
        "TWITTER_ACCESS_TOKEN":"",
        "TWITTER_ACCESS_SECRET_TOKEN":""
    }
```

# Run

```
    1. twitter_age/csv/mentions 에 분석할 csv 파일 넣기

    2. 아래 명령어로 실행
        python main.py

    3. 모든 분석이 끝나면 twitter 에 아래와 같은 파일들 생성됨
        - mentions_user_list.csv
        - metions-1_rev_result.csv
        - metions-2_rev_result.csv
        ...
```

# API List

- Twitter API

  - tweepy

- AWS Rekognition
