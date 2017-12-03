"""
File:     main.py
Authors:  Irfan Khan 999207665, Larissa Ribeiro Madeira 1003209173
Date:     November 2017
Purpose:  Web application main function
"""
from flask import session, escape, redirect, url_for
from app import webapp
@webapp.route('/')
def main():
    """Handles default route"""
    if 'username' in session:
        print("Session user is: %s" % escape(session['username']))
        return redirect(url_for('homepage'))
    return redirect(url_for('login'))
