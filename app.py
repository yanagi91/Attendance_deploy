import os
from flask import Flask, render_template, request, url_for, redirect, flash
from werkzeug.utils import secure_filename
import base64
from PIL import Image
from io import BytesIO
import numpy as np

from AZURE import identify, train
from DB import attendance_db as db
import pyocr_test as pyocr
import dlib_cv2 as dlcv


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png']) # 拡張子の設定 ここで設定したものしか読み込まない


@app.route('/')
def index():
    return render_template('index.html')


def allwed_file(filename):
    # ファイルの拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/training', methods=['GET', "POST"])
def training():
    # 人物を学習
    if request.method == 'POST':
        # ファイルのチェック
        if 'file1' not in request.files:
            flash('ファイルがありません', 'error')
            return redirect('/training')

        i = 0
        for i in range(len(request.files)):
            # ファイルを取得
            file = request.files['file{}'.format(i)]
            if not file:
                break
            if file.filename == '':
                flash('ファイルがありません', 'error')
                return redirect('/training')

            train_name = request.form['name']
            file_path = './static/training/{}'.format(train_name)
            # フォルダがないときだけフォルダを作成
            if not os.path.exists(file_path):
                os.mkdir(file_path)
            # ファイルがあり拡張子が対応しているとき画像を入力した名前のフォルダに保存
            if file and allwed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(file_path, filename)) # パスを指定し画像を保存
                flash(filename, "success")
            else:
                flash('拡張子をjpgかpngにしてください', 'error')
        try:
            # 学習
            train.face_traning([train_name])
            flash('学習に成功しました', 'success')
        except:
            flash('画像を選択しなおしてください', 'error')
        return redirect('/training')
    return render_template('training.html')


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
    # 選択した出退勤情報を取得
    attendance_data = taikin
    return render_template('sebcam.html', taikin=attendance_data)


@app.route('/image_ajax/<attendance_data>', methods=['POST'])
def set_data(attendance_data=None):
    # 画像を処理する
    enc_data  = request.form['img']
    #dec_data = base64.b64decode( enc_data )              # これではエラー  下記対応↓
    dec_data = base64.b64decode( enc_data.split(',')[1] ) # 環境依存の様(","で区切って本体をdecode)
    
    # 判定用の画像を保存
    dec_img = BytesIO(dec_data)
    img  = Image.open(dec_img)
    img_path = 'static/images/image.jpg'
    img.save(img_path)
    img_path = './static/images/image.jpg'

    # 顔の判定
    #result_name, rate = identify.start_identify_faces(img_path)
    if result_name == None:
        result_name = '検出できませんでした'
        rate = '0' 
    return render_template('setdata.html', result_name=result_name, rate=rate, taikin=attendance_data)


@app.route('/add_db/<result_name>/<rate>/<attendance_data>')
def add_db(result_name=None, rate=0, attendance_data=None):
    # データベースへ保存する
    db.add_attendance_db(result_name, rate, attendance_data)
    return redirect('/result/{}/{}/{}'.format(result_name, rate, attendance_data))


@app.route('/result/<result_name>/<rate>/<attendance_data>')
def sub(result_name=None, rate=0, attendance_data=None):
    # データベースの情報を表示
    db_info = db.get_infomation_attendance()
    return render_template(
        'identify.html', taikin=attendance_data, result_name=result_name, rate=rate, db_info=db_info)


@app.route('/menkyo_ocr')
def main_ocr():
    return render_template('menkyo_ocr.html')


@app.route('/image_ocr_ajax', methods=['POST'])
def set_ocr_data():
    result_txt = ''
    # 画像を処理する
    enc_data  = request.form['img']
    #dec_data = base64.b64decode( enc_data )              # これではエラー  下記対応↓
    dec_data = base64.b64decode( enc_data.split(',')[1] ) # 環境依存の様(","で区切って本体をdecode)
    
    # 判定用の画像を保存
    dec_img = BytesIO(dec_data)
    img  = Image.open(dec_img)
    img_path = 'static/images/image_ocr.jpg'
    cv2_img = pil2cv(img)                                 # PIL -> OpenCV
    # 顔の位置を検出
    clone, roi, point_position, rectangle_position = dlcv.face_shape_detector_dlib(cv2_img)
    if roi is None:
        return 'もう一度撮影してください' 
    x1, y1 = point_position[0]                            # 右目の位置
    x2, y2 = point_position[1]                            # 左目の位置
    #img.save(img_path)

    # 画像の判定                                           # 両目の位置の指定
    posi_flag = (x1 > 320 and x2 > 320 and y1 < 285 and y2 < 285)
    interval_flag = (25 <= x2 - x1 <= 50)                 # 両目の幅の指定
    if posi_flag and interval_flag:
        atan = dlcv.rotate_culc(point_position)           # 角度計算
        img_r = dlcv.img_rotate(img, atan)                # 画像回転
        # 回転させた画像から再度顔を検出
        clone, _, _, rectangle_position = dlcv.face_shape_detector_dlib(pil2cv(img_r))
        if rectangle_position is not None:
            cv2.imwrite(img_path, clone)
            for i in range(4):
                cut_img = pyocr.cut_number_2(img_r, rectangle_position, i) # 番号の位置の切り抜き
                cut_img.save('static/images/cut_img' + str(i) + '.jpg')
                txt = pyocr.ocr_digit(cut_img)                # 番号読み取り
                if txt.isdecimal() and len(txt) == 12:
                    result_txt = txt
                    break
    if not result_txt:
        result_txt = 'もう一度撮影してください'
    return result_txt


def pil2cv(image):
    ''' PIL型 -> OpenCV型 '''
    new_image = np.array(image, dtype=np.uint8)
    if new_image.ndim == 2:                                # モノクロ
        pass
    elif new_image.shape[2] == 3:                          # カラー
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGB2BGR)
    elif new_image.shape[2] == 4:                          # 透過
        new_image = cv2.cvtColor(new_image, cv2.COLOR_RGBA2BGRA)
    return new_image


def cv2pil(image):
    ''' OpenCV型 -> PIL型 '''
    new_image = image.copy()
    if new_image.ndim == 2:                               # モノクロ
        pass
    elif new_image.shape[2] == 3:                         # カラー
        new_image = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)
    elif new_image.shape[2] == 4:                         # 透過
        new_image = cv2.cvtColor(new_image, cv2.COLOR_BGRA2RGBA)
    new_image = Image.fromarray(new_image)
    return new_image
    

if __name__ == '__main__':
    app.run(debug=True)