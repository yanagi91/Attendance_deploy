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


# 学習
def face_traning(person_group_name):
    """学習する顔のグループの作成、学習を行う"""
    '''
    Create the PersonGroup
    '''
    # person_group の初期化
    #face_client.person_group.delete(person_group_id=PERSON_GROUP_ID)

    # Create empty Person Group. Person Group ID must be lower case, alphanumeric, and/or with '-', '_'.
    print('Person group:', PERSON_GROUP_ID)
    try:
        face_client.person_group.create(person_group_id=PERSON_GROUP_ID, name=PERSON_GROUP_ID, recognition_model="recognition_03")
    except:
        pass
    
    for person_name in person_group_name:
        # Define aragaki friend
        print(person_name)
        train_person_name = face_client.person_group_person.create(PERSON_GROUP_ID, person_name)

        '''
        Detect faces and register to correct person
        '''
        # Find all jpeg images of friends in working directory
        train_person_images = [file for file in glob.glob('static/training/{}/*.jpg'.format(person_name))]


        #print(aragaki_images)
        # Add to a aragaki person
        for image in train_person_images:
            a = open(image, 'r+b')
            face_client.person_group_person.add_face_from_stream(PERSON_GROUP_ID, train_person_name.person_id, a)

        time.sleep(12)


    '''
    Train PersonGroup
    '''
    print()
    print('Training the person group...')
    # Train the person group
    face_client.person_group.train(PERSON_GROUP_ID)

    while (True):
        training_status = face_client.person_group.get_training_status(PERSON_GROUP_ID)
        print("Training status: {}.".format(training_status.status))
        print()
        if (training_status.status is TrainingStatusType.succeeded):
            break
        elif (training_status.status is TrainingStatusType.failed):
            sys.exit('Training the person group has failed.')
        time.sleep(5)


if __name__ == '__main__':
    # フォルダ名から名前グループの作成
    path = 'image'
    person_group_name = ['yanagishima']         # os.listdir(path)
    face_traning(person_group_name)
