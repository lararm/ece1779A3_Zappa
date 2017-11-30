

from flask import Flask

from app import config
webapp = Flask(__name__)
webapp.secret_key = config.SECRET_KEY

from app import main
from app import homepage
from app import dynamo
#from app import collage


