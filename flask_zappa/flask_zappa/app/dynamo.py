"""
File:     dynamo.py
Authors:  Irfan Khan 999207665, Larissa Ribeiro Madeira 1003209173
Date:     November 2017
Purpose:  DynamoDB Queries
"""
import hashlib
import uuid
import boto3
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

def query_tag_table(tags):
    """Queries the database for images that contain all tags provided in the argument tags"""
    tag_list = tags.split(",")

    queries = []
    tagcount = 0
    for tag in tag_list:
        response = query_tag(tag.strip())
        if tagcount == 0:
            queries = response
            tagcount = 1
        else:
            queries = intersect(queries, response)

    return queries


def query_tag(tag): #Need to make this a query in the image table FIXME
    """Queries the Images table for all images that are tagged with the argument tag"""
    response = dynamodb_client().query(TableName="Tags",
                                       Select="ALL_ATTRIBUTES",
                                       KeyConditionExpression="tag = :tagName",
                                       ExpressionAttributeValues={":tagName":{"S":tag}})

    if not response["Items"]:
        return []
    return response["Items"][0]["images"]['SS']

def query_image():
    """Quereies the Images table for all images"""
    table = dynamodb_resource().Table('Images')
    response = table.scan(ProjectionExpression="#images",
                          ExpressionAttributeNames={"#images": "image"})

    image_list = []
    for image in response['Items']:
        image_list.append(image['image'])

    return image_list

def update_profiles_table(name, picture):
    """Queries the Profiles table for all profileS"""
    response = dynamodb_client().update_item(TableName="Profiles",
                                             Key={"name": {"S":name}},
                                             UpdateExpression='SET picture = :picture',
                                             ExpressionAttributeValues={":picture":{"S":picture}},
                                             ReturnValues="ALL_NEW")
    print(response)

def update_collages_table(name, collage):
    """Adds the new collage to the Collages table"""
    response = dynamodb_client().update_item(TableName='Collages',
                                             Key={'name':{"S":name}},
                                             UpdateExpression='SET collage= :collage',
                                             ExpressionAttributeValues={":collage":{"S":collage}},
                                             ReturnValues="ALL_NEW")
    print(response)

def query_tags(image):
    """Queries the Images table for all tags associated with this image"""
    response = dynamodb_client().get_item(TableName="Images", Key={"image":{"S":image}})
    return response['Item']['tags']['SS']
