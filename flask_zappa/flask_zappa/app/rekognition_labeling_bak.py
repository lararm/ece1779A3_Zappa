from __future__ import print_function

import boto3
from boto3 import dynamodb
from boto3.dynamodb.conditions import Key, Attr

from decimal import Decimal
import json
import urllib

# --------------- Amazon Resources -------------------------------------------
rekognition     = boto3.client('rekognition')
dynamodb        = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb',region_name='us-east-1')

# --------------- Configuration Settings -------------------------------------
faceMatchThreshold = 70.00 # We can adjust this confidence factor
tagMatchThreshold  = 70.00 # We can adjust this confidence factor

# --------------- Helper Functions to call Rekognition APIs ------------------

def update_images_table(image,tags):
    
    tagList = []
    for tag in tags['Labels']:
        tagName = tag['Name'].lower()
        tagList.append(tagName)
    
    response = dynamodb_client.update_item(
        TableName= "Images",
        Key={"image": {"S":image}},
        UpdateExpression = "ADD tags :taglist",
        ExpressionAttributeValues = {":taglist": {"SS":tagList}},
        ReturnValues = "ALL_NEW"
    )
    
def add_names_to_images(image,names):
    
    response = dynamodb_client.update_item(
        TableName= "Images",
        Key={"image": {"S":image}},
        UpdateExpression = "ADD tags :taglist",
        ExpressionAttributeValues = {":taglist": {"SS":names}},
        ReturnValues = "ALL_NEW"
    )

def update_images_faces(image,faces):
    response = dynamodb_client.update_item(
        TableName= 'Images',
        Key={'image': {"S":image}},
        UpdateExpression = 'SET faces = :face',
        ExpressionAttributeValues = {":face" : {"BOOL":faces}},
        ReturnValues = "ALL_NEW"
    )
    
def update_tags_table(tag,image):
    response = dynamodb_client.update_item(
        TableName= "Tags",
        Key={"tag": {"S":tag}},
        UpdateExpression = "ADD images :image",
        ExpressionAttributeValues = {":image": {"SS":[image]}},
        ReturnValues = "ALL_NEW"
    )

def query_profiles():
    table = dynamodb.Table("Profiles")
    profiles = table.scan(
        ProjectionExpression= "#name,picture",
        ExpressionAttributeNames= {"#name": "name"}
    )
    return profiles['Items']
    
def parse_image_response(image,response):
    Tags = response['Labels']
    for tag in Tags:
        tagName = tag['Name'].lower()
        tagMatch = float(tag['Confidence'])
        if (tagMatch>=tagMatchThreshold ):  
            update_tags_table(tagName,image)

def detect_labels(bucket, key):
    response = rekognition.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response

def detect_faces(bucket, key):
    
    response = rekognition.detect_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    if (len(response['FaceDetails']) == 0):
        return False
    return True

def detect_existing_user(src_bucket,src_key,tgt_bucket,tgt_key):

    print ("DETECT EXISTING USERS") #FIXME remove these prints
    print (src_bucket + " " + src_key)
    print (tgt_bucket + " " + tgt_key)
    
    response = rekognition.compare_faces(
        SimilarityThreshold=faceMatchThreshold,
        SourceImage={'S3Object': {'Bucket': src_bucket, 'Name': src_key}},
        TargetImage={'S3Object': {'Bucket': tgt_bucket, 'Name': tgt_key}}
    )
    
    for faceMatch in response['FaceMatches']:
        confidence = float(faceMatch['Face']['Confidence'])
        if (confidence >= faceMatchThreshold):
            return True
              
    return False

# --------------- Helper Functions Version 2 to call Rekognition APIs ------------------

def update_images_table_2(image,tags):
    
    tagList = []
    for tag in tags['Labels']:
        tagName = tag['Name'].lower()
        tagList.append(tagName)
    
    response = dynamodb_client.update_item(
        TableName= "Images",
        Key={"image": {"S":image}},
        UpdateExpression = "ADD tags :taglist",
        ExpressionAttributeValues = {":taglist": {"SS":tagList}},
        ReturnValues = "ALL_NEW"
    )
    
def add_names_to_images_2(image,names):
    
    response = dynamodb_client.update_item(
        TableName= "Images",
        Key={"image": {"S":image}},
        UpdateExpression = "ADD tags :taglist",
        ExpressionAttributeValues = {":taglist": {"SS":names}},
        ReturnValues = "ALL_NEW"
    )

def update_images_faces_2(image,faces):
    response = dynamodb_client.update_item(
        TableName= 'Images',
        Key={'image': {"S":image}},
        UpdateExpression = 'SET faces = :face',
        ExpressionAttributeValues = {":face" : {"BOOL":faces}},
        ReturnValues = "ALL_NEW"
    )
    
def update_tags_table_2(tag,image):
    response = dynamodb_client.update_item(
        TableName= "Tags",
        Key={"tag": {"S":tag}},
        UpdateExpression = "ADD images :image",
        ExpressionAttributeValues = {":image": {"SS":[image]}},
        ReturnValues = "ALL_NEW"
    )

def query_profiles_2():
    table = dynamodb.Table("Profiles")
    profiles = table.scan(
        ProjectionExpression= "#name,picture",
        ExpressionAttributeNames= {"#name": "name"}
    )
    return profiles['Items']
    
def parse_image_response_2(image,response):
    Tags = response['Labels']
    for tag in Tags:
        tagName = tag['Name'].lower()
        tagMatch = float(tag['Confidence'])
        if (tagMatch>=tagMatchThreshold ):  
            update_tags_table(tagName,image)
            
# --------------- Main handler ------------------

def lambda_handler(event, context):
    
    #S3 trigger that uses Rekognition APIs to detect a new user in a database of files

    # Get the object from the event
    bucket  = event['Records'][0]['s3']['bucket']['name']
    key     = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    image   = "https://s3.amazonaws.com/lambdas3source/" + key
        
    try:

        # Calls rekognition DetectLabels API to detect labels in S3 object
        tags = detect_labels(bucket, key)
        
        # Upload Image Tags to database
        #parse_image_response(image,tags)
        #update_images_table(image,tags)
        parse_image_response_2(image,tags)
    
        # Check for Faces
        faces = detect_faces(bucket,key)
        
        print (faces)
        # Add Face Detected Attribute to Image Table
        #update_images_faces(image,faces)
        update_images_faces_2(image,faces)
        
        if (faces):
            
            print ("FACES DETECTED")
            
            # Buckets and Images for Face Comparison
            src_bucket      = "lambdas3source.people"
            src_bucket_path = "https://s3.amazonaws.com/lambdas3source.people/"
            tgt_bucket      = bucket
            tgt_key         = key
        
            profiles = query_profiles()
        
            names = []
            for profile in profiles:
                name =  profile['name']
                src_key = profile['picture'].split(src_bucket_path,1)[1]
                if(detect_existing_user(src_bucket,src_key,tgt_bucket,tgt_key)):
                    print ("Match found")
                    #update_tags_table(name,image)
                    update_tags_table_2(name,image)
                    names.append(name)
            
            #add_names_to_images(image,names)    
            add_names_to_images_2(image,names)
            
        return
        
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e

