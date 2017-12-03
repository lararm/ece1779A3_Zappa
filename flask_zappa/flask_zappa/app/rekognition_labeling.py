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

# --------------- Configuration Settings -------------------------------------
FACE_MATCH_THRESHOLD = 80.00 # We can adjust this confidence factor
TAG_MATCH_THRESHOLD = 60.00 # We can adjust this confidence factor

# --------------- Helper Functions to call Rekognition APIs ------------------

def get_username(image):
    """Gets the username from the Image table"""
    user = DYNAMODB_CLI.query(TableName="Images",
                              Select="ALL_ATTRIBUTES",
                              IndexName="image-index",
                              KeyConditionExpression="image = :image",
                              ExpressionAttributeValues={":image":{"S":image}})

    username = user['Items'][0]['username']['S']
    return username

def update_images_faces(username, image, faces):
    """Updates images table boolean attribute faces"""
    response = DYNAMODB_CLI.update_item(TableName='Images',
                                        Key={'username': {"S":username},'image': {"S":image}},
                                        UpdateExpression='SET faces = :face',
                                        ExpressionAttributeValues={":face" : {"BOOL":faces}},
                                        ReturnValues="ALL_NEW")
    print(response['Attributes'])

def update_tags_table(username, tag, image):
    """Adds labels to the tags table"""
    DYNAMODB_CLI.put_item(TableName="Tags",
                          Item={'tag':{"S":tag},
                                'image':{"S":image},
                                'username':{"S":username}})


def query_profiles(username):
    """Queries for all profiles belonging to a user"""

    table = DYNAMODB_RSC.Table("Profiles")
    response = table.query(ProjectionExpression="profilename,image",
                          KeyConditionExpression=Key('username').eq(username))

    profiles = []
    for item in response['Items']:
        profiles.append(item)

    while 'LastEvaluatedKey' in response:
        response = table.query(ProjectionExpression="profilename,image",
                              KeyConditionExpression=Key('username').eq(username),
                              ExclusiveStartKey=response['LastEvaluatedKey'])

        for item in response['Items']:
            profiles.append(item)

    return profiles

def parse_image_response(username, image, response):
    """Parses reponse from Rekognize API, adding tags that meet the confidence threshold."""
    tags = response['Labels']
    for tag in tags:
        tagname = tag['Name'].lower()
        tagmatch = float(tag['Confidence'])
        if tagmatch >= TAG_MATCH_THRESHOLD:
            update_tags_table(username, tagname, image)

def detect_labels(bucket, key):
    """Uses Rekognition API to detect labels in an image"""
    response = REKOGNITION.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response

def detect_faces(bucket, key):
    """Uses Rekognition API to detects faces in an image"""
    response = REKOGNITION.detect_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    if not response['FaceDetails']:
        return False
    return True

def detect_existing_profile(src_bucket, src_key, tgt_bucket, tgt_key):
    """Uses Rekognition API to to detect if the face in src image exsits in the tgt image"""
    response = REKOGNITION.compare_faces(
        SimilarityThreshold=FACE_MATCH_THRESHOLD,
        SourceImage={'S3Object': {'Bucket': src_bucket, 'Name': src_key}},
        TargetImage={'S3Object': {'Bucket': tgt_bucket, 'Name': tgt_key}}
    )

    for facematch in response['FaceMatches']:
        confidence = float(facematch['Face']['Confidence'])
        if confidence >= FACE_MATCH_THRESHOLD:
            return True

    return False

# --------------- Main handler ------------------

def lambda_handler(event, context):
    """S3 trigger that uses Rekognition APIs to detect a new user in a database of file"""

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    image = "https://s3.amazonaws.com/lambdas3source/" + key

    try:

        # Get the Username for the Image that was uploaded
        print("GETTING USERNAME")
        username = get_username(image)

        # Calls rekognition DetectLabels API to detect labels in S3 object
        print("GETTING TAGS")
        tags = detect_labels(bucket, key)

        # Upload Image Tags to database
        print("PARSING IMAGE RESPONSE ")
        parse_image_response(username, image, tags)

        # Check for Faces
        print ("DETECTING FACES")
        faces = detect_faces(bucket, key)

        # Add Face Detected Attribute to Image Table
        print ("UPDATING IMAGES FACES")
        update_images_faces(username, image, faces)

        if faces:

            print("FACES DETECTED")

            # Buckets and Images for Face Comparison
            src_bucket = "lambdas3source.people"
            src_bucket_path = "https://s3.amazonaws.com/lambdas3source.people/"
            tgt_bucket = bucket
            tgt_key = key

            profiles = query_profiles(username)

            names = []
            for profile in profiles:
                profilename = profile['profilename']
                src_key = profile['image'].split(src_bucket_path, 1)[1]
                if detect_existing_profile(src_bucket, src_key, tgt_bucket, tgt_key):
                    print("Match found")
                    update_tags_table(username, profilename, image)
                    names.append(profilename)

        return

    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e
