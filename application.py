import os
from flask import Flask, render_template, url_for, flash, redirect, request, session, make_response, abort, jsonify
from forms import RegistrationForm, LoginForm, MovieSearchForm, ReviewForm
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
import omdb
from accolades import *

#app configs for SQL, SQLAlchemy & Flask
app = Flask(__name__)
SECRET_KEY = '\x96^\xe7W\xd3#\xb8\x97\x98L\xd9\xb0\r\x83cD\x14\x87k\xfe\xefY\xff\x87'
app.config['SECRET_KEY'] = SECRET_KEY
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
Session(app)

#Ensure jsonify() does not sort order of keys in dictionary to give desired api output
app.config['JSON_SORT_KEYS'] = False

#omdb settings
API_KEY = '2c402f70'
omdb.set_default('apikey', API_KEY) #For retrival of info from omdb


#Routes

#Route for home & default page
@app.route("/", methods=['GET','POST'])
@app.route("/home", methods=['GET','POST'])
def home():
    searchresults = []

    #Ensures is_logged & current_user are in session
    if 'is_logged' not in session:
        session['is_logged'] = False
    if 'current_user' not in session:
        session['current_user'] = ""

    #Uses the Movie Search Form from forms.py
    form = MovieSearchForm()

    #Only display form if user is logged in
    if session['is_logged'] == True:

        #Display search results
        if (form.search.data != None):
            searchresults = []

            #Find results from movies in DB
            results = db.execute("SELECT * FROM movies WHERE title LIKE :src OR lowercase LIKE :src OR year LIKE :src OR imdbid LIKE :src;",{"src": "%"+form.search.data+"%"}).fetchall()
            for result in results:

                #Use imdbID to retrieve more information from omdb
                imdb_id = result[3]
                attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response"]

                #Retrieval from omdb
                omdbResults = omdb.request(i=imdb_id)
                omdbData = omdbResults.json()
                temp = {}

                #Attaches every attribute of movie from omdb into search result
                for attr in attrlist:
                    temp[attr] = omdbData[attr]

                #searchresults to be displayed by Jinjja in home.html
                searchresults.append(temp)

        #Redirect to home page & display search results
        return render_template('home.html', accolades=accolades ,is_logged=True, form=form,searchresults = searchresults)
    else:

        #Redirect user to home if user is NOT logged in but somehow manages to use the search bar
        #Prevent tampering from returning errors
        return render_template('home.html', accolades=accolades)

    return render_template('home.html', accolades=accolades,is_logged=True,form=form)

#Route for about page
@app.route("/about")
def about():
    return render_template('about.html', accolades=accolades)

#Route for register / sign up page
@app.route("/register", methods=['GET', 'POST'])
def register():

    #Define 2 checkers
    unok = True
    emok = True

    #Redirects user to home if they are logged in and navigate to the login page
    if session['is_logged']:
        return redirect(url_for('home'))

    #Ensure that user's username & email is unique
    usernames = db.execute("SELECT username FROM users").fetchall()
    emails = db.execute("SELECT email FROM users").fetchall()
    form = RegistrationForm()

    for username in usernames:
        if form.username.data == username[0]:
            unok = False
    for email in emails:
        if form.email.data == email[0]:
            emok = False

    #Allows user to create account if both username and email are unique
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

    #Return register / sign up page If Fields Do Not Satisfy Requirements
    return render_template('register.html', title='Register', form=form)

#Route for login
@app.route("/login", methods=['GET', 'POST'])
def login():

    #Ensures that session object is functional if new user directly goes to login page instead of home
    if 'is_logged' not in session:
        session['is_logged'] = False
    if 'current_user' not in session:
        session['current_user'] = ""
    loginok = False
    form = LoginForm()
    if form.validate_on_submit():

        #Check For Special Characters As Part Of Special Characters to prevent SQL hacking

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

        #Check If Username & Password Are Matching Pairs


        userinfo = db.execute("SELECT * FROM users WHERE (username = :un);",{"un": form.username.data}).fetchall()
        ''' userinfo Is A Row Of Data, userinfo[0][3] Is The Password Of User'''
        try:
            if form.password.data == userinfo[0][3]:
                session['current_user'] = form.username.data
                message = 'You have been logged in, ' + session['current_user'] + '!'

                flash(message, 'success')

                if form.remember.data:
                    session.permanent = True
                else:
                    session.permanent = False

                #Sets session is_logged to True which is used across all templates
                session['is_logged'] = True
                return redirect(url_for('home'))
            else:
                flash('Login Unsuccessful. Please check username and password and make sure that they are correct!', 'danger')
        except:
            flash('Login Unsuccessful. Please check username and password and make sure that they are correct!', 'danger')

    return render_template('login.html', title='Login', form=form)

#Route for logout
@app.route("/logout")
def logout():

    #Sets all session values to not logged in state
    session['is_logged'] = False
    session['current_user'] = ""
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

#Route for specific movies & information
@app.route("/movies/<imdb_id>", methods=['GET', 'POST'])
def movie(imdb_id):

    #Uses Review Form object from forms.py
    form = ReviewForm()

    #Update DB when new form is submitted
    if form.validate_on_submit():
        db.execute("INSERT INTO reviews (userid, imdbid, rating, content) VALUES (:un, :ii, :ra, :co);",{"un": session['current_user'], "ii": imdb_id, "ra": form.select.data, "co": form.content.data})
        db.commit()

        return(redirect(url_for('movie', imdb_id=imdb_id)))

    # Ensure that movie exists
    movie = db.execute("SELECT * FROM movies WHERE imdbid = :id", {'id': imdb_id}).fetchone()
    if movie == None:
        abort(404)
    else:

        #Retrieve additional data from omdb
        imdb_id = movie[3]
        attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response"]
        omdbResults = omdb.request(i=imdb_id)
        omdbData = omdbResults.json()
        temp = {}
        for attr in attrlist:
            temp[attr] = omdbData[attr]

        # Get all reviews
        revu = db.execute("SELECT * FROM reviews WHERE imdbid = :imdbid",{"imdbid": imdb_id}).fetchall()
        attrlist2 = ["Author", "MovieID", "Rating", "ReviewContent"]
        reviews = []
        temp2 = {}

        #Check if user has submitted a review
        userRev = False

        for i in range(len(revu)):
            temp2 = {}
            for j in range(len(revu[i])):
                temp2[attrlist2[j]] = revu[i][j]
            reviews.append(temp2)
            if temp2['Author'] == session['current_user']:
                userRev = True

        #Sets reviews to blank list, not None
        if revu == None:
            reviews = []

        #Get average score from Metascore & imdbRating
        try:
            avgR = ( float( temp['Metascore'] ) + float( temp['imdbRating'] ) * 10 ) / 2
        except:
            try:
                avgR = temp['imdbRating']
            except:
                avgR = temp['Metascore']

        return render_template("movie.html", movie=temp, reviews=reviews, avgR=avgR, form = form, userRev=userRev)

#Route for api
@app.route('/api/<imdb_id>', methods=["GET"])
def get_api(imdb_id):

    #try / except in case of miscellaneous errors
    try:

        #Get all movie information & reviews
        movie = db.execute("SELECT * FROM movies WHERE imdbid = :id", {"id": imdb_id}).fetchall()
        reviews = db.execute("SELECT * FROM reviews WHERE imdbid = :id", {"id": imdb_id}).fetchall()
        avgS = 0
        c = 0

        #Retrieve movie information from omdb
        imdb_id = movie[0][3]
        attrlist = ["Title", "Year", "Rated", "Released", "Runtime", "Genre", "Director", "Writer", "Actors", "Plot", "Language", "Country", "Awards", "Poster", "Metascore", "imdbRating", "imdbVotes", "imdbID", "Type", "DVD", "BoxOffice", "Production", "Website", "Response"]
        omdbResults = omdb.request(i=imdb_id)
        omdbData = omdbResults.json()
        movieInfo = {}
        for attr in attrlist:
            movieInfo[attr] = omdbData[attr]

        #Outputs average score
        for review in reviews:
            avgS += review[2]
            c += 1
            avgS = avgS / c
        #Round to 1 decimal place
        avgS = round(avgS,1)

        #Prepare results to be jsonified, ordered in terms of time added
        finalRes = {}
        finalRes['title'] = movieInfo['Title']
        finalRes['year'] = movieInfo['Year']
        finalRes['imdb_id'] = movieInfo['imdbID']
        finalRes['director'] = movieInfo['Director']
        finalRes['actors'] = movieInfo['Actors']
        finalRes['imdb_rating'] = movieInfo['imdbRating']
        finalRes['review_count'] = len(reviews)
        finalRes['average_score'] = avgS

        #Gives a jsonified output
        return jsonify(finalRes)

    except:
        abort(404)

#Return error.html in case of error 404
@app.errorhandler(404)
def not_found(error):
    return make_response(render_template('error.html'), 404)
