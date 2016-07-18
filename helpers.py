#coding: utf-8
##-------------------- helpers
import os

import random
import hashlib
import hmac
import string

import logging
import json
from string import letters
from datetime import datetime, timedelta
import time


import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

        
def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

#------hash the pw
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name+pw+salt).hexdigest()
    return "%s,%s" %(salt,h)

def valid_pw(name, pw, h):
   salt = h.split(",")[0]
   return h == make_pw_hash(name, pw, salt)


def users_key(group='default'):
    return db.Key.from_path('users',group)


def blog_key(group = 'default'):
    return db.Key.from_path('blogs', group)

def comment_key(group ="default"):
    return db.Key.from_path('comments', group)

def like_key(group ="default"):
    return db.Key.from_path('likes', group)