

from flask import Flask

webapp = Flask(__name__)

from app import main
from app import example4
from app import homepage
from app import dynamo



