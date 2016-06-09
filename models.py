#coding: utf-8
## models 
from dateutil import tz

from google.appengine.ext import db
from helpers import render_str, render_post, valid_pw, make_pw_hash, users_key, blog_key, comment_key, like_key

################################################
## data models
#-------------user model
class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key()) ## query from datastore by id

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get() ## query from datastore and filter by name
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u

    

#--------------  Post model
class Post(db.Model):
    owner = db.ReferenceProperty(User, required=True, collection_name='posts')
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", post = self)

    def render_frontpage(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post-frontpage.html", post = self)

    def get_created_time_str(self):
        time_utc = "%Y-%m-%d %H:%M:%S UTC%z"
        # time_fmt='%c'
        # tzinfo=pytz.UTC
        utc_time = self.created.replace(tzinfo=tz.tzutc())
        # obj = datetime.strptime(utc_time.strftime(utc_time), time_utc)
        # obj = obj.astimezone(tz.tzlocal())
        local_time = utc_time.astimezone(tz.tzlocal())
        return local_time.strftime(time_utc)

    def get_modified_time_str(self):
        # time_fmt='%c'
        time_utc = "%Y-%m-%d %H:%M:%S UTC%z"
        
        return self.last_modified.replace(tzinfo=tz.tzutc()).strftime(time_utc)
    
    def as_dict(self):
        time_fmt='%c' ## local time format
        d = {'subject':self.subject,
             'content':self.content,
             'created':self.created.replace(tzinfo=tz.tzutc()).strftime(time_utc),
             'last_modified':self.last_modified.replace(tzinfo=tz.tzutc()).strftime(time_utc)
            }
        return d

#--------------    
class Comment(db.Model):
    owner = db.ReferenceProperty(User, required=True, collection_name='comments_by_owner')
    post = db.ReferenceProperty(Post, required=True, collection_name='comments_by_post')
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def get_created_time_str(self):
        #time_fmt='%c'
        time_utc = "%Y-%m-%d %H:%M:%S UTC%z"
        return self.created.replace(tzinfo=tz.tzutc()).strftime(time_utc)

    def get_modified_time_str(self):
        #time_fmt='%c'
        time_utc = "%Y-%m-%d %H:%M:%S UTC%z"  
        return self.last_modified.replace(tzinfo=tz.tzutc()).strftime(time_utc)
  
    def as_dict(self):
        #time_fmt='%c'
        time_utc = "%Y-%m-%d %H:%M:%S UTC%z"
        d = {
             'content':self.content,
             'created':self.created.replace(tzinfo=tz.tzutc()).strftime(time_utc),
             'last_modified':self.last_modified.replace(tzinfo=tz.tzutc()).strftime(time_utc)
            }



class Like(db.Model):
    owner = db.ReferenceProperty(User, required=True, collection_name='likes_by_owner')
    post = db.ReferenceProperty(Post, required=True, collection_name='likes_by_post')
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def as_dict(self):
        #time_fmt='%c'
        time_utc = "%Y-%m-%d %H:%M:%S %Z%z"
        d = {
             'created':self.created.replace(tzinfo=tz.tzutc()).strftime(time_utc),
             'last_modified':self.last_modified.replace(tzinfo=tz.tzutc()).strftime(time_utc)
            }

