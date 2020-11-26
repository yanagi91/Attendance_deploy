import asyncio
import io
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
# To install this module, run:
# python -m pip install Pillow
from PIL import Image, ImageDraw
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person
from google.cloud import secretmanager


project_id = ''
secret_name = ''
secret_ver = ''

client = secretmanager.SecretManagerServiceClient()

name = client.secret_version_path(
    project_id, secret_name, secret_ver)  # シークレットマネージャーのアドレスの取得
response = client.access_secret_version(name)

payload = response.payload.data.decode('UTF-8')

# Set the FACE_SUBSCRIPTION_KEY environment variable with your key as the value.
# This key will serve all examples in this document.
KEY = payload

# Set the FACE_ENDPOINT environment variable with the endpoint from your Face service in Azure.
# This endpoint will be used in all examples in this quickstart.
ENDPOINT = os.environ['FACE_ENDPOINT']

# Create an authenticated FaceClient.
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))
# Detect a face in an image that contains a single face

# Used in the Person Group Operations and Delete Person Group examples.
# You can call list_person_groups to print a list of preexisting PersonGroups.
# SOURCE_PERSON_GROUP_ID should be all lowercase and alphanumeric. For example, 'mygroupname' (dashes are OK).
PERSON_GROUP_ID = str('mygroupname') # assign a random ID (or name it anything)

# Used for the Delete Person Group example.
TARGET_PERSON_GROUP_ID = str('mygroupname') # assign a random ID (or name it anything)


# 画像内の顔の検出
def face_detected(face_data, image_name):
    """return detected_faces, image_face_ID
    
    顔の検出"""
    # We use detection model 2 because we are not retrieving attributes.
    detected_faces = face_client.face.detect_with_stream(image=face_data, recognition_model="recognition_03", detectionModel='detection_02')
    if not detected_faces:
        # 顔が検出出来なかった場合の処理
        #raise Exception('No face detected from image {}'.format(image_name))
        return None, None

    # Display the detected face ID in the first single-face image.
    # Face IDs are used for comparison to faces (their IDs) detected in other images.
    print('Detected face ID from', image_name, ':')
    for face in detected_faces: print (face.face_id)
    print()

    # Save this ID for use in Find Similar
    #print(detected_faces)
    #face_IDs = detected_faces[0].face_id
    face_ids = []
    for face in detected_faces:
        face_ids.append(face.face_id)
    return detected_faces, face_ids


def identify_faces(image, face_ids, detected_faces):
    """return result_name, rates

    学習した顔のグループと入力された画像を比較し一致するものを返す"""
    # Identify faces
    results = face_client.face.identify(face_ids, PERSON_GROUP_ID)
    print('Identifying faces in {}'.format(os.path.basename(image.name)))

    result_name = None
    rate = 0
    
    if not results:
        print('No person identified in the person group for faces from {}.'.format(os.path.basename(image.name)))
    for person in results:
        if len(person.candidates) > 0:
            # 一致したデータのnameのIDを取得
            result_name_id = face_client.person_group_person.get(PERSON_GROUP_ID, person.candidates[0].person_id)
            result_name = result_name_id.name # nameのIDから名前を格納
            rate = person.candidates[0].confidence # 確率を格納
            print('Person for face ID {} is identified in {} with a confidence of {}.'.format(result_name_id.name, os.path.basename(image.name), person.candidates[0].confidence)) # Get topmost confidence score
        else:
            print('No person identified for face ID {} in {}.'.format(person.face_id, os.path.basename(image.name)))
    #print(result_name)
    return result_name, rate


def start_identify_faces(image):
    """return result_name, str(rates * 100)

    確率と名前を返す（文字列型）。見つからない場合、Falseを返す"""

    # 入力画像の加工
    input_image = image
    input_image_name = os.path.basename(input_image)
    input_image_data = open(input_image, 'rb')
    #print("recognition:")
    #print(face_client.person_group.get(PERSON_GROUP_ID))
    # 顔の検出
    detected_faces, image_face_ID = face_detected(input_image_data, input_image_name)
    if detected_faces == None:
        # 顔を検出出来なかった場合の処理
        print('noface')
        return None, 0

    # 顔の判定
    result_name, rate = identify_faces(input_image_data, image_face_ID, detected_faces)
    return result_name, str(rate * 100)


if __name__ == '__main__':
    image = ('')
    result_name, rate = start_identify_faces(image)
    print(result_name + ':信頼度は' + str(rate) + '%です')
