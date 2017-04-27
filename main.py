#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import cgi
import jinja2
import os
from google.appengine.ext import db
import hashlib
import hmac

# set up jinja
template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

#creates a hash string from the input value using hmac
def hash_str(s):
    SECRET = "boba" #set a secret word
    return hmac.new(SECRET, s).hexdigest()

#accepts a string, calls hash_str(), to create a hash based on the
#input string and outputs the input string and the hash as "string,hash"
def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

#accepts a string in the form of " 'word', 'output of a hash algorithm' "
def check_secure_val(h):
    val = h.split('|')[0] #takes the value 'h' and splits the string at the comma, splitting the string from the hash and taking the first part of that by using [0], storing that in 'val'
    if h == make_secure_val(val): #this runs val back through the hash creation algorithm and compares it to the completion of make_secure_val(), this reaccomplishes the hash creation to ensure the values match
        return val #if it passes the test above, return the input string only


class Blog(db.Model):
    title = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    blog_body = db.TextProperty(required = True)

class Handler(webapp2.RequestHandler):
    """ A base RequestHandler class for our app.
        The other handlers inherit form this one.
    """

    def renderError(self, error_code):
        """ Sends an HTTP error code and a generic "oops!" message to the client. """

        self.error(error_code)
        self.response.write("Oops! Something went wrong.")


class BlogHandler(Handler): #makes a handler that inherits from the Handler class created above. This class deals with all requests submitted to /blog. this is set below in the 'app' section
    def get(self):

        #this first 'paragraph' is what sets the cookie in the client's browser
        visit = 0
        visit_cookie_str = self.request.cookies.get('visit') #requests the value of the cookie's visit value, defult 0 value set above
        if visit_cookie_str: #this checks to see if there is a value in visit_cookie_str. if it's not 'None', do the if statement
            cookie_val = check_secure_val(visit_cookie_str) #check the secure value on the visit cookie str using our function above. it returns 'None' if it is not valid
            if cookie_val: #if something other than 'None' was returned from check_secure_val()
                visit = int(cookie_val) #the visit counter is updated from it's default '0' value to whatever the number is in the visit cookie
        #if visit.isdigit(): #checks to see if visit consists of only digits, if it does, add 1 to the amount of times we've visited the page. this isnt needed after updating the if statement above, converting visit to an int earlier. we no longer need to see if it's a digit
            #visit = int(visit) + 1 #convert visit to an integer so we can increment it up by 1
        #else: #if we get a False back from isdigit(), set visit to 0
            #visit = 0
        visit =+ 1 #increment our visit counter up by 1
        new_visit_cookie_val = make_secure_val(str(visit))[0] #setting the updated visit counter and creating a new hash for the updated number
        self.response.headers.add_header('Set-Cookie', 'visit=%s' % new_visit_cookie_val) #tells the header to set a cookie. we're inputing the value of visit. we get that value with with string substitution, inputting the value we just updated above

        #this second 'paragraph' is what passes all the data required to the html template and then writes that template to the browser
        blog_list = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC LIMIT 5") #sets the value of blog_list to the database query of 'Blog' database I created above, then orders them by creation date, newest to oldest, and only shows the last 5
        b = jinja_env.get_template("blog.html") #sets 'b' to use jijna to use the template "blog.html" that was created to show the last 5 blogs created.
        content = b.render(blogs = blog_list, #this passes the 2 variables that are in the template (blogs and visits) and equates those values to the ones created within this class
                            visits = new_visit_cookie_val    #this is how I pass the data between Python code and the HTML templates I've created
                            )
        self.response.write(content) #Make everything that content was set equal to, show up on in the browser



class NewPostHandler(Handler):
    def get(self):
        post = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC LIMIT 5")
        n = jinja_env.get_template("newpost.html")
        content = n.render(post = post)
        self.response.write(content)

    def post(self):
        title = self.request.get("title")
        new_post = self.request.get("post")
        n = jinja_env.get_template("newpost.html")

        if title and new_post:
            b = Blog(
                    title = title,
                    blog_body = new_post
                    )
            b.put()


        content = n.render(
                        title = title,
                        post = new_post,
                        error = self.request.get("error"))
        self.response.write(content)

class ViewPostHandler(Handler):
    def get(self, id):
        id = int(id)
        blog = Blog.get_by_id(id)

        b = jinja_env.get_template("/blog_post.html")
        content = b.render(blog = blog)
        self.response.write(content)

app = webapp2.WSGIApplication([
    ('/blog', BlogHandler),
    ('/newpost', NewPostHandler),
    webapp2.Route('/blog/<id:\d+>', ViewPostHandler)
], debug=True)
