from flask import render_template, session, request, escape, redirect, url_for,flash
from app import webapp
from app import config
from app import dynamo
import datetime
import os
import os.path
import boto3
import time
import random
import re
from wand.image import Image
from PIL import Image
from app import collage

ALLOWED_IMAGE_EXTENSIONS = set(['image/png', 'image/jpg', 'image/jpeg', 'image/gif'])

@webapp.route('/homepage',methods=['GET','POST'])
def homepage():

    image_list = dynamo.query_image()
    print (image_list)
    return render_template("homepage.html",image_names=image_list)
    return render_template("homepage.html")

@webapp.route('/upload_image_submit', methods=['POST'])
def upload_image_submit():
    print("#image_submit")
    #collage_test()

    listofimages = ['flower1.jpg', 'flower2.jpg', 'flower3.jpg', 'flower4.jpg', 'flower5.jpg']
    collage.make_collage(listofimages, 'collage5.jpg',500,450)
    # Get Session Information
    username = 'test' #escape(session['username'])

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

    # Creating unique name
    timestamp = str(int(time.time()))
    randomnum = str(random.randint(0, 10000))
    unique_name = timestamp + "_" + randomnum + "_" + image_name

    # Upload image to S3
    image_new_name = username + "/" + unique_name
    s3.upload_fileobj(image,
                      id,
                      image_new_name,
                      ExtraArgs={"Metadata": {"Content-Type": image_type}})
    image_url = (s3.generate_presigned_url('get_object', Params={'Bucket': id, 'Key': image_new_name},
                                           ExpiresIn=100)).split('?')[0]

    print("image url: " + image_url )

    return redirect(url_for('homepage'))

@webapp.route('/query_submit', methods=['POST'])
def query_submit():

    tags = request.form['query']
    print (tags)
    #image_list = query_tag_table(tags)

    #image_list = dynamo.query_image()
    #return render_template("homepage.html",image_names=image_list)
    return render_template("homepage.html")

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



