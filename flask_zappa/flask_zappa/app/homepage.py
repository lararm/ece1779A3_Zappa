from flask import render_template, session, request, escape, redirect, url_for,flash
from app import webapp
from app import config
from app import dynamo
from app import collage
import datetime
import os
import os.path
import boto3
import time
import random
import re
from wand.image import Image
from PIL import Image, ImageDraw, ImageFont
import json
import requests


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
ALLOWED_IMAGE_EXTENSIONS = set(['image/png', 'image/jpg', 'image/jpeg', 'image/gif'])


@webapp.route('/login', methods=['GET','POST'])
def login():
    print("login")
    return render_template("login.html")


@webapp.route('/login_submit', methods=['POST'])
def login_submit():
    #Get User Input
    username = request.form['username']
    password = request.form['password']
    # Login
    if (username == config.LOGIN_USER):
        return redirect(url_for('homepage'))
    else:
        return redirect(url_for('login'))

@webapp.route('/homepage',methods=['GET','POST'])
def homepage():
    image_list = dynamo.query_image()
    return render_template("homepage.html",image_names=image_list)


@webapp.route('/upload_image_submit', methods=['POST'])
def upload_image_submit():

    # Get Session Information
    #username = 'irfan' #escape(session['username'])

    # Get User Input
    image = request.files['image']
    image_name = image.filename
    image_type = image.content_type

    # If user does not select file, browser also
    # submit a empty part without filename
    if image_name == '':
        flash("No image selected for upload.")
        return redirect(url_for('homepage'))

    # Check image file extension
    if not valid_image_extension(image_type):
        flash("%s is not a valid image type. Must be of type [png,gif,jpeg,jpg]." % (image_type))
        return redirect(url_for('homepage'))

    # Create an S3 client
    s3 = boto3.client('s3')
    # s3 = boto3.client('s3')
    id = config.AWS_ID

    # # Creating unique name
    timestamp = str(int(time.time()))
    randomnum = str(random.randint(0, 10000))
    unique_name = timestamp + "_" + randomnum + "_" + image_name
    
    # Upload image to S3
    image_new_name = unique_name
    s3.upload_fileobj(image,
                      id,
                      image_new_name,
                      ExtraArgs={"Metadata": {"Content-Type": image_type}})
    image_url = (s3.generate_presigned_url('get_object', Params={'Bucket': id, 'Key': image_new_name},
                                           ExpiresIn=100)).split('?')[0]

    print("image url: " + image_url )

    return redirect(url_for('homepage'))


@webapp.route('/upload_profile_submit', methods=['POST'])
def upload_profile_submit():
    print("#profile_submit")
    # collage_test()

    #Get User Input
    profile_name = request.form['profile_name']
    image = request.files['profile_image']
    image_name = image.filename
    image_type = image.content_type
    print(profile_name)
    print(image)
    

    #TODO: Check if there is a face in image
    # If user does not select file, browser also
    # submit a empty part without filename
    if image_name == '':
        flash("No image selected for upload.")
        return redirect(url_for('homepage'))

    # Check image file extension
    if not valid_image_extension(image_type):
        flash("%s is not a valid image type. Must be of type [png,gif,jpeg,jpg]." % (image_type))
        return redirect(url_for('homepage'))

    # Create an S3 client
    s3 = boto3.client('s3')
    # s3 = boto3.client('s3')
    id = 'lambdas3source.people'

    # # Creating unique name
    timestamp = str(int(time.time()))
    randomnum = str(random.randint(0, 10000))
    unique_name = timestamp + "_" + randomnum + "_" + image_name

    # Upload image to S3
    image_new_name = unique_name
    s3.upload_fileobj(image,
                      id,
                      image_new_name,
                      ExtraArgs={"Metadata": {"Content-Type": image_type}})
    image_url = (s3.generate_presigned_url('get_object', Params={'Bucket': id, 'Key': image_new_name},
                                           ExpiresIn=100)).split('?')[0]

    print("image url: " + image_url)
    url ='https://s3.amazonaws.com/lambdas3source.people/'+image_new_name
    dynamo.update_profiles_table(profile_name,url)

    return redirect(url_for('homepage'))



@webapp.route('/image_info', methods=['GET', 'POST'])
def image_info():
    print("#image_info")
    # Get User Input
    if request.method == 'GET':
        return render_template("image.html")

    image_name = request.form['image_name']
    print(image_name)
    #image_names = db.get_transforms(username, image_name)


    return render_template("image.html", image_name=image_name)

@webapp.route('/query_submit', methods=['POST'])
def query_submit():
    print("#query_submit")
    tags = request.form['query']

    if (len(tags) == 0):
        return redirect(url_for('homepage'))
    image_list = dynamo.query_tag_table(tags)
    print(tags)
    return render_template("homepage.html",image_names=image_list,query=[tags])

@webapp.route('/parse_image', methods=['GET','POST'])
def parse_image():

    with open("face.json") as json_file:
        response = json.load(json_file)

    for face in response['FaceMatches']:
        faceMatch = float(face['Similarity'])
        if ((faceMatch>=70.00) and (faceMatch<=100.0)):
            print ("I think hes in the image")

    return redirect(url_for('homepage'))

def valid_image_extension(ext):
    for extension in ALLOWED_IMAGE_EXTENSIONS:
        if (ext == extension):
            return True

    return False

def lambda_handler(event, context):
    print("#lambda_handler")
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        print("CONTENT TYPE: " + response['ContentType'])
        print("Key: " + key)
        return response['ContentType']
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

def draw_retangle():
    # "BoundingBox": {
    #     "Width": 0.13733333349227905,
    #     "Height": 0.20956256985664368,
    #     "Left": 0.31066668033599854,
    #     "Top": 0.15157680213451385
    print("#draw retangle")
    source_img = Image.open('flower1.jpg')
    draw = ImageDraw.Draw(source_img)
    draw.rectangle(((50, 50), (100, 100)),outline = "blue")
    source_img.save("retangle.jpg")


@webapp.route('/collages', methods=['GET'])
def make_collage():

    table = dynamodb.Table("Profiles")
    profiles = table.scan(
        ProjectionExpression="#name,picture",
        ExpressionAttributeNames={"#name": "name"}
    )
    for profile in profiles['Items']:
        name = profile['name']
        image_list = dynamo.query_tag_table(name)
        collage.make_collage(image_list, 'collage5.jpg', 800, 600, name)

    #Display collages
    image_list = []
    table = dynamodb.Table("Collages")
    collages = table.scan(
        ProjectionExpression="#name,collage",
        ExpressionAttributeNames={"#name": "name"}
    )
    response = collages['Items']
    for collagei in  collages['Items']:
        image_list.append(collagei['collage'])
        print(collagei['collage'])

    return render_template("homepage.html",image_names=image_list)


