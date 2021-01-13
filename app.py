from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta, datetime
from werkzeug.utils import secure_filename
import flask_whooshalchemy as wa
import os

cw = os.getcwd()

app = Flask(__name__)
app.secret_key = "#$%#@$EDFDDFGsdfsdfskijsfdsd@#$7898"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///db.sqlite3'
app.config["UPLOAD_FOLDER"] = '/static/media/images'
app.config["UPLOAD_FOLDER_FULL"] = cw + '\\static\\media\\images'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["WHOOSH_BASE"] = "whoosh_search_configs"
app.permanent_session_lifetime = timedelta(days=365)

db = SQLAlchemy(app)


class Users(db.Model):
  _id = db.Column("id", db.Integer, primary_key=True)
  name = db.Column("name", db.String(100), nullable=False)
  email = db.Column("email", db.String(100), nullable=False)
  password = db.Column("password", db.String(100), nullable=False)

class Sightings(db.Model):
  __searchable__ = ['title', 'species', 'comment', 'by', 'country', 'site']
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(100))
  picture = db.Column(db.String(200))
  species = db.Column(db.String(200))
  comment = db.Column(db.String(200))
  by = db.Column(db.String(200))
  uploaded = db.Column(db.String(200))
  email = db.Column(db.String(200))
  country = db.Column(db.String(200))
  site = db.Column(db.String(200))

  def __init__(self, title, picture, species, comment, by, uploaded, email, country, site):
    self.title = title
    self.picture= picture
    self.species = species
    self.comment = comment
    self.by = by
    self.uploaded = uploaded
    self.email = email
    self.country = country
    self.site = site

wa.whoosh_index(app, Sightings)


class Comments(db.Model):
  _id = db.Column("id", db.Integer, primary_key=True)
  post_id = db.Column(db.Integer)
  comment = db.Column(db.String(300))
  by = db.Column(db.String(100))

  def __init__(self, post_id, comment, by):
    self.post_id = post_id
    self.comment = comment
    self.by = by


@app.route("/")
def index():
  if "user" in session:
    return render_template("signhome.html", user=session["user"])
  else:
    return render_template("nonsignhome.html")


@app.route("/signup", methods=["POST", "GET"])
def signup():
  if request.method == "POST":
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    found_email = Users.query.filter_by(email=email).first()

    if found_email:
      flash("Account with the same email already exists")
      return redirect(url_for("signup"))
    
    data = Users(
      name = name,
      email = email,
      password = password
    )

    db.session.add(data)
    db.session.commit()

    session["user"] = name
    session["email"] = email

    return redirect(url_for("index", user=session["user"]))


  return render_template("signup.html")


@app.route("/login", methods=["POST", "GET"])
def Login():
  if request.method == "POST":
    email = request.form["email"]
    password = request.form["password"]

    found_email = Users.query.filter_by(email=email).first()

    if found_email:
      if found_email.password == password:
        session["user"] = found_email.name
        session["email"] = email
        return redirect(url_for("index", user=session["user"]))
      else :
        flash("Incorrect Password")
        return redirect(url_for("Login"))
    else :
      flash("Email not Found")
      return redirect(url_for("Login"))
  return render_template("login.html")


@app.route("/sightings")
def sightings():
  values = Sightings.query.all()
  if "user" in session:
    return render_template("signsight.html", values=values, user=session["user"])
  else :
    return render_template("nonsignsight.html", values=values)


@app.route("/sighting/add/post", methods=["POST", "GET"])
def add_sighting():
  if "user" in session:
    if request.method == "POST":
      title = request.form["title"]

      picture = request.files["picture"]
      pic = secure_filename(picture.filename)

      species = request.form["species"]
      comment = request.form["comment"]
      country = request.form["country"]
      site = request.form["site"]

      now = datetime.now()
      dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

      picture.save(app.config["UPLOAD_FOLDER_FULL"]+'\\'+pic)

      db.session.add(Sightings(
        title,
        app.config["UPLOAD_FOLDER"] + "/" + pic,
        species,
        comment,
        session["user"],
        dt_string,
        session["email"],
        country,
        site
      ))
      db.session.commit()

      return redirect(url_for("sightings"))

    return render_template("add_sighting.html")
  else :
    return redirect(url_for("Login"))

@app.route('/sight/detail/<int:id>')
def show_sight(id):
  found_id = Sightings.query.filter_by(id=id).first()
  found_comments = Comments.query.filter_by(post_id=id).all()
  if found_id:
    if 'user' in session:
      return render_template("signshow_sight.html", values=found_id, user=session['user'], comments=found_comments)
    else :
      return render_template('nonsignshow_sight.html', values=found_id, comments=found_comments)
  else :
    return redirect(url_for("sightings"))


@app.route('/post/comment/sight/<int:id>', methods=['POST', 'GET'])
def comment_add(id):
  found_post = Sightings.query.filter_by(id=id).first()
  if found_post:
    if 'user' in session:
      if request.method == 'POST':
        comment = request.form['comment']
        db.session.add(Comments(id, comment, session['user']))
        db.session.commit()
        return redirect(f'/sight/detail/{id}')
      return render_template('add_comment.html')
    else:
      return redirect(url_for("Login"))
  else :
    return redirect(url_for('index'))


@app.route('/you/posts', methods=['POST', 'GET'])
def your_posts():
  found_posts = Sightings.query.filter_by(email=session['email']).all()
  if 'user' in session:
    if request.method == 'POST':
      id_post = request.form['remove']
      found_post = Sightings.query.filter_by(id=id_post).first()
      found_comments = Comments.query.filter_by(post_id=id_post).all()

      rem_file = found_post.picture.replace('/static/media/images','')
      os.remove(app.config["UPLOAD_FOLDER_FULL"] + rem_file)
      db.session.delete(found_post)
      for item in found_comments:
        db.session.delete(item)

      db.session.commit()

      return redirect(url_for('your_posts'))
    return render_template('your_posts.html', posts=found_posts)
  else :
    return redirect(url_for('index'))


@app.route('/search', methods=['POST', 'GET'])
def search():
  query = request.args.get("query")
  if 'user' in session: 
    return render_template('signsearch.html',values=Sightings.query.whoosh_search(query).all(), user=session['user'])
  else :
    return render_template('nonsignsearch.html',values=Sightings.query.whoosh_search(query).all())


@app.route("/logout")
def logout():
  session.pop("user")
  session.pop("email")
  return redirect(url_for("index"))


if __name__ == "__main__":
  db.create_all()
  app.run(debug=True)