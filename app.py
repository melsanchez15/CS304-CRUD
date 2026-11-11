from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

import secrets
import pymysql
import cs304dbi as dbi

# we need a secret_key to use flash() and sessions
app.secret_key = secrets.token_hex()

# configure DBI
dbi.conf('ms142_db')
staffid = 10090

# For CRUD and Ajax, use your personal db

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

@app.route('/')
def index():
    return render_template('base.html', page_title='Home Page')

#adds, add flash message and check if it would create duplicate tt
@app.route('/insert/', methods = ['POST', 'GET'])
def insert():
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    if request.method == 'POST':
        ttform = request.form.get('movie-tt')
        titleform = request.form.get('movie-title')
        releaseform = request.form.get('movie-release')

        #checks if any form values are empty, flashes message and redirects if it is
        if ttform == '' or titleform == '' or releaseform == '':
            flash('Form is incomplete!')
            return redirect(url_for('insert'))

        #checks if theres an existing tt value
        try:
            curs.execute('''INSERT INTO movie (tt, title, `release`, addedby) VALUES (%s, %s, %s, %s)''',[ttform, titleform, releaseform, staffid])
        except pymysql.err.IntegrityError as err:
            flash(f'There is an existing movie with that tt value of: {ttform}')
            return redirect(url_for('insert'))

        conn.commit()
        return redirect(url_for('update', movie_tt = ttform))
    return render_template('insert.html', page_title='Insert')

#updates, allows for movie to be deleted and checks if the tt value is changed to an already existing value will flash message
@app.route('/update/<movie_tt>', methods = ['POST','GET'])
def update(movie_tt):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)

    if request.method == 'POST':
        action = request.form.get('submit')

        #deletes
        if action == 'delete':
            curs.execute('''delete from movie where tt = %s''', [movie_tt])
            conn.commit()
            flash(f'{movie_tt} deleted!')
            return redirect(url_for('index'))
        
        #updates
        elif action == 'update':
            ttform = request.form.get('movie-tt')
            titleform = request.form.get('movie-title')
            releaseform = request.form.get('movie-release')
            directorform = request.form.get('movie-director')
            print('person is', person)
            if directorform in person:
                curs.execute('''select name from person where nm = %s''', directorform)
                dirname = curs.fetchone()
                print(dirname)
            else:
                variable = "none specified"
            addedform = request.form.get('movie-addedby')

            #since director id is int, if the value was left '' it was trying to put in a string, so makes sure if empty its stores as NONE
            if directorform == '':
                directorform = None
            
            #checks if any form values are empty, flashes message and redirects if it is
            if ttform == '' or titleform == '' or releaseform == '' or addedform == '':
                if ttform == '':
                    flash('Movie ID/TT missing')
                if titleform == '':
                    flash('Movie Title missing')
                if releaseform == '':
                    flash('Movie Release Year missing')
                if addedform == '':
                    flash('Movie Added By missing')
                return redirect(url_for('update', movie_tt = movie_tt))

            #checks if there is already an existing tt value, flashes message if there is
            curs.execute('''select * from movie where tt = %s AND tt != %s''', [ttform, movie_tt])
            movie_amounts = curs.fetchall()
            if len(movie_amounts) != 0:
                flash(f'There is an existing movie with that tt value of: {ttform}')
                return redirect(url_for('update', movie_tt = movie_tt))

            #flashes update message and should now update the db
            curs.execute('''
            update movie set tt = %s, title = %s, `release` = %s, director = %s, 
            addedby = %s where tt = %s''', 
            [ttform, titleform, releaseform, directorform, addedform, movie_tt])
            conn.commit()
            flash(f'{movie_tt} updated!')
            
    curs.execute('''select * from movie where tt = %s''', [movie_tt])
    movie = curs.fetchone()
    directorform = request.form.get('movie-director')
    curs.execute('''select name from person where nm = %s''', directorform)
    dirname = curs.fetchall()
    if dirname is None:
        dirname == 'None Specified'
        print(dirname)
    return render_template('update.html', movie = movie, dirname = dirname)

#select from dropdown of movies with missing values, redirects to update page
@app.route('/select/', methods = ['POST', 'GET'])
def select():
    if request.method == 'POST':
        ttform = request.form.get('movie-tt')
        return redirect(url_for('update', movie_tt = ttform))
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from movie where `release` IS NULL OR director IS NULL''')
    movies = curs.fetchall()
    return render_template('select.html', movies = movies)

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    app.debug = True
    app.run('0.0.0.0',port)
