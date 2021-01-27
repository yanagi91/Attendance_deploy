#! /usr/bin/python
# -*- coding: utf-8 -*-
import cv2
import dlib
import numpy as np
import math
import imutils
from imutils import face_utils
from PIL import Image

""" 
各部位の輪郭情報の数字
口 = 48:68
右眉 = 17:22
左眉 = 22:27
右目 = 36:42
左目 = 42:48
鼻 = 27:35
あご = 0:17 
"""

predictor_path = "./shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(predictor_path)
detector = dlib.get_frontal_face_detector()

mark_point = [36, 45]
filename = "./static/images/dlib"


def face_shape_detector_dlib(img):
    point_position = []
    rectangle_position = []
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # frontal_face_detectorクラスは矩形, スコア, サブ検出器の結果を返す
    dets, scores, idx = detector.run(img_rgb, 0)
    if len(dets) > 0:
        for i, rect in enumerate(dets):
            shape = predictor(img_rgb, rect)
            shape = face_utils.shape_to_np(shape)
            clone = img.copy()
            # landmarkを画像に書き込む
            for i in mark_point:
                x, y = shape[i]
                print(str(x) + ':' + str(y))
                #cv2.circle(clone, (x, y), 1, (0, 0, 255), -1)
                point_position.append((x, y))
            (x, y, w, h) = cv2.boundingRect(np.array([shape[36:45]])) #口の部位のみ切り出し
            roi = img[y:y + h, x:x + w]
            x1, y1 = point_position[0]
            x2, y2 = point_position[1]
            a = int(4.43 * (x2 - x1))   # 2点間の比率から番号取得する枠の長さを計算
            b = 136 * a // 155        # 番号取得する枠の位置を計算
            y1 += int(33 * a / 155)
            x2 -= b
            y2 = y1 + int(30 * a /155)
            x1 = x2 - a
            if len(point_position) >= 2:
                rectangle_position = [(x1, y1), (x2, y2)]
                cv2.rectangle(clone, (x1, y1), (x2, y2), (0,0,255))
            #roi = cv2.resize(roi, (100, 100))
        return clone, roi, point_position, rectangle_position
    else:
        return img, None, None, None


def canny_edge(img):
    image = cv2.imread(img)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    canny = cv2.Canny(blurred, 120, 255, 1)

    # Find contours
    cnts = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    # Iterate thorugh contours and draw rectangles around contours
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)
    cv2.imwrite(filename + '_canny.jpg', canny)
    cv2.imwrite(filename + '_image.jpg', image)


def rectangle_image(img):
    # ファイルを読み込み グレースケール化
    img = cv2.imread(img, cv2.IMREAD_GRAYSCALE)

    # しきい値指定によるフィルタリング
    _, threshold = cv2.threshold(img, 240, 255, cv2.THRESH_BINARY)

    # 輪郭を抽出
    contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    font = cv2.FONT_HERSHEY_DUPLEX
    # 図形の数の変数
    triangle = 0
    rectangle = 0
    pentagon = 0
    oval = 0
    circle = 0

    # 図形の設定
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.01*cv2.arcLength(cnt, True), True)
        cv2.drawContours(img, [approx], 0, (0), 2)
        x = approx.ravel()[0]
        y = approx.ravel()[1]

        if len(approx) == 3:
            triangle +=1
            cv2.putText(img, "triangle{}".format(triangle),  (x, y), font, 0.8, (0))
            
        elif len(approx) == 4:
            rectangle +=1
            cv2.putText(img, "rectangle{}".format(rectangle),  (x, y), font, 0.8, (0))
                    
        elif len(approx) == 5:
            pentagon +=1
            cv2.putText(img, "pentagon{}".format(pentagon),  (x, y), font, 0.8, (0))
            
        elif 6 < len(approx) < 14:
            oval +=1
            cv2.putText(img, "oval{}".format(oval),  (x, y), font, 0.8, (0))
            
        else:
            circle +=1
            cv2.putText(img, "circle{}".format(circle), (x, y), font, 0.8, (0))
            
    # 結果の画像作成
    cv2.imwrite(filename + 'output_shapes.png',img)
    # 図形の数の結果
    print('Number of triangle = ' , triangle)
    print('Number of rectangle = ' , rectangle)
    print('Number of pentagon = ' , pentagon)
    print('Number of circle = ' , circle)
    print('Number of oval = ' , oval)


def main():

    cap = cv2.VideoCapture(0)
    count = 0

    while True:
        ret, frame = cap.read()
        frame = imutils.resize(frame, width=640, height=380)
        frame, roi, point_position, _ = face_shape_detector_dlib(frame)
        cv2.imshow('img', frame)
        c = cv2.waitKey(1)
        if c == 27:  # ESCを押してウィンドウを閉じる
            break
        if c == 32:  # spaceで保存
            count += 1
            filename_1 = filename + str(count) + ".jpg"
            cv2.imwrite(filename_1, frame)  # 001~連番で保存
            print('save done')
            if roi is not None:
                print(point_position)
                atan = rotate_culc(point_position)
                img_r = img_rotate(filename_1, atan)
                print("ok")
                canny_edge(filename+"_rotate.jpg")
                #rectangle_image(filename+"_rotate.jpg")
    cap.release()
    cv2.destroyAllWindows()


def rotate_culc(point_position):
    x1, y1 = point_position[0]
    x2, y2 = point_position[1]
    x3 = x1 - x2
    y3 = y1 - y2
    tan = y3 / x3
    print(tan)
    atan = np.arctan(tan) * 180 / math.pi
    return atan


def img_rotate(img, atan):
    #img = Image.open(img)
    img_r = img
    img_r = img.rotate(atan)
    img_r.save(filename+"_rotate.jpg")
    return img_r


if __name__ == '__main__':
    main()
