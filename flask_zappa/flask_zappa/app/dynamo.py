###########################################################
# File:     dynamo.py
# Authors:  Irfan Khan               999207665
#           Larissa Ribeiro Madeira 1003209173
# Date:     November 2017
# Purpose:  DynamoDB Queries
###########################################################
import boto3
from boto3 import dynamodb
from boto3.dynamodb.conditions import Key, Attr

dynamodb        = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb',region_name='us-east-1')

def intersect (a,b):
    return list(set(a) & set(b))

def query_tag_table(tags):

    tag_list = tags.split(",")

    queries = []
    tagcount = 0;
    for tag in tag_list:
        response = query_tag(tag.strip())
        if (tagcount == 0):
            queries = response 
            tagcount = 1
        else:
            queries = intersect(queries,response)

    return queries


def query_tag(tag):

    response = dynamodb_client.query(
        TableName="Tags",
        Select = "ALL_ATTRIBUTES",
        KeyConditionExpression = "tag = :tagName",
        ExpressionAttributeValues = {":tagName":{"S":tag}}
    )

    if not response["Items"]:
        return []
    else:
        return response["Items"][0]["images"]['SS']


def query_image():

    table = dynamodb.Table('Images')
    response = table.scan(
        ProjectionExpression= "#images",
        ExpressionAttributeNames= {"#images": "image"}
    )

    image_list = []
    for image in response['Items']:
        image_list.append(image['image'])

    return image_list

def update_profiles_table(name,picture): #FIXME PUT THIS IN WEBSITE
    response = dynamodb_client.update_item(
        TableName= "Profiles",
        Key={"name": {"S":name}},
        UpdateExpression = 'SET picture = :picture',
        ExpressionAttributeValues = {":picture" : {"S":picture}},
        ReturnValues = "ALL_NEW"

    )