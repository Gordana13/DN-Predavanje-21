#!/usr/bin/env python
import os
import jinja2
import webapp2

from google.appengine.api import users

from models import Register


template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}
        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            sign_in = True
            logout_url = users.create_logout_url("/")
            output = {
                "user": user,
                "sign_in": sign_in,
                "logout_url": logout_url,
            }
        else:
            sign_in = False
            login_url = users.create_login_url("/")
            output = {
                "user": user,
                "sign_in": sign_in,
                "login_url": login_url,
            }
        return self.render_template("hello.html", output)

class GuestbookHandler(BaseHandler):
    def get(self):
        return self.render_template("guestbook.html")

class SaveHandler(BaseHandler):
    def post(self):
        name = self.request.get('name')
        surname = self.request.get('surname')
        message = self.request.get('message')

        user = users.get_current_user()
        if user:
            email = user.email()

        if "<script>" in message:
            return self.write("You can't hack me! :)")

        save = Register(name=name, surname=surname, email=email, message=message)
        save.put()

        return self.render_template("save.html")

class MessagesHandler(BaseHandler):
    def get(self):
        msg = Register.query().fetch()
        output = {"msg": msg}
        return self.render_template("messages.html", output)

class DetailsHandler(BaseHandler):
    def get(self, details_id):
        message = Register.get_by_id(int(details_id))
        user = users.get_current_user()
        if user:
            admin = users.is_current_user_admin()
            output = {
                "admin": admin,
                "message": message
            }
        else:
            admin = False
            output = {
                "admin": admin,
                "message": message
            }
        return self.render_template("details.html", output)

class EditHandler(BaseHandler):
    def get(self, details_id):
        message = Register.get_by_id(int(details_id))
        output = {
            "message": message
        }
        return self.render_template("edit.html", output)

    def post(self, details_id):
        message = Register.get_by_id(int(details_id))
        message.name = self.request.get("name")
        message.surname = self.request.get("surname")
        message.email = self.request.get("email")
        message.message = self.request.get("message")
        message.put()

        return self.redirect("/messages")

class DeleteHandler(BaseHandler):
    def get(self, details_id):
        message = Register.get_by_id(int(details_id))
        output = {
            "message": message
        }
        return self.render_template("delete.html", output)

    def post(self, details_id):
        message = Register.get_by_id(int(details_id))
        message.key.delete()

        return self.redirect("/messages")

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/guestbook', GuestbookHandler),
    webapp2.Route('/save', SaveHandler),
    webapp2.Route('/messages', MessagesHandler),
    webapp2.Route('/details/<details_id:\d+>', DetailsHandler),
    webapp2.Route('/details/<details_id:\d+>/edit', EditHandler),
    webapp2.Route('/details/<details_id:\d+>/delete', DeleteHandler),
], debug=True)
