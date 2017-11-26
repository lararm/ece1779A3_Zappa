
from flask import render_template, url_for
from app import webapp

import datetime


@webapp.route('/')
def main():
    return render_template("homepage.html")
    

