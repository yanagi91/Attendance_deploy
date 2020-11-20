import os
from flask import Flask, render_template, request, url_for, redirect
import base64
from PIL import Image
from io import BytesIO

from AZURE import identify
from DB import attendance_db as db


app = Flask(__name__)


@app.route('/')
def index():
    global dec_img
    dec_img = ''
    return render_template('index.html')


@app.context_processor
def override_url_for():
    """staticの画像の更新用"""
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    # 判定後の画像の保存を上書きしているためhtmlの画像を更新する処理
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.route('/identify/<taikin>')
def main(taikin=None):
    global attendance_data
    # 選択した出退勤情報を取得
    attendance_data = taikin
    return render_template('sebcam.html')


@app.route('/image_ajax', methods=['POST'])
def set_data():
    global result_name, rate, attendance_data
    enc_data  = request.form['img']
    #dec_data = base64.b64decode( enc_data )              # これではエラー  下記対応↓
    dec_data = base64.b64decode( enc_data.split(',')[1] ) # 環境依存の様(","で区切って本体をdecode)
    
    # 判定用の画像を保存
    dec_img = BytesIO(dec_data)
    img  = Image.open(dec_img)
    img_path = 'static/images/image.jpg'
    img.save(img_path)
    img_path = './static/images/image.jpg'
    result_rate = '検出できませんでした'
    # 顔の判定
    result_name, rate = identify.start_identify_faces(img_path)
    if result_name:
        if result_name == None:
            result_name = ''
        else:
            result_rate = rate + '%'  
    return render_template('setdata.html', result_name=result_name, rate=result_rate)


@app.route('/result')
def sub():
    db.add_attendance_db(result_name, rate, attendance_data)     # データベースの保存
    db_info = db.get_infomation_attendance()                     # データベースの取得
    return render_template(
        'identify.html', taikin=attendance_data, result_name=result_name, rate=rate, db_info=db_info)


if __name__ == '__main__':
    app.run(debug=True)
