###########################################################
# File:     web.py
# Authors:  Irfan Khan               999207665
#           Larissa Ribeiro Madeira 1003209173
# Date:     November 2017
# Purpose:  Webpage routes
###########################################################
from flask import render_template, session, request, escape, redirect, url_for,flash
from werkzeug.utils import secure_filename
import datetime
import os
import boto3
import time
import random 
from random import randint
from boto3 import dynamodb
from boto3.dynamodb.conditions import Key, Attr
import json

ALLOWED_IMAGE_EXTENSIONS = set(['image/png', 'image/jpg', 'image/jpeg', 'image/gif'])
dynamodb        = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb',region_name='us-east-1')

def intersect (a,b):
    return list(set(a) & set(b))

def query_tag_table(tags):

    tag_list = tags.split(",")

    #print (tag_list)

    queries = []
    tagcount = 0;
    for tag in tag_list:
        #print (tag.strip())
        response = query_tag(tag.strip())
        if (tagcount == 0):
            queries = response 
            tagcount = 1
        else:
            queries = intersect(queries,response)
        #print (queries)
        #print (response)

    #print (queries)

    return redirect(url_for('main'))

def query_tag(tag):

    response = dynamodb_client.query(
        TableName="Tags",
        Select = "ALL_ATTRIBUTES",
        KeyConditionExpression = "tag = :tagName",
        ExpressionAttributeValues = {":tagName":{"S":tag}}
    )

    images = response["Items"][0]["tags"]['SS']

    return images

def query_image():

    table = dynamodb.Table('Images')
    response = table.scan(
        ProjectionExpression= "#images",
        ExpressionAttributeNames= {"#images": "image"}
    )

    #print (response)
    image_list = []
    for image in response['Items']:
        #print (image['image'])
        image_list.append(image['image'])

    return image_list
    #print (image_list)
