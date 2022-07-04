######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'p301102s'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	def has_liked_photo(self, picture_id):
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT COUNT(*) FROM Likes WHERE user_id ='{0}' AND picture_id='{1}'".format(uid, picture_id))
		return cursor.fetchone()[0]
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/user_photos', methods=['GET', 'POST'])
@flask_login.login_required
def user_photos():
	user = request.args.get('user')
	uid = user[0]
	email=flask_login.current_user.id
	#if email != user[1]:
	#	print(email)
	#	return render_template('hello.html', name=flask_login.current_user.id, message='Email Mismatch Error #001')
	album = request.args.get('album')
	photos = getUsersPhotosByAlbum(album[0])
	#albums = getUsersAlbums(uid)
	photos = getUsersPhotosByUser(uid)
	tags = comments = likes = []
	if request.method == 'POST':
		return render_template('/user_photos.html', user=user, photos=photos, album=album)
	else:
		return render_template('/user_photos.html', user=user, photos=photos, album=album, tags=tags, likes=likes, comments=comments, base64=base64)

@app.route('/user_albums', methods=['GET', 'POST'])
@flask_login.login_required
def user_albums():
	email=flask_login.current_user.id
	uid = getUserIdFromEmail(flask_login.current_user.id)
	albums = getUsersAlbums(uid)
	if request.method == 'POST':
		albumName = request.form.get('albumName')
		action=request.form.get('action')
		action = str(action)
		if action == 'Add':
			for album in albums:
				if albumName == album[1]:
					return render_template('user_albums.html', name=flask_login.current_user.id, user = (uid, email), message="You cannot add album with same name again.", albums = albums)	
			# if albumName in albums: return render_template('user_albums.html', name=flask_login.current_user.id, message="You cannot add album with same name again.")
			cursor.execute("INSERT INTO Albums(name, user_id) VALUES ('{0}', '{1}')".format(albumName, uid))
			conn.commit()
			return render_template('user_albums.html', name=flask_login.current_user.id, user = (uid, email), message='New Album Added!', albums = getUsersAlbums(uid))
		if action == 'Remove':
			# edge case - trying to remove album not yet added
			#if albumName not in albums: return render_template('user_albums.html', name=flask_login.current_user.id, user = (uid, email), message="You cannot remove album you haven't added yet.")
			cursor.execute("DELETE FROM Albums WHERE user_id = '{0}' AND name = '{1}'".format(uid, albumName))
			conn.commit()
			return render_template('user_albums.html', name=flask_login.current_user.id, user = (uid, email), message='Album Removed!', albums = getUsersAlbums(uid))
	else:
		return render_template('user_albums.html', user = (uid, email), albums = albums)

@app.route('/view_myphotos', methods=['GET', 'POST'])
@flask_login.login_required
def view_myphotos():
	email=flask_login.current_user.id
	uid = getUserIdFromEmail(flask_login.current_user.id)
	photos = getUsersPhotosByUser(uid)
	return render_template('viewphotos.html', user = (uid, email), photos=photos, base64=base64)

@app.route('/viewphotos', methods=['GET', 'POST'])
def viewphotos():
	email=flask_login.current_user.id
	uid = getUserIdFromEmail(flask_login.current_user.id)
	'''
	try:
		tag_id=request.args.get('tag_id')
		photos = getUsersPhotosByTag(tag_id)
	except:
		photos = getAllPhotos() '''
	photos = getAllPhotos()
	tags = getAllTags()
	if request.method == 'POST':
		return render_template('viewphotos.html')
	else:
		return render_template('viewphotos.html', user = (uid, email), photos=photos, tags=tags, base64=base64)


# https://stackoverflow.com/questions/52665707/how-do-i-implement-a-like-button-function-to-posts-in-python-flask
@app.route('/like_action')
@flask_login.login_required
def like_action():
	email=flask_login.current_user.id
	uid = getUserIdFromEmail(flask_login.current_user.id)
	picture_id=request.args.get('picture_id')
	action=request.args.get('action')
	action = str(action)
	cursor = conn.cursor()
	if action == 'like':
		cursor.execute("INSERT INTO Likes(user_id, picture_id) VALUES('{0}','{1}')".format(uid, picture_id))
		conn.commit()
		return redirect(request.referrer)
	if action == 'unlike':
		cursor.execute("DELETE FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, picture_id))
		conn.commit()
		return redirect(request.referrer)
	if action == 'seelikes':
		cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT user_id FROM Likes WHERE picture_id = '{0}')".format(picture_id))
		users = cursor.fetchall()
		return render_template('userlist.html', users=users, count=len(users), message="Users who've liked")

@app.route('/top10')
def top10():
	cursor.execute("SELECT email, contributions FROM Users U, (SELECT user_id, count(*) AS contributions FROM ((SELECT user_id FROM Pictures) UNION ALL (SELECT C.user_id FROM Comments C WHERE C.picture_id NOT IN (SELECT P.picture_id FROM Pictures P WHERE P.user_id=C.user_id))) AS counted GROUP BY user_id LIMIT 10) as top10 WHERE U.user_id = top10.user_id ORDER BY contributions DESC")
	users = cursor.fetchall()
	return render_template('userlist.html', users=users, message='Top 10 in User Activity')

@app.route('/accountExists')
def accountExists():
	return render_template('accountExists.html')

@app.route('/delete_user', methods=['GET', 'POST'])
@flask_login.login_required
def delete_user():
	if request.method == 'POST':
		cursor = conn.cursor()
		uid = getUserIdFromEmail(flask_login.current_user.id)
		conf_email = request.form.get('conf_email')
		conf_id = getUserIdFromEmail(conf_email)

		if uid == conf_id:
			cursor.execute("DELETE FROM Users WHERE user_id = '{0}'".format(uid))
			conn.commit()
			return render_template('hello.html', message='Profile & Account Deleted!')
	#The method is GET so we return a HTML form to delete user.
	else:
		return render_template('delete_user.html')

@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
def friends():
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	currentFriendList = getUsersFriends(uid)
	
	if request.method == 'POST':
		friendEmail = request.form.get('friendEmail')
		friend_id = getUserIdFromEmail(friendEmail)

		# edge case - trying to add/remove yourself
		if uid == friend_id:
			return render_template('friends.html', name=flask_login.current_user.id, message="You cannot friend/unfriend yourself!")

		action=request.form.get('action')
		action = str(action)
		if action == 'Add':
			cursor.execute("INSERT INTO Friends(user_id, friend_id) VALUES ('{0}', '{1}')".format(uid, friend_id))
			cursor.execute("INSERT INTO Friends(friend_id, user_id) VALUES ('{0}', '{1}')".format(uid, friend_id))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='Friend Added!')

		elif action == 'Remove':
			# edge case - tryinhg to remove someone who is not yet friend
			if friend_id not in currentFriendList:
				return render_template('friends.html', name=flask_login.current_user.id, message="You cannot unfriend someone who is not your friend!")

			cursor.execute("DELETE FROM Friends WHERE user_id = '{0}' AND friend_id = '{1}'".format(uid, friend_id))
			cursor.execute("DELETE FROM Friends WHERE user_id = '{0}' AND friend_id = '{1}'".format(friend_id, uid))
			conn.commit()
			return render_template('hello.html', name=flask_login.current_user.id, message='Friend Removed!')
		else:
			return render_template('hello.html', name=flask_login.current_user.id, message='Error #001-action')

	else:
		return render_template('friends.html', currentFriendList = currentFriendList)

#Given routes and code below

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstName=request.form.get('firstName')
		lastName=request.form.get('lastName')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
		gender = str(gender)
		dateOfBirth = request.form.get('dateOfBirth')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, firstName, lastName, hometown, gender, dateOfBirth) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, firstName, lastName, hometown, gender, dateOfBirth)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('accountExists'))
		#return render_template('hello.html', message='Account exists. Login or create un')
		#return flask.redirect(flask.url_for('hello', message='Account exists.'))

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT friend_id FROM Friends WHERE user_id = '{0}')".format(uid))
	return cursor.fetchall()

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, name, date_created FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(album_id, name, date_created), ...]

#by users, not by albums
def getUsersPhotosByUser(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUsersPhotosByAlbum(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id = '{0}'".format(album_id))
	return cursor.fetchall()

def getUsersPhotosByTag(tag_id):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Pictures WHERE picture_id IN (SELECT DISTINCT picture_id FROM Tags WHERE tagname = '{0}')".format(tag_id))
	return cursor.fetchall()

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Pictures")
	return cursor.fetchall() 

def getAllTags():
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Tags")
	return cursor.fetchall()

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserPhotoID(photo_data):
	cursor = conn.cursor()
	cursor.execute('''SELECT picture_id FROM Pictures WHERE imgdata = %s''', (photo_data))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/modifyphoto', methods=['GET', 'POST'])
@flask_login.login_required
def modifyphoto():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		caption = request.form.get('caption')
		tags = request.form.get('tags')
		picture_id = request.form.get('photo id')

		if len(caption) > 0:
			cursor = conn.cursor()
			cursor.execute('''UPDATE Pictures SET caption = %s WHERE picture_id = %s''', (caption, picture_id))
			conn.commit()
		if len(tags) > 0:
			taglist = tags.split()
			cursor = conn.cursor()
			cursor.execute("DELETE FROM Tags WHERE picture_id = '{0}'".format(picture_id))
			for tagname in taglist:
				cursor.execute("INSERT INTO Tags(tagname, picture_id) VALUES ('{0}', '{1}')".format(tagname, picture_id))
			conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Possible modifications made!')
	else:
		return render_template('modifyphoto.html')

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()

		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s )''', (photo_data,uid,caption))
		conn.commit()
		picture_id = getUserPhotoID(photo_data)
		try:
			tags = request.form.get('tags')
			taglist = tags.split()
			cursor = conn.cursor()
			for tagname in taglist:
				cursor.execute("INSERT INTO Tags(tagname, picture_id) VALUES ('{0}', '{1}')".format(tagname, picture_id))
			conn.commit()
		except:
			return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', base64=base64)

		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=8910, debug=True)
