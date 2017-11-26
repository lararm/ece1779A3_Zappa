from flask import render_template, session, request, escape, redirect, url_for,flash
from app import webapp
from app import config
import datetime
import os
import boto3
import time
import random

import json
import urllib.parse

ALLOWED_IMAGE_EXTENSIONS = set(['image/png', 'image/jpg', 'image/jpeg', 'image/gif'])

@webapp.route('/add')
def add_two_numbers():
    if request.args.get('n1').isdigit() == False or \
       request.args.get('n2').isdigit() == False:
        return "Error! All inputs most be of type int"
    
    n1 = int(request.args.get('n1'))
    n2 = int(request.args.get('n2'))
    return render_template("example4.html",n1=n1, n2=n2, result=n1+n2)

@webapp.route('/add_v2',methods=['GET'])
def add_two_numbers_v2_form():
    return render_template("example4_form.html")


@webapp.route('/add_v2_submit',methods=['POST'])
def add_two_numbers_v2():
    if request.form.get('n1').isdigit() == False or \
       request.form.get('n2').isdigit() == False:
        return "Error! All inputs most be of type int"

    n1 = int(request.form.get('n1'))
    n2 = int(request.form.get('n2'))
    return render_template("example4.html",n1=n1, n2=n2, result=n1+n2)

@webapp.route('/add_v3',methods=['GET'])
def add_two_numbers_v3_form():
    return render_template("example4_form_v2.html")


@webapp.route('/add_v3_submit',methods=['POST'])
def add_two_numbers_v3():

    n1 = request.form.get('n1')
    n2 = request.form.get('n2')

    if n1.isdigit() == False or \
       n2.isdigit() == False:
        error="Error! All inputs most be of type int"
        return render_template("example4_form_v2.html", error=error,n1=n1, n2=n2)

    n1 = int(request.form.get('n1'))
    n2 = int(request.form.get('n2'))
    return render_template("example4.html",n1=n1, n2=n2, result=n1+n2)


# @webapp.route('/homepage',methods=['GET','POST'])
# def homepage():
#     return render_template("homepage.html")
#
#
# @webapp.route('/upload_image_submit', methods=['POST'])
# def upload_image_submit():
#     print("#image_submit")
#     # Get Session Information
#     username = 'test' #escape(session['username'])
#
#     # Get User Input
#     image = request.files['image']
#     image_name = image.filename
#     image_type = image.content_type
#
#     # If user does not select file, browser also
#     # submit a empty part without filename
#     if image_name == '':
#         flash("No image selected for upload.")
#         return redirect(url_for('homepage'))
#
#     # Check image file extension
#     if not valid_image_extension(image_type):
#         flash("%s is not a valid image type. Must be of type [png,gif,jpeg,jpg]." % (image_type))
#         return redirect(url_for('homepage'))
#
#     # Create an S3 client
#     s3 = boto3.client('s3')
#     # s3 = boto3.client('s3')
#     id = config.AWS_ID
#
#     # Creating unique name
#     timestamp = str(int(time.time()))
#     randomnum = str(random.randint(0, 10000))
#     unique_name = timestamp + "_" + randomnum + "_" + image_name
#
#     # Upload image to S3
#     image_new_name = username + "/" + unique_name
#     s3.upload_fileobj(image,
#                       id,
#                       image_new_name,
#                       ExtraArgs={"Metadata": {"Content-Type": image_type}})
#     image_url = (s3.generate_presigned_url('get_object', Params={'Bucket': id, 'Key': image_new_name},
#                                            ExpiresIn=100)).split('?')[0]
#
#     return redirect(url_for('homepage'))
#
#
# def valid_image_extension(ext):
#     for extension in ALLOWED_IMAGE_EXTENSIONS:
#         if (ext == extension):
#             return True
#
#     return False
#
# def lambda_handler(event, context):
#     print("#lambda_handler")
#     #print("Received event: " + json.dumps(event, indent=2))
#
#     # Get the object from the event and show its content type
#     bucket = event['Records'][0]['s3']['bucket']['name']
#     key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
#     try:
#         response = s3.get_object(Bucket=bucket, Key=key)
#         print("CONTENT TYPE: " + response['ContentType'])
#         print("Key: " + key)
#         return response['ContentType']
#     except Exception as e:
#         print(e)
#         print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
#         raise e