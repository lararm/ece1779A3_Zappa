from __future__ import print_function

import boto3
from boto3 import dynamodb
from boto3.dynamodb.conditions import Key, Attr

from decimal import Decimal
import json
import urllib

# --------------- Amazon Resources -------------------------------------------
rekognition     = boto3.client('rekognition',region_name='us-east-1')
dynamodb        = boto3.client('dynamodb',region_name='us-east-1')

# --------------- Configuration Settigns -------------------------------------
faceMatchThreshold = 70.00 #FIXME we can adjust this confidence factor

# --------------- Helper Functions to call Rekognition APIs ------------------

def detect_new_user(src_bucket,src_key,tgt_bucket,tgt_key):

    print ("DETECT NEW USERS") #FIXME remove these prints
    print (src_bucket + " " + src_key)
    print (tgt_bucket + " " + tgt_key)
    
    #return False #FIXME
    
    response = rekognition.compare_faces(
        SourceImage={"S3Object": {"Bucket": src_bucket, "Name": src_key}},
        TargetImage={"S3Object": {"Bucket": tgt_bucket, "Name": tgt_key}}
    )
    
    for faceMatch in response['FaceMatches']:
        confidence = float(faceMatch['Face']['Confidence'])
        if (confidence >= faceMatchThreshold):
            return True
              
    return False

def query_name(image): 
    name = dynamodb.scan(
        TableName="Profiles",
        FilterExpression= "picture = :image",
        ExpressionAttributeValues = {":image":{"S":image}}
    )
    return (name['Items'][0]['name']['S'])
    
def query_images():
    images = dynamodb.scan(
        TableName='Images',
        FilterExpression= "faces = :face",
        ExpressionAttributeValues= {":face": {"BOOL":True}}
    )
    return images['Items']
    
def update_tags_table(tag,image):
    response = dynamodb.update_item(
        TableName= "Tags",
        Key={"tag": {"S":tag}},
        UpdateExpression = "ADD images :image",
        ExpressionAttributeValues = {":image": {"SS":[image]}},
        ReturnValues = "ALL_NEW"
    )

def update_images_table(name,image):
    
    response = dynamodb.update_item(
        TableName= "Images",
        Key={"image": {"S":image}},
        UpdateExpression = "ADD tags :taglist",
        ExpressionAttributeValues = {":taglist": {"SS":[name]}},
        ReturnValues = "ALL_NEW"
    )

# --------------- Helper Functions Version 2 to call Rekognition APIs ------------------

def query_name_2(image): 
    name = dynamodb.scan(
        TableName="Profiles_2",
        FilterExpression= "picture = :image",
        ExpressionAttributeValues = {":image":{"S":image}}
    )
    return (name['Items'][0]['name']['S'])
    
def query_images_2():
    images = dynamodb.scan(
        TableName='Images_2',
        FilterExpression= "faces = :face",
        ExpressionAttributeValues= {":face": {"BOOL":True}}
    )
    return images['Items']
    
def update_tags_table_2(tag,image):
    response = dynamodb.update_item(
        TableName= "Tags_2",
        Key={"tag": {"S":tag}},
        UpdateExpression = "ADD images :image",
        ExpressionAttributeValues = {":image": {"SS":[image]}},
        ReturnValues = "ALL_NEW"
    )

def update_images_table_2(name,image):
    
    response = dynamodb.update_item(
        TableName= "Images_2",
        Key={"image": {"S":image}},
        UpdateExpression = "ADD tags :taglist",
        ExpressionAttributeValues = {":taglist": {"SS":[name]}},
        ReturnValues = "ALL_NEW"
    )
    
# --------------- Main handler ------------------

def lambda_handler(event, context):
    """S3 trigger that uses Rekognition APIs to detect a new user in a database of files"""
    
    # Get the object from the event
    src_bucket      = event['Records'][0]['s3']['bucket']['name']
    src_key         = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    tgt_bucket      = "lambdas3source"
    
    src_bucket_path = "https://s3.amazonaws.com/lambdas3source.people/"
    tgt_bucket_path = "https://s3.amazonaws.com/lambdas3source/"
    
    try:
    
        # Get Username from Profiles
        #name = query_name(src_bucket_path + src_key)
        name = query_name_2(src_bucket_path + src_key)

        # Get Images that Contain a Face in them
        #images = query_images()
        images = query_images_2()
        
        for image in images:
            
            tgt_key = image['image']['S'].split(tgt_bucket_path,1)[1]
            
            #if (detect_new_user(src_bucket,src_key,src_bucket,src_key)):
            #    print ("I CAN FIND ME")
            
            if (detect_new_user(src_bucket,src_key,tgt_bucket,tgt_key)):
                print ("Match Found")
                #update_tags_table(name,tgt_bucket_path + tgt_key)
                #update_images_table(name,tgt_bucket_path + tgt_key)
                update_tags_table_2(name,tgt_bucket_path + tgt_key)
                update_images_table_2(name,tgt_bucket_path + tgt_key)

        return 
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(src_key,src_bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e 
