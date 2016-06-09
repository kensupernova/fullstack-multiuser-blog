#coding:utf-8
import os
import re
import random
import hashlib
import hmac
import string
## timezone
# import pytz

#for HW5
import logging
import json
from string import letters
from datetime import datetime, timedelta
import time

import webapp2 ## in GAE running environment
import jinja2

from google.appengine.ext import db
from google.appengine.api import memcache
# from google.appengine.ext import ndb

## 
from models import User, Post, Comment, Like
from helpers import render_str, valid_pw, make_pw_hash, users_key, blog_key, comment_key, like_key


#------------for setting the cookie
secret="iamsecret"

## regex patterin for validate username, password, email address
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

def valid_username(username):
    return username and USER_RE.match(username)

def valid_password(password):
    return password and PASS_RE.match(password)

def valid_email(email):
    return not email or EMAIL_RE.match(email)

def make_secure_val(val):
    return '%s-%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('-')[0]
    if secure_val == make_secure_val(val):
        return val

# #------hash the pw
# def make_salt(length = 5):
#     return ''.join(random.choice(letters) for x in xrange(length))

# def make_pw_hash(name, pw, salt = None):
#     if not salt:
#         salt = make_salt()
#     h = hashlib.sha256(name+pw+salt).hexdigest()
#     return "%s,%s" %(salt,h)

# def valid_pw(name, pw, h):
#    salt = h.split(",")[0]
#    return h == make_pw_hash(name, pw, salt)


# def users_key(group='default'):
#     return db.Key.from_path('users',group)

# def blog_key(group = 'default'):
#     return db.Key.from_path('blogs', group)

# def comment_key(group ="default"):
#     return db.Key.from_path('comments', group)

# def like_key(group ="default"):
#     return db.Key.from_path('likes', group)

#cache the post for hw6
def cache_computation(self): 
    #start_time=time.time()
    cache={}
    key=self.length()
    if key in cache:
       r=cache[key]
    else:
       r= Post.all().order('-created')
    return r    

### memcache to store posts, comments, likes
def age_set(key,val):
    ## check the size of cache, if > 2 MB, flush all
    if memcache.get_stats()["bytes"] > 2000000:
        memcache.flush_all()

    save_time=datetime.utcnow()

    ## memcache.delete(key)
    memcache.set(key, (val, save_time))
    
def age_get(key):
    r = memcache.get(key)
    if r:
        val, save_time=r
        age = (datetime.utcnow()-save_time).total_seconds()
    else:
        val, age = None, 0
    return val, age

def age_str(name, age):
    s = '%s queried %s seconds ago'
    age=int(age)
    if age==1:
        s = s.replace('seconds','second')
    return s % (name, age)

def add_post(post):
    post.put() ## save to datastore

    mc_key = mc_key = "POST_%s"% post.key().id()
    age_set(mc_key, post) ## save to memcache

    get_posts(update = True) ## update the posts in memcache
    return str(post.key().id())

def add_post_no_cache(post):
    post.put() ## save to datastore

    get_posts(update = True) ## update the posts in memcache
    return str(post.key().id())


def delete_post(post):
    # print("delet post %s.... " % post.key().id())
    ## delete this post from memcache
    try:
        mc_key = "POST_%s"% post.key().id()
        memcache.delete(mc_key) ## delete from cache
        post.delete() ## delete from datastore
        # memcache.flush_all()

        ## udpate posts in memcache
        get_posts(update = True)
        
        return True
    except e:
        return False

def delete_post_no_cache(post):
    try:
        post.delete()
        ## udpate posts in memcache
        get_posts(update = True)
        return True
    except e:
        ## udpate posts in memcache
        get_posts(update = True)
        return False

def get_post(post_id):
    mc_key = "POST_%s"% post_id
    post, age = age_get(mc_key)

    if post is None:
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        age_set(mc_key, post)
        age = 0
    return post, age

## make use of the posts that are already stored
## when visiting front page
def get_post_from_posts_of_frontpage(post_id):
    ""

def get_post_no_cache(post_id):
    key = db.Key.from_path('Post', int(post_id), parent=blog_key())
    post = db.get(key)

    return post, 0

def get_posts(update = False):
    mc_key='BLOGS'
    posts, age=age_get(mc_key)

    if update or posts is None:
        q=Post.all().order('-created').fetch(limit=10)
        #q = db.GqlQuery("select * from Post order by created desc limit 10")
        posts=list(q)
        age_set(mc_key,posts)
        age = 0
        
    return posts, age

def add_comment(comment, post):
    comment.put()
    get_comments(update=True, post=post)
    return str(comment.key().id())

def get_comments(update=False, post=None):
    # mc_key='COMMENTS_%s' % str(post.key().id())

    # comments, age=age_get(mc_key)
    # if update or comments is None:
    #     comments = post.comments_by_post.order('created')
    #     comments=list(comments)
    #     age_set(mc_key, comments)
    #     age = 0

    #-------
    ## no cache for comments in order to save cost
    comments = post.comments_by_post.order('created')
    comments=list(comments)
    age = 0
        
    return comments, age

def add_like(like, post):
    like.put()
    get_likes(update=True, post=post)
    return str(like.key().id())

def delete_like(like, post):
    like.delete()
    get_likes(update=True, post=post)

def get_likes(update=False, post=None):
    mc_key = "LIKES_%s" % str(post.key().id())
    likes, age = age_get(mc_key)
    if update or likes is None:
        likes = post.likes_by_post.order("created")
        likes = list(likes)
        age_set(mc_key, likes)
        age = 0

    return likes, age




########################################################################
### request handlers
class BlogHandler(webapp2.RequestHandler):

#----------for initializing
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id') 
        if not uid:
            self.user = None
        else :
            self.user =  User.by_id(int(uid))
#------------for .json
        if self.request.url.endswith('.json'):
            self.format='json'
        else:
            self.format='html'

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)
#-------- for html rendering
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

#-------the follow is for json rendering
    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

        
#--------------set the cookie        
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header('Set-Cookie',
                                        '%s=%s; Path=/' %(name, cookie_val))
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def set_cookie(self, name, val):
        self.response.headers.add_header('Set-Cookie',
                                        '%s=%s; Path=/' %(name, val))
    def read_cookie(self, name):
        return self.request.cookies.get(name)

    def set_secure_cookie_with_expire(self, name, val, expire_time):
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/; expires=%s' %(name, make_secure_val(val), expire_time))
#------------log in
    def login(self, user):
        # self.set_secure_cookie('user_id',str(user.key().id()))
        # self.response.headers.add_header('Set-Cookie','user_id=%s; Path=/' % str(user.key().id()))
        # self.set_cookie('user_id', str(user.key().id()))
        expire_time = str(datetime.now() + timedelta(minutes=30))
        self.set_secure_cookie_with_expire('user_id', str(user.key().id()), expire_time)
        
#----------log out
    def logout(self):
        # self.response.delete_cookie('user_id')  
        self.set_cookie('user_id', "")
        # print "log out in blog handler:  %s" % self.read_secure_cookie('user_id')


class MainPage(BlogHandler):
  def get(self):
      self.write('I am ken. This is my blog project')
      


#--------
class BlogFront(BlogHandler):
    def get(self):
        
        #posts = Post.all().order('-created')
        #posts = db.GqlQuery("select * from Post order by created desc limit 10")
        #        if self.format=='.':    
        #            self.render('front.html', posts = posts)
        #        else:
        #            self.render_json([p.as_dict() for p in posts])  

        # posts, age = get_posts(True) 
        posts, age = get_posts(False) 

        uid = self.read_secure_cookie('user_id') 
        # uid = self.read_cookie('user_id') 
        #print("blogfront: current user id %s" % uid)

        if self.format=='html':    
            if self.user:
                self.render('front.html', posts = posts ,age=age_str("posts", age), user = self.user)
            else:
                self.render('front.html', posts = posts ,age=age_str("posts",age), user = None)
        else:
            return self.render_json([p.as_dict() for p in posts])
              


class PostPage(BlogHandler):
    def get(self, post_id):
        # post_key='POST_'+post_id
        # post, age = age_get(post_key)

        ## key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        ## post = db.get(key)

        # if not post:
        #     key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        #     post = db.get(key)
        #     age_set(post_key,post)
        #     age = 0

        post, post_age = get_post(post_id)

        if not post:
            self.render('404.html', requested_url = self.request.url, user = self.user)
            return

        ## get all the comments of the post
        # comments = post.comments_by_post
        # comments_key = "COMMENTS_" + post_id
        # # comments, comments_age = comments_get(comments_key)
        # comments, comments_age = age_get(comments_key)
        # if not comments:
        #     comments = post.comments_by_post
        #     # comments_set(comments_key, comments)
        #     age_set(comments_key, comments)
        #     comments_age = 0

        comments, comments_age = get_comments(post=post)
        # likes, likes_age = get_likes(update= True, post=post)
        likes, likes_age = get_likes(post=post)
        # likes, likes_age = post.likes_by_post, 0

        if not comments:
            print "no comments on this post!"

        if self.format=='html':    
            self.render("permalink.html", user= self.user, 
                post = post, age=age_str("post", post_age), 
                comments = comments, comments_age = age_str("comments", comments_age), 
                likes=likes, likes_age = age_str("likes", likes_age)
                )
        else:
            self.render_json(post.as_dict())


class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html", user=self.user)
        else:
            self.redirect("/login?redirect=%s" % "/blog/newpost")
            return

    def post(self):
        if not self.user:
            self.redirect("/login?redirect=%s" % "/blog/newpost")

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content, owner = self.user)
            p.put() ## store into database
            add_post(p)
            self.redirect('/blog/%s' % str(p.key().id()))
            # memcache.flush_all()
######the above is clear the cache after new post.
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

#___________ edit handler
class EditHandler(BlogHandler):
    
    def get(self, post_id):
        if not self.user:
            redirect = "/blog/%s/edit" % post_id
            self.redirect("/login?redirect=%s" % redirect)
            return

        post, age = get_post(post_id)

        if not post:
            self.error(404)
            return

        
        ## check whether current logged in user is owner of the blog
        # print "edit request user: %s" % self.user
        # print "edit post owner: %s" % post.owner
        if post.owner.name == self.user.name:
            self.render("newpost.html", user=self.user, subject=post.subject, content = post.content)
        else:
            redirect_url = "/blog/%s" % post_id
            self.render("unauthorized.html", post_id=post_id, user=self.user, redirect=redirect_url);
    def post(self, post_id):
        if not self.user:
            self.redirect("/login")

        post, age = get_post(post_id)

        if not post:
            self.error(404)
            return

        ## get texts from form
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post.subject = subject
            post.content = content
            post.put()
            add_post(post)
            self.redirect('/blog/%s' % str(post.key().id()))
            # memcache.flush_all()
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

#___________ delete handler
class DeleteHandler(BlogHandler):
    
    def post(self, post_id):
        if not self.user:
            # redirect = "/blog/%s/delete" % post_id
            # self.redirect("/login?redirect=%s" % redirect)
            # return

            redirect_url = "/login?redirect=/blog/%s" % post_id
            self.render_json(
                {
                    "isLogged": False,
                    "redirect": redirect_url
                })

            return

        post, age = get_post(post_id)

        if not post:
            # self.error(404)
            # return
            self.render_json({
                "isLogged": True,
                "detail":"can not found post"
                })
            return 

        ## check whether current logged in user is owner of the blog
        # print "edit request user: %s" % self.user
        # print "edit post owner: %s" % post.owner
        if post.owner.name == self.user.name:
            
            if delete_post(post):
                self.render_json({
                    "isLogged": True,
                    "canDelete": True,
                    "isDeleted": True
                    })
            else:
                self.render_json({
                    "isLogged": True,
                    "canDelete": True,
                    "isDeleted": False
                    })
            return
        else:
            # redirect_url = "/blog/%s" % post_id
            # self.render("unauthorized.html", post_id=post_id, user=self.user, redirect=redirect_url)
            self.render_json({
                "isLogged": True,
                "canDelete": False,
                "isDeleted": False
                })
            return

#___________ comment handler
class CommentHandler(BlogHandler):
    def post(self, post_id):
        # post_key='POST_'+post_id
        # post, post_age = age_get(post_key)

        # #key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        # #post = db.get(key)

        # if not post:
        #     key = db.Key.from_path('Post', int(post_id), parent=blog_key()) ## get key of the object first
        #     post = db.get(key) ## to retrieve object
        #     age_set(post_key, post)
        #     post_age = 0
        # if not post:
        #     self.error(404)
        #     return

        if not self.user:
            redirect_url = "/blog/%s" % post_id
            self.redirect("/login?redirect=%s" % redirect_url)
            return

        post, post_age = get_post(post_id)

        comment_content = self.request.get('add_comment_content').strip()

        if comment_content:
            comment = Comment(parent = comment_key(), content = comment_content, owner = self.user, post = post)
            comment.put() ## store into database
            ### delete cached post and comments by post_id 
            #----------------------!!!!!!
            # memcache.delete("COMMENTS_%s" % post_id)
            # memcache.delete("POST_%s" % post_id)
            add_comment(comment, post)

            # self.redirect('/blog/%s' % post_id)
            self.render_json({
                "isSuccess": True,
                'comment_content': comment_content,
                'comment_created_time': comment.get_created_time_str,
                'comment_owner_name': comment.owner.name
                })
            return
            
        else:
            # self.redirect('/blog/%s' % post_id)
            self.render_json({
                "isSuccess": False
                })
            return
        

#___________ like handler
class LikeHandler(BlogHandler):
    def post(self, post_id):
        # print ("likehanlder, current user: %s" % self.user)
        if not self.user:
            redirect_url = "/login?redirect=/blog/%s" % post_id
            self.render_json(
                {
                    "isLogged": False,
                    "redirect": redirect_url
                })

            return
            
        # post_key='POST_'+post_id
        # post, age = age_get(post_key)

        # if not post:
        #     key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        #     post = db.get(key)
        #     age_set(post_key, post)
        #     age = 0
        # if not post:
        #     self.error(404)
        #     return

        post, age = get_post(post_id)
        if not post:
            self.error(404)
            return

        ## if the owner of the post is the current logged user, display message
        if post.owner.name == self.user.name:
            self.render_json({
                "isLogged": True,
                "canLike": False})
            return


        ## check whether like is already, otherwise delete
        ## toggle like
        old_likes = post.likes_by_post
        # print("total old likes %s" % type(old_likes))
        like_by_user= None
        for old_like in old_likes: 
            # print("who liked this post: %s" % old_like.owner.name)  
            # print("%s ?? %s" %(old_like.owner.name, self.user.name)) 
            if old_like.owner.name  == self.user.name:
                like_by_user = old_like
                break;
                
        # print("like by logged user on this post : %s" % like_by_user)

        if not like_by_user:
            # print("add like ... ")
            like = Like(parent = like_key(), owner=self.user, post=post)
            # like.put()
            add_like(like, post)
            # time.sleep(1)
            self.render_json({
                "isLogged": True,
                "canLike": True,
                "isAdd": True})
            # self.redirect('/blog/%s' % str(post.key().id()))
        else:
            # print("delete like ...")
            # like_by_user.delete()
            delete_like(like_by_user, post)
            # time.sleep(1)
            self.render_json({
                "isLogged": True,
                "canLike": True,
                "isAdd": False})
            
            # self.redirect('/blog/%s' % str(post.key().id()))

       

        


#----------------------
class SignUp(BlogHandler):

    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username, email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
            
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()
            
    def done(self, *a, **kw):
        raise NotImplementedError 

    def done(self):
        #make sure the user has not already existed
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect("/welcome")   

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            ## if has redirect, go to that url
            redirect_url = self.request.get("redirect")
            self.login(u)
            if redirect_url:
                self.redirect(redirect_url)
            else:
                self.redirect('/')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(BlogHandler):
    def get(self):

        self.logout()
        self.redirect('/flush')
        self.redirect('/')
        
class Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name, user=self.user)
        else:
            self.redirect('/signup')

class Flush(BlogHandler):
    def get(self):        
        posts, age = get_posts()
        memcache.flush_all()
        self.redirect("/")
        #the above is to flush all the memcache.

class Cache(BlogHandler):
    def get(self):        
        self.render_json(memcache.get_stats())
        #the above is to show cache statistic

#--------------------
app = webapp2.WSGIApplication([
    ('/', BlogFront),
    ('/welcome', Welcome), 
    ('/blog/?(?:.json)?', BlogFront),
    ('/blog/([0-9]+)(?:.json)?', PostPage),
    ('/blog/newpost', NewPost),
    ('/blog/([0-9]+)/edit', EditHandler),
    ('/blog/([0-9]+)/delete', DeleteHandler),
    ('/blog/([0-9]+)/like', LikeHandler),
    ('/blog/([0-9]+)/comment', CommentHandler),
    ('/flush', Flush),
    ('/cache', Cache),
    ('/signup', SignUp),
    ('/login', Login),
    ('/logout', Logout),                
    ],
    debug=True)
