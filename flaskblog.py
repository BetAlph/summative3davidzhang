import os
from flask import Flask, render_template, url_for, flash, redirect, request, session, make_response, abort, jsonify
from forms import RegistrationForm, LoginForm, MovieSearchForm, ReviewForm
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
import omdb
from accolades import *

app = Flask(__name__)
SECRET_KEY = '\x96^\xe7W\xd3#\xb8\x97\x98L\xd9\xb0\r\x83cD\x14\x87k\xfe\xefY\xff\x87'
app.config['SECRET_KEY'] = SECRET_KEY
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
Session(app)
app.config['JSON_SORT_KEYS'] = False

'''
export FLASK_APP="flaskblog.py" DATABASE_URL="postgres://wvenojhujcidrk:db3cff2e367514a94dff20e895be599f419c7c92bf5e907f2358e4f8ff7f78f3@ec2-54-163-226-238.compute-1.amazonaws.com:5432/d6k656cqrila1b" FLASK_DEBUG=1
'''




usernames = db.execute("SELECT username FROM users").fetchall()
searchresults = []


API_KEY = '2c402f70'
omdb.set_default('apikey', API_KEY)

@app.route("/", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
def home():

    if 'is_logged' not in session:
        session['is_logged'] = False
    if 'current_user' not in session:
        session['current_user'] = ""
    form = MovieSearchForm()
    if session['is_logged'] == True:

        if (form.search.data != None):
            global searchresults
            searchresults = []
            results = db.execute("SELECT * FROM movies WHERE title LIKE :src OR lowercase LIKE :src OR year LIKE :src OR imdbid LIKE :src;",{"src": "%"+form.search.data+"%"}).fetchall()
            for result in results:
                imdb_id = result[3]
                attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response"]
                omdbResults = omdb.request(i=imdb_id)
                omdbData = omdbResults.json()
                temp = {}
                for attr in attrlist:
                    temp[attr] = omdbData[attr]
                searchresults.append(temp)
            '''
            for i in range(len(results)):
                temp = {}
                attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response","lowercase"]
                for j in range(len(results[i])):
                    temp[attrlist[j]] = results[i][j]
                searchresults.append(temp)
'''

        return render_template('home.html', accolades=accolades ,is_logged=True, form=form,searchresults = searchresults)
    else:
        return render_template('home.html', accolades=accolades)
    return render_template('home.html', accolades=accolades,is_logged=True,form=form)

@app.route("/about")
def about():
    return render_template('about.html', accolades=accolades)


@app.route("/register", methods=['GET', 'POST'])
def register():
    unok = True
    emok = True
    if session['is_logged']:
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
    if 'is_logged' not in session:
        session['is_logged'] = False
    if 'current_user' not in session:
        session['current_user'] = ""
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
                session['current_user'] = form.username.data
                message = 'You have been logged in, ' + session['current_user'] + '!'

                flash(message, 'success')

                '''if form.remember:
                    session.permanent = True
                else:
                    session.permanent = False'''
                session['is_logged'] = True
                return redirect(url_for('home'))
            else:
                flash('Login Unsuccessful. Please check username and password and make sure that they are correct!', 'danger')
        except:
            flash('Login Unsuccessful. Please check username and password and make sure that they are correct!', 'danger')

    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    session['is_logged'] = False
    session['current_user'] = ""
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

@app.route("/movies/<imdb_id>", methods=['GET', 'POST'])
def movie(imdb_id):

    form = ReviewForm()

    if form.validate_on_submit():
        db.execute("INSERT INTO reviews (userid, imdbid, rating, content) VALUES (:un, :ii, :ra, :co);",{"un": session['current_user'], "ii": imdb_id, "ra": form.select.data, "co": form.content.data})
        db.commit()

        return(redirect(url_for('movie', imdb_id=imdb_id)))
    """Lists details about a single movie."""

    # Make sure movie exists.
    movie = db.execute("SELECT * FROM movies WHERE imdbid = :id", {'id': imdb_id}).fetchone()
    if movie == None:
        abort(404)
    else:
        imdb_id = movie[3]
        attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response"]
        omdbResults = omdb.request(i=imdb_id)
        omdbData = omdbResults.json()
        temp = {}
        for attr in attrlist:
            temp[attr] = omdbData[attr]

        for j in range(len(movie)):
            temp[attrlist[j]] = movie[j]
        # Get all reviews.
        revu = db.execute("SELECT * FROM reviews WHERE imdbid = :imdbid",{"imdbid": imdb_id}).fetchall()
        attrlist2 = ["Author", "MovieID", "Rating", "ReviewContent"]
        reviews = []
        temp2 = {}

        userRev = False

        for i in range(len(revu)):
            temp2 = {}
            for j in range(len(revu[i])):
                temp2[attrlist2[j]] = revu[i][j]
            reviews.append(temp2)
            if temp2['Author'] == session['current_user']:
                userRev = True
        if revu == None:
            reviews = []
        try:
            avgR = ( float( temp['Metascore'] ) + float( temp['imdbRating'] ) * 10 ) / 2
        except:
            try:
                avgR = temp['imdbRating']
            except:
                avgR = temp['Metascore']
        return render_template("movie.html", movie=temp, reviews=reviews, avgR=avgR, form = form, userRev=userRev)

@app.route('/api/<imdb_id>', methods=["GET"])
def get_api(imdb_id):

    try:
        movie = db.execute("SELECT * FROM movies WHERE imdbid = :id", {"id": imdb_id}).fetchall()
        reviews = db.execute("SELECT * FROM reviews WHERE imdbid = :id", {"id": imdb_id}).fetchall()
        avgS = 0
        c = 0

        imdb_id = movie[0][3]
        attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response"]
        omdbResults = omdb.request(i=imdb_id)
        omdbData = omdbResults.json()
        movieInfo = {}
        for attr in attrlist:
            movieInfo[attr] = omdbData[attr]

        for review in reviews:
            avgS += review[2]
            c += 1
        avgS = avgS / c
        avgS = round(avgS,1)

        finalRes = {}
        finalRes['title'] = movieInfo['Title']
        finalRes['year'] = movieInfo['Year']
        finalRes['imdb_id'] = movieInfo['imdbID']
        finalRes['director'] = movieInfo['Director']
        finalRes['actors'] = movieInfo['Actors']
        finalRes['imdb_rating'] = movieInfo['imdbRating']
        finalRes['review_count'] = len(reviews)
        finalRes['average_score'] = avgS
        '''
        finalRes = {
            'title': movieInfo['Title'],
            'year': movieInfo['Year'],
            'imdb_id': movieInfo['imdbID'],
            'director': movieInfo['Director'],
            'actors': movieInfo['Actors'],
            'imdb_rating': movieInfo['imdbRating'],
            'review_count': len(reviews),
            'average_score': avgS

        }
        '''
        return jsonify(finalRes)

    except:
        abort(404)

@app.errorhandler(404)
def not_found(error):
    return make_response(render_template('error.html'), 404)