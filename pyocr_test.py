import os
from PIL import Image
import sys
import cv2
import pyocr
import pyocr.builders


img = 'image.jpg'

# 1.インストール済みのTesseractのパスを通す
path_tesseract = ""           # Tesseract-OCRのパス
if path_tesseract not in os.environ["PATH"].split(os.pathsep):
    os.environ["PATH"] += os.pathsep + path_tesseract

tools = pyocr.get_available_tools()
if len(tools) == 0:
    # ツールが読み取れたか確認
    print("No OCR tool found")
    sys.exit(1)

tool = tools[0]
print("Will use tool '%s'" % (tool.get_name()))


def threshold(input_img):
    # 画像の2値化
    img = cv2.imread(input_img, 0)
    img = cv2.medianBlur(img,5)

    th3 = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)

    threshold_img = 'threshold_'+img
    cv2.imwrite(threshold_img, th3)
    return threshold_img


def pic_processing(img):
    # 原稿画像の読み込み
    img_org = Image.open(img)
    #img_org = img_org.resize((int(img_org.width*2),int(img_org.height*2)))
    #img_org.save('menkyo_resize.png')
    img_rgb = img_org.convert("L")
    pixels = img_rgb.load()

    # 原稿画像加工（黒っぽい色以外は白=255,255,255にする）
    c_max = 100
    for j in range(img_rgb.size[1]):
        for i in range(img_rgb.size[0]):
            if pixels[i, j] > c_max:
            #if (pixels[i, j][0] > c_max or pixels[i, j][1] > c_max or
                    #pixels[i, j][0] > c_max):
                pixels[i, j] = (255)
            elif pixels[i, j] < 50:
                pixels[i, j] = 0
    img_rgb.save('chenge_' + img)
    return img_rgb


def cut_number(img, i=0):
    #img = cv2.imread(img)
    #img_name = 'static/images/cut_number.jpg'
    #cut_img = img[220:250, 180:340]
    cut_img = img.crop((180+i, 220+i, 340+i, 250+i))
    #cv2.imwrite(img_name, cut_img)
    return cut_img


def ocr_digit(img):
    txt = tool.image_to_string(
        img,
        lang="jpn",
        builder=pyocr.builders.WordBoxBuilder(tesseract_layout=6)
    )
    #print(txt)
    result = ''
    for i in txt:
        print(i.content, ':', i.confidence)
        if i.confidence > 85:
            result = result + i.content
    return result


if __name__ == '__main__':
    img = threshold(img)
    img_rgb = pic_processing(img)
    txt = ocr_digit(img_rgb)
