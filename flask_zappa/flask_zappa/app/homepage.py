"""
File:     homepage.py
Authors:  Irfan Khan 999207665, Larissa Ribeiro Madeira 1003209173
Date:     November 2017
Purpose:  Webpage Routes
"""
import time
import random
import boto3
from flask import render_template, session, request, escape, redirect, url_for, flash
from app import webapp
from app import dynamo
from app import config
#from wand.image import Image
#from PIL import Image, ImageDraw, ImageFont

@webapp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles /login route."""
    if 'username' in session:
        return redirect(url_for('homepage'))
    return render_template("login.html")

@webapp.route('/login_submit', methods=['POST'])
def login_submit():
    """Handles /login_submit route."""

    #Get User Input
    username = request.form['username']
    password = request.form['password']

    # Login
    if dynamo.login_user(username, password):
        session['username'] = username
        return redirect(url_for('homepage'))
    return redirect(url_for('login'))

@webapp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handles singup route."""
    if 'username' in session:
        print("Session user is: %s" % escape(session['username']))
        return redirect(url_for('homepage'))
    return render_template("signup.html")

@webapp.route('/signup_submit', methods=['POST'])
def signup_submit():
    """Handles signup_submit route."""

	#Get User Input
    username = request.form['username']
    password = request.form['password']

	#Add User
    if dynamo.add_user(username, password):
        session['username'] = request.form['username']
        return redirect(url_for('homepage'))
    return redirect(url_for('signup'))

@webapp.route('/logout_submit', methods=['POST'])
def logout_submit():
    """Handles /logout_submit route."""

    #Get Session Information
    username = escape(session['username'])
    print("Logging " + username + " out")

    #Close Session
    session.pop('username', None)
    return redirect(url_for('login'))

@webapp.route('/homepage', methods=['GET', 'POST'])
def homepage():
    """Handles /homepage route."""
    if 'username' not in session:
        return redirect(url_for('login'))

    username = escape(session['username'])
    image_list = dynamo.query_image(username)
    return render_template("homepage.html", image_names=image_list)

@webapp.route('/upload_image_submit', methods=['POST'])
def upload_image_submit():
    """Handles upload_image_submit route."""
    # Get User Input
    username = escape(session['username'])
    image = request.files['image']
    image_name = image.filename
    image_type = image.content_type

    # If no image name redirect to homepage
    if image_name == '':
        flash("No image selected for upload.")
        return redirect(url_for('homepage'))

    # Check image file extension
    if not valid_image_extension(image_type):
        flash("%s is not a valid image type. Must be of type [png,gif,jpeg,jpg]." % (image_type))
        return redirect(url_for('homepage'))

    # Create an S3 client
    storage = boto3.client('s3')
    storage_id = config.AWS_ID
    storage_path = "https://s3.amazonaws.com/lambdas3source/"

    # Creating unique name
    timestamp = str(int(time.time()))
    randomnum = str(random.randint(0, 10000))
    unique_name = timestamp + "_" + randomnum + "_" + image_name

    # Add image to the Database
    dynamo.add_new_image(username, storage_path + unique_name)

    # Upload image to S3
    image_new_name = unique_name
    storage.upload_fileobj(image,
                           storage_id,
                           image_new_name,
                           ExtraArgs={"Metadata": {"Content-Type": image_type}})
    image_url = (storage.generate_presigned_url('get_object',
                                                Params={'Bucket': storage_id, 'Key':image_new_name},
                                                ExpiresIn=100)).split('?')[0]

    print("image url: " + image_url)

    return redirect(url_for('homepage'))

@webapp.route('/upload_profile_submit', methods=['POST'])
def upload_profile_submit():
    """Handles upload_profile_submit route."""

    #Get User Input
    username = escape(session['username'])
    profile_name = request.form['profile_name']
    image = request.files['profile_image']
    image_name = image.filename
    image_type = image.content_type

    # Check for file
    if image_name == '':
        flash("No image selected for upload.")
        return redirect(url_for('homepage'))

    # Check image file extension
    if not valid_image_extension(image_type):
        flash("%s is not a valid image type. Must be of type [png,gif,jpeg,jpg]." % (image_type))
        return redirect(url_for('homepage'))

    # Create an S3 client
    storage = boto3.client('s3')
    storage_id = 'lambdas3source.people'

    # # Creating unique name
    timestamp = str(int(time.time()))
    randomnum = str(random.randint(0, 10000))
    unique_name = timestamp + "_" + randomnum + "_" + image_name
    
    # Upload Image to Database
    url = 'https://s3.amazonaws.com/lambdas3source.people/' + unique_name
    dynamo.update_profiles_table(username, profile_name, url)

    # Upload image to S3
    image_new_name = unique_name
    storage.upload_fileobj(image,
                           storage_id,
                           image_new_name,
                           ExtraArgs={"Metadata": {"Content-Type": image_type}})
    image_url = (storage.generate_presigned_url('get_object',
                                                Params={'Bucket': storage_id,
                                                        'Key': image_new_name},
                                                ExpiresIn=100)).split('?')[0]

    print("image url: " + image_url)


    return redirect(url_for('homepage'))

@webapp.route('/image_info', methods=['GET', 'POST'])
def image_info():
    """Handles image_info route."""

    # Get User Input
    if request.method == 'GET':
        return render_template("image.html")

    username = escape(session['username'])
    image_name = request.form['image_name']
    tags = dynamo.get_image_tags(username, image_name)
    print(tags)

    return render_template("image.html", image_name=image_name, tags=tags)

@webapp.route('/query_submit', methods=['POST'])
def query_submit():
    """Handles query_submit route."""

    username = escape(session['username'])
    tags = request.form['query']

    if not tags:
        return redirect(url_for('homepage'))
    image_list = dynamo.query_tag_table(username, tags)
    print(tags)
    return render_template("homepage.html", image_names=image_list, query=[tags])

@webapp.route('/profiles', methods=['GET'])
def query_profiles():
    """Returns list of all profiles"""

    username = escape(session['username'])
    profile_dictionary = dynamo.query_profiles(username)

    return render_template("profiles.html", dict=profile_dictionary)

def valid_image_extension(ext):
    """Determines if image is of a valid extension"""
    allowed_image_extensions = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif']

    for extension in allowed_image_extensions:
        if ext == extension:
            return True

    return False

"""
@webapp.route('/collages', methods=['GET'])
def make_collage():
    #Handles collages route.
    if 'username' not in session:
        return redirect(url_for('login'))

    table = dynamodb_resource().Table("Profiles")
    profiles = table.scan(
        ProjectionExpression="#name,picture",
        ExpressionAttributeNames={"#name": "name"}
    )
    for profile in profiles['Items']:
       name = profile['name']
       image_list = dynamo.query_tag_table(name)
       collageMaker.make_collage(image_list, name)
       break

    #Display collages
    image_list = []
    table = dynamodb_resource().Table("Collages")
    collages = table.scan(
        ProjectionExpression="#name,collage",
        ExpressionAttributeNames={"#name": "name"}
    )
    response = collages['Items']
    for collagei in  collages['Items']:
        image_list.append(collagei['collage'])
        print(collagei['collage'])

    return render_template("homepage.html", image_names=image_list)
"""
