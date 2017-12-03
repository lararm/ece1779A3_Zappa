from __future__ import print_function

import boto3
from boto3 import dynamodb
from boto3.dynamodb.conditions import Key, Attr

from decimal import Decimal
import json
import urllib

# --------------- Amazon Resources -------------------------------------------
REKOGNITION = boto3.client('rekognition', region_name='us-east-1')
DYNAMODB_RSC = boto3.resource('dynamodb', region_name='us-east-1')
DYNAMODB_CLI = boto3.client('dynamodb', region_name='us-east-1')

# --------------- Configuration Settigns -------------------------------------
FACE_MATCH_THRESHOLD = 70.00 # We can adjust this confidence factor

# --------------- Helper Functions to call Rekognition APIs ------------------

def get_username(image):
    """Gets the username from the Profiles table"""
    user = DYNAMODB_CLI.query(TableName="Profiles",
                              Select="ALL_ATTRIBUTES",
                              IndexName="image-index",
                              KeyConditionExpression="image = :image",
                              ExpressionAttributeValues={":image":{"S":image}})

    username = user['Items'][0]['username']['S']
    return username

def get_profilename(image):
    """Gets the profilename from the Profiles table"""
    profile = DYNAMODB_CLI.query(TableName="Profiles",
                                 Select="ALL_ATTRIBUTES",
                                 IndexName="image-index",
                                 KeyConditionExpression="image = :image",
                                 ExpressionAttributeValues={":image":{"S":image}})
    profilename = profile['Items'][0]['profilename']['S']
    return profilename

def detect_new_profile(src_bucket, src_key, tgt_bucket, tgt_key):
    """Uses Rekognition API to to detect if the face in src image exsits in the tgt image"""
    response = REKOGNITION .compare_faces(
        SourceImage={"S3Object": {"Bucket": src_bucket, "Name": src_key}},
        TargetImage={"S3Object": {"Bucket": tgt_bucket, "Name": tgt_key}}
    )

    for facematch in response['FaceMatches']:
        confidence = float(facematch['Face']['Confidence'])
        if confidence >= FACE_MATCH_THRESHOLD:
            return True

    return False

def query_images(username):
    """Retrieves all images for a user that have a face in them"""
    table = DYNAMODB_RSC.Table('Images')
    response = table.query(ProjectionExpression="image,faces",
                           FilterExpression="faces = :face",
                           ExpressionAttributeValues={':face':True},
                           KeyConditionExpression=Key('username').eq(username))

    image_list = []
    for image in response['Items']:
        image_list.append(image['image'])

    while 'LastEvaluatedKey' in response:
        response = table.scan(ProjectionExpression="image,faces",
                              FilterExpression="faces = :face",
                              ExpressionAttributeValues={':face':True},
                              KeyConditionExpression=Key('username').eq(username),
                              ExclusiveStartKey=response['LastEvaluatedKey'])

        for image in response['Items']:
            image_list.append(image['image'])
    return image_list

def update_tags_table(username, tag, image):
    """Adds labels to the tags table"""
    response = DYNAMODB_CLI.put_item(
        TableName="Tags",
        Item={'tag':{"S":tag},
              'image':{"S":image},
              'username':{"S":username}}
    )
    print(response)
# --------------- Main handler ------------------

def lambda_handler(event, context):
    """S3 trigger that uses Rekognition APIs to detect a new user in a database of files"""

    # Get the object from the event
    src_bucket = event['Records'][0]['s3']['bucket']['name']
    src_key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    tgt_bucket = "lambdas3source"

    src_bucket_path = "https://s3.amazonaws.com/lambdas3source.people/"
    tgt_bucket_path = "https://s3.amazonaws.com/lambdas3source/"

    try:

        # Get Username from Profiles
        username = get_username(src_bucket_path + src_key)
        profilename = get_profilename(src_bucket_path + src_key)

        # Get Images that Contain a Face in them
        images = query_images(username)

        for image in images:
            tgt_key = image.split(tgt_bucket_path, 1)[1]
            if detect_new_profile(src_bucket, src_key, tgt_bucket, tgt_key):
                print("Match Found")
                update_tags_table(username, profilename, tgt_bucket_path + tgt_key)

        return
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(src_key,src_bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e 
