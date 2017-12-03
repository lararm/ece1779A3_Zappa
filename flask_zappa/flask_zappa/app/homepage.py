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
from app import collageMaker
#from wand.image import Image
#from PIL import Image, ImageDraw, ImageFont

def dynamodb_resource():
    """Returns a dynamodb resource."""
    return boto3.resource('dynamodb', region_name='us-east-1')

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

    image_list = dynamo.query_image()
    return render_template("homepage.html", image_names=image_list)


@webapp.route('/upload_image_submit', methods=['POST'])
def upload_image_submit():
    """Handles upload_image_submit route."""
    # Get User Input
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

    # # Creating unique name
    timestamp = str(int(time.time()))
    randomnum = str(random.randint(0, 10000))
    unique_name = timestamp + "_" + randomnum + "_" + image_name

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
    print("#profile_submit")
    # collage_test()

    #Get User Input
    profile_name = request.form['profile_name']
    image = request.files['profile_image']
    image_name = image.filename
    image_type = image.content_type
    print(profile_name)
    print(image)

    #Check if there is a face in image FIXME
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
    storage = boto3.client('s3')
    storage_id = 'lambdas3source.people'

    # # Creating unique name
    timestamp = str(int(time.time()))
    randomnum = str(random.randint(0, 10000))
    unique_name = timestamp + "_" + randomnum + "_" + image_name

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
    url = 'https://s3.amazonaws.com/lambdas3source.people/' + image_new_name
    dynamo.update_profiles_table(profile_name, url)

    return redirect(url_for('homepage'))

@webapp.route('/image_info', methods=['GET', 'POST'])
def image_info():
    """Handles image_info route."""

    # Get User Input
    if request.method == 'GET':
        return render_template("image.html")

    image_name = request.form['image_name']
    tags = dynamo.query_tags(image_name)
    print(tags)

    return render_template("image.html", image_name=image_name, tags=tags)


@webapp.route('/query_submit', methods=['POST'])
def query_submit():
    """Handles query_submit route."""

    tags = request.form['query']

    if not tags:
        return redirect(url_for('homepage'))
    image_list = dynamo.query_tag_table(tags)
    print(tags)
    return render_template("homepage.html", image_names=image_list, query=[tags])

@webapp.route('/collages', methods=['GET'])
def make_collage():
    """Handles collages route."""
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

def valid_image_extension(ext):
    """Determines if image is of a valid extension"""
    allowed_image_extensions = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif']

    for extension in allowed_image_extensions:
        if ext == extension:
            return True

    return False

@webapp.route('/profiles', methods=['GET'])
def query_profiles():
    table = dynamodb_resource().Table("Profiles")
    profiles = table.scan(
        ProjectionExpression="#name,picture",
        ExpressionAttributeNames={"#name": "name"}
    )
    aDict = {}
    for profile in profiles['Items']:
        name = profile['name']
        picture = profile['picture']
        aDict[name] = picture

    return render_template("profiles.html", dict =aDict)

# <<<<<<< HEAD #TODO do we need this lambda_handler?
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
#
# =======
# >>>>>>> c18fd9ced68265aa0fd9518a3b9fdf505b205101
