"""
File:     __init__.py
Authors:  Irfan Khan 999207665, Larissa Ribeiro Madeira 1003209173
Date:     November 2017
Purpose:  Web application initialization file
"""
from flask import Flask
from app import config
webapp = Flask(__name__)
webapp.secret_key = config.SECRET_KEY

from app import dynamo
from app import homepage
from app import main
