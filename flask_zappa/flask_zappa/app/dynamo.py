"""
File:     dynamo.py
Authors:  Irfan Khan 999207665, Larissa Ribeiro Madeira 1003209173
Date:     November 2017
Purpose:  DynamoDB Queries
"""
import hashlib
import uuid
import boto3
from boto3.dynamodb.conditions import Key
from flask import flash

def dynamodb_resource():
    """Returns a dynamodb resource"""
    return boto3.resource('dynamodb', region_name='us-east-1')

def dynamodb_client():
    """Returns a dynamodb client"""
    return boto3.client('dynamodb', region_name='us-east-1')

def intersect(list_a, list_b):
    """Converts input lists into sets, finds their intersection, and returns the resulting list"""
    return list(set(list_a) & set(list_b))

def add_user(username, password):
    """Determines if username is available and adds it to the user table if requirments met"""

    #Determine if username meets requirements
    if len(username) < 8:
        flash("Username must be atelast 8 characters long.")
        return False

    #Determine if password meets requirements
    if len(password) < 8:
        flash("Password must be atleast 8 characters long.")
        return False

    #Determine if username is available
    users = dynamodb_client().query(TableName="Users",
                                    Select="ALL_ATTRIBUTES",
                                    KeyConditionExpression="username = :username",
                                    ExpressionAttributeValues={":username":{"S":username}})

    if users['Items']:
        flash("Username %s is unavailable." % (username))
        return False

    # Encrypt New Password
    passsalt = uuid.uuid4().hex
    hash_object = hashlib.sha1(password.encode('utf-8') + passsalt.encode('utf-8'))
    passhash = hash_object.hexdigest()

    dynamodb_client().update_item(TableName="Users",
                                  Key={"username": {"S":username}},
                                  UpdateExpression="SET passhash=:passhash, passsalt=:passsalt",
                                  ExpressionAttributeValues={":passhash": {"S":passhash},
                                                             ":passsalt": {"S":passsalt}},
                                  ReturnValues="ALL_NEW")

    return True

def login_user(username, password):
    """Determines username and password credentials are correct, then logs user in."""

    #Determine if username exists
    users = dynamodb_client().query(TableName="Users",
                                    Select="ALL_ATTRIBUTES",
                                    KeyConditionExpression="username = :username",
                                    ExpressionAttributeValues={":username":{"S":username}})

    if not users['Items']:
        flash("User %s does not exist" % (username))
        return False

    #Recreate Hashed Password
    passhash = users['Items'][0]['passhash']['S']
    passsalt = users['Items'][0]['passsalt']['S']
    hash_object = hashlib.sha1(password.encode('utf-8') + passsalt.encode('utf-8'))
    newhash = hash_object.hexdigest()

    if passhash == newhash:
        return True

    flash("Password is incorrect!")
    return False

def add_new_image(username, image):
    """Adds a new image to the Image table"""
    response = dynamodb_client().put_item(TableName='Images',
                                          Item={'username':{"S":username},
                                                'image':{"S":image}})

    print(response)

def query_tag_table(username, tags):
    """Queries the database for images that contain all tags provided in the argument tags"""
    tag_list = tags.split(",")

    queries = []
    tagcount = 0
    for tag in tag_list:
        response = query_tag(username, tag.strip())
        if tagcount == 0:
            queries = response
            tagcount = 1
        else:
            queries = intersect(queries, response)

    return queries


def query_tag(username, tag):
    """Queries the Tags table for all images that are tagged with the argument tag for user"""
    response = dynamodb_client().query(TableName="Tags",
                                       ProjectionExpression="image",
                                       IndexName="tag-username-index",
                                       KeyConditionExpression="tag = :tag AND username = :username",
                                       ExpressionAttributeValues={":tag":{"S":tag}, ":username":{"S":username}})


    images = []
    for item in response['Items']:
        images.append(item['image']['S'])

    while 'LastEvaluatedKey' in response:
        response = dynamodb_client().query(TableName="Tags",
                                           ProjectionExpression="image",
                                           IndexName="tag-username-index",
                                           KeyConditionExpression="tag = :tag AND username = :username",
                                           ExpressionAttributeValues={":tag":{"S":tag}, "username":{"S":username}})

        for item in response['Items']:
            images.append(item['image']['S'])

    return images

def query_image(username):
    """Queries the Images table for all images for a user"""

    table = dynamodb_resource().Table('Images')
    response = table.query(ProjectionExpression="#user, image",
                           ExpressionAttributeNames={"#user": "username"},
                           KeyConditionExpression=Key('username').eq(username))

    image_list = []
    for image in response['Items']:
        image_list.append(image['image'])

    while 'LastEvaluatedKey' in response:
        response = table.query(ProjectionExpression="#user, image",
                               ExpressionAttributeNames={"#user": "username"},
                               KeyConditionExpression=Key('username').eq(username),
                               ExclusiveStartKey=response['LastEvaluatedKey'])

        for image in response['Items']:
            image_list.append(image['image'])

    return image_list

def update_profiles_table(username, profilename, image):
    """Adds a new entry the Profiles table for all profileS"""
    dynamodb_client().put_item(TableName="Profiles",
                               Item={'profilename':{"S":profilename},
                                     'image':{"S":image},
                                     'username':{"S":username}})

def get_image_tags(username, image):
    """Queries the Tags table for all tags associated with this image"""
    response = dynamodb_client().query(TableName="Tags",
                                       ProjectionExpression="tag",
                                       IndexName="image-username-index",
                                       KeyConditionExpression="image = :image AND username = :username",
                                       ExpressionAttributeValues={":image":{"S":image}, ":username":{"S":username}})


    tags = []
    for item in response['Items']:
        tags.append(item['tag']['S'])

    while 'LastEvaluatedKey' in response:
        response = dynamodb_client().query(TableName="Tags",
                                           ProjectionExpression="tag",
                                           IndexName="image-username-index",
                                           KeyConditionExpression="image = :image AND username = :username",
                                           ExpressionAttributeValues={":image":{"S":image}, "username":{"S":username}})

        for item in response['Items']:
            tags.append(item['tag']['S'])

    return tags

def query_profiles(username):
    """Returns list of all profiles."""

    table = dynamodb_resource().Table("Profiles")
    response = table.query(ProjectionExpression="profilename,image",
                          KeyConditionExpression=Key('username').eq(username))

    profiles = {}
    for item in response['Items']:
        profilename = item['profilename']
        image = item['image']
        profiles[profilename] = image

    while 'LastEvaluatedKey' in response:
        response = table.query(ProjectionExpression="profilename,image",
                               KeyConditionExpression=Key('username').eq(username),
                               ExclusiveStartKey=response['LastEvaluatedKey'])

        for item in response['Items']:
            profilename = item['profilename']
            image = item['image']
            profiles[profilename] = image

    return profiles

'''
def face_detected(bucket, key): 
    """Determines if an image has a face in it"""
    rekognition_client = boto3.client('rekognition')
    response = rekognition_client.detect_faces(Image={"S3Object": {"Bucket": bucket,
                                                                   "Name": key}})
    if response['FaceDetails']:
        return True
    return False
'''
"""
def update_collages_table(name, collage):
    #Adds the new collage to the Collages table
    response = dynamodb_client().update_item(TableName='Collages',
                                             Key={'name':{"S":name}},
                                             UpdateExpression='SET collage= :collage',
                                             ExpressionAttributeValues={":collage":{"S":collage}},
                                             ReturnValues="ALL_NEW")
    print(response)
"""
