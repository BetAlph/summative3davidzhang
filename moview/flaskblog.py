import os
from flask import Flask, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, LoginForm, MovieSearchForm, PostForm
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker

from postlist import *

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

'''
HOW TO CHECK GLOBAL VARIABLES INSIDE JINJA
TO DO
So basically:
1. Download a copy of username password pairs from DB
2. User inputs username and password into form
3. Check if form.username && form.password matches any pair
4. If match, set GLOBAL is_logged=True. Otherwise return login page again.
5. Redirect to home page

export FLASK_APP="flaskblog.py" DATABASE_URL="postgres://wvenojhujcidrk:db3cff2e367514a94dff20e895be599f419c7c92bf5e907f2358e4f8ff7f78f3@ec2-54-163-226-238.compute-1.amazonaws.com:5432/d6k656cqrila1b" FLASK_DEBUG=1

'''

is_logged = False
current_user = ""

usernames = db.execute("SELECT username FROM users").fetchall()
searchresults = []

attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response"]

@app.route("/")
@app.route("/home", methods=['GET','POST'])
def home():
    form = MovieSearchForm()
    if is_logged:

        if (form.search.data != None):
            global searchresults
            searchresults = []
            results = db.execute("SELECT * FROM movies WHERE title LIKE :src OR lowercase LIKE :src OR year LIKE :src OR imdbid LIKE :src;",{"src": "%"+form.search.data+"%"}).fetchall()
            for i in range(len(results)):
                temp = {}
                attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response","lowercase"]
                for j in range(len(results[i])):
                    temp[attrlist[j]] = results[i][j]
                searchresults.append(temp)


        return render_template('home.html', posts=posts,is_logged=True, form=form,searchresults = searchresults)
    else:
        return render_template('home.html', posts=posts)
    return render_template('home.html', posts=posts,is_logged=True,form=form)

@app.route("/about")
def about():
    if is_logged:
        return render_template('about.html', title='About',is_logged=True)
    else:
        return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    unok = True
    emok = True
    if is_logged:
        return redirect(url_for('home'))
    usernames = db.execute("SELECT username FROM users").fetchall()
    emails = db.execute("SELECT email FROM users").fetchall()
    form = RegistrationForm()

    for username in usernames:
        if form.username.data == username[0]:
            unok = False
    for email in emails:
        if form.email.data == email[0]:
            emok = False

    '''Check For Duplicate Username & Email'''
    if form.validate_on_submit() and unok and emok:
        db.execute("INSERT INTO users (username, email, password) VALUES (:un, :em, :pw);",{"un": form.username.data, "em": form.email.data, "pw": form.password.data})
        db.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    elif not unok and emok:
        flash(f'The username "{form.username.data}" has been taken!', 'danger')
        return render_template('register.html', title='Register', form=form)
    elif not emok and unok:
        flash(f'The email "{form.email.data}" has been registered already!', 'danger')
        return render_template('register.html', title='Register', form=form)
    elif not unok and not emok:
        flash(f'The username "{form.username.data}" and email "{form.email.data}" have both been taken!', 'danger')
        return render_template('register.html', title='Register', form=form)
    '''Return Same Website If Fields Do Not Satisfy Requirements'''
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    global is_logged
    global current_user
    loginok = False
    form = LoginForm()
    if form.validate_on_submit():
        '''
        Check For Special Characters As Part Of Special Characters
        '''
        for letter in form.password.data:
            for character in specialChars:
                if letter == character:
                    flash('Login Unsuccessful. Please check username and password for any special characters!', 'danger')
                    return render_template('login.html', title='Login', form=form)
        try:
            for letter in form.username.data:
                for character in specialChars:
                    if letter == character:
                        flash('Login Unsuccessful. Please check username and password for any special characters!', 'danger')
                        return render_template('login.html', title='Login', form=form)
        except:
            print(form.username.data,specialChars)
        '''
        Check If Username & Password Are Matching Pairs
        '''

        userinfo = db.execute("SELECT * FROM users WHERE (username = :un);",{"un": form.username.data}).fetchall()
        ''' userinfo Is A Row Of Data, userinfo[0][3] Is The Password Of User'''
        try:
            if form.password.data == userinfo[0][3]:
                is_logged = True
                current_user = form.username.data
                message = 'You have been logged in, ' + current_user + '!'
                flash(message, 'success')
                return redirect(url_for('home'))
            else:
                flash('Login Unsuccessful. Please check username and password and make sure that they are correct!', 'danger')
        except:
            flash('Login Unsuccessful. Please check username and password and make sure that they are correct!', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    global is_logged
    global current_user
    is_logged = False
    current_user = ""
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

@app.route("/movies/<imdb_id>")
def movie(imdb_id):
    """Lists details about a single movie."""

    # Make sure movie exists.
    movie = db.execute("SELECT * FROM movies WHERE imdbid = :id", {'id': imdb_id}).fetchone()
    if movie is None:
        return render_template("error.html", message="No such movie.")

    temp = {}
    attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response","lowercase"]
    for j in range(len(movie)):
        temp[attrlist[j]] = movie[j]

    # Get all reviews.
    reviews = db.execute("SELECT * FROM reviews WHERE imdbid = :imdbid",{"imdbid": imdb_id}).fetchone()
    if reviews is None:
        reviews = []
    return render_template("movie.html", movie=temp, reviews=reviews)

@app.route("/movies/<imdb_id>/new")
def newreview(imdb_id):
    form = PostForm()
    """Allows users to write posts."""

    # Make sure user hasn't made a review already.
    review = db.execute("SELECT * FROM reviews WHERE userid = :uid AND imdbid = :id", {'': current_user, 'id': imdb_id}).fetchone()
    if movie is not None:
        return redirect(url_for('movies/imdb_id'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')

@app.route("/post/new", methods=['GET', 'POST'])
def new_post():
    if is_logged == False:
        return redirect(url_for('home'))
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')
