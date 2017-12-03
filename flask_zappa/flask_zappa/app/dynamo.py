"""
File:     dynamo.py
Authors:  Irfan Khan 999207665, Larissa Ribeiro Madeira 1003209173
Date:     November 2017
Purpose:  DynamoDB Queries
"""
import boto3

def dynamodb_resource():
    """Returns a dynamodb resource"""
    return boto3.resource('dynamodb', region_name='us-east-1')

def dynamodb_client():
    """Returns a dynamodb client"""
    return boto3.client('dynamodb', region_name='us-east-1')

def intersect(list_a, list_b):
    """Converts input lists into sets, finds their intersection, and returns the resulting list"""
    return list(set(list_a) & set(list_b))

def query_user(user, password):
    """Determines if username is available and adds it to the user table if possible"""
    print(user)
    print(password)
    return False #Need to add query to user table here FIXME

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
