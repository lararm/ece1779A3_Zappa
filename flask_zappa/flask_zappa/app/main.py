
from flask import render_template, session, request, escape, redirect, url_for,flash
from app import webapp

import datetime


@webapp.route('/')
def main():
    return redirect(url_for('homepage'))
    

