import datetime
import os
import random
import pymysql.cursors
from google.cloud import secretmanager

project_id = ''
secret_name = ''
secret_ver = ''

client = secretmanager.SecretManagerServiceClient()

name = client.secret_version_path(
    project_id, secret_name, secret_ver)  # シークレットマネージャーのアドレスの取得
response = client.access_secret_version(name)

payload = response.payload.data.decode('UTF-8')

db_config = {
    'host': '',
    'db': 'attendance',  # Database Name
    'user': 'root',
    'passwd': payload,
    'unix_socket': '',
    'charset': 'utf8',
}

try:
    # 接続
    conn = pymysql.connect(host=db_config['host'], db=db_config['db'], user=db_config['user'],
                           passwd=db_config['passwd'], unix_socket=db_config['unix_socket'], charset=db_config['charset'])
except pymysql.Error as ex:
    print('MySQL Error: ', ex)

# カーソルの取得
cursor = conn.cursor()

# table作成
# ログイン情報テーブル
cursor.execute(""" CREATE TABLE IF NOT EXISTS login_info(
    id INT AUTO_INCREMENT NOT NULL,
    set_login_name TEXT NOT NULL,
    set_password TEXT NOT NULL,
    PRIMARY KEY(id)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci """)

cursor.execute(""" CREATE TABLE IF NOT EXISTS attendance_db (
    id INT AUTO_INCREMENT NOT NULL,
    name TEXT NOT NULL,
    rate INT NOT NULL,
    attendance_data TEXT NOT NULL,
    time_now DATETIME NOT NULL,
    PRIMARY KEY(id)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci """)


def add_attendance_db(name, rate, attendance_data):
    if name and rate and attendance_data:
        # 出退勤情報を作成
        cursor.execute(
            """INSERT INTO attendance_db(name, rate, attendance_data, time_now)
                        VALUES (%s, %s, %s, %s)""",
            (name, int(float(rate)), attendance_data, datetime.datetime.now()))
        conn.commit()
    else:
        raise('正しく読み込まれませんでした')


def get_infomation_attendance():
    # 辞書型のカーソルを取得
    dict_cursor = conn.cursor(pymysql.cursors.DictCursor)
    # id の降順で50まで取得
    dict_cursor.execute("SELECT* from attendance_db ORDER BY id DESC")

    result = dict_cursor.fetchmany(size=50)
    return result


def hoge():
    # 50件表示されるか試すための50件分ランダム出勤情報を作成
    path = '../AZURE/image'
    name_list = os.listdir(path)
    attendance_data = ['出勤', '退勤']
    for i in range(50):
        a = random.randint(0, 12)
        add_attendance_db(name_list[a], 100, attendance_data[i % 2])


if __name__ == '__main__':
    hoge()
