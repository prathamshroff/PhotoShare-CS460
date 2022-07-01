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

from heapq import nlargest
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
import datetime

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'LCAWe!come2'
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
	pwd = str(data[0][0])
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

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
			#return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file
			return flask.redirect(flask.url_for('home'))
	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"



@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html',supress=True)

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstName = request.form.get('firstName')
		lastName = request.form.get('lastName')
		dob = request.form.get('dob')
		hometown = request.form.get('hometown')
		gender = request.form.get('gender')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, firstName, lastName, password, dob, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, firstName, lastName, password, dob, hometown, gender)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='account created')
	else:
		print("email already in use")
		return flask.redirect(flask.url_for('register'))

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, album_name, doc, user_id FROM Have_Album WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() 

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT picture_id, user_id, album_id, imgdata, caption FROM Contain_picture WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(picture_id, album_id, imgdata, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	try: return cursor.fetchone()[0]
	except TypeError: return cursor.fetchone()

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
	
def getUsersNameFromID(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT firstName FROM Users WHERE user_id = '{0}'".format(uid))
	firstName = cursor.fetchone()[0]
	cursor.execute("SELECT lastName FROM Users WHERE user_id = '{0}'".format(uid))
	lastName = cursor.fetchone()[0]
	return firstName+" "+lastName
#end login code
	

#album_id,album_name,doc,user_id
def getAlbumInfoFromAID(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id,album_name,doc,user_id FROM Have_Album WHERE album_id = '{0}'".format(aid))
	return cursor.fetchone()

def getUsersFriends(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id2 FROM Befriend WHERE user_id1 = '{0}'".format(uid))
	return cursor.fetchall()

@app.route('/profile',methods = ['GET','POST'])
@flask_login.login_required
def profile(): #profile
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album_rename = request.form.get('album_rename')
		aid = request.form.get('album_id')
		cursor=conn.cursor()
		if album_rename != None:
			#change the album's name
			cursor.execute("UPDATE Have_Album SET album_name = '{0}' WHERE album_id='{1}'".format(album_rename,aid))
			conn.commit()
			return render_template('hello.html', name=getUsersNameFromID(uid), message="here's your profile", albums = getUsersAlbums(uid), base64=base64)
		albumName = getAlbumInfoFromAID(aid)[1]
		cursor.execute("DELETE FROM Have_Album WHERE album_id='{0}'".format(aid))
		conn.commit()
		return render_template('hello.html',name=flask_login.current_user.id, message='your album %s has been deleted!'%albumName,base64=base64)
	else:
		albums = getUsersAlbums(uid)
		return render_template('hello.html', name=getUsersNameFromID(uid), message="here's your profile", albums = albums, base64=base64)

#begin album creating code
@app.route('/create',methods = ['Get','POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		albumName = request.form.get('albumName')
		dateNow = datetime.date.today()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Have_Album (album_name, doc, user_id) VALUES (%s, %s,%s)''', (albumName,dateNow,uid))
		conn.commit()
		return render_template('hello.html',name=flask_login.current_user.id, message='your album %s has been created'%albumName,base64=base64)
	else:
		return render_template('create.html')
#end album creating code


#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		tags = request.form.get('tags')
		album_name = request.form.get('albumName')
		
		photo_data =imgfile.read()
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		
		if cursor.execute("SELECT album_id FROM Have_Album WHERE album_name = '{0}' AND user_id = '{1}'".format(album_name,uid)):
			aid = cursor.fetchone()[0]
			cursor.execute('''INSERT INTO Contain_picture (user_id, album_id,imgdata, caption) VALUES (%s,%s, %s,%s)''', (uid,aid,photo_data,caption))
			conn.commit()
			
			cursor.execute('''SELECT LAST_INSERT_ID()''')
			pid = int(cursor.fetchone()[0])
			#duplicate tags ignored
			tag_list = list(set(tags.split()))
			for tag in tag_list:
				cursor.execute('''INSERT INTO Hashtag (picture_id, tag_description) VALUES (%s,%s)''',(pid,tag))
				conn.commit()
			
			cursor.execute("SELECT imgdata FROM Contain_picture WHERE picture_id = '{0}'".format(pid))
			return render_template('hello.html', name=flask_login.current_user.id, message='your photo has been uploaded to %s'%album_name, photo=cursor.fetchone()[0], base64=base64)
		return render_template('upload.html', message = 'Album does not exist')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code

#begin befriend code
@app.route('/add-friend',methods = ['Get','POST'])
@flask_login.login_required
def befriend():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		friendEmail = request.form.get('friendEmail')
		friend_uid = getUserIdFromEmail(friendEmail)
		
		cursor = conn.cursor()
		if cursor.execute('''INSERT IGNORE INTO Befriend(user_id1, user_id2) VALUES (%s, %s)''', (uid,friend_uid)):
			conn.commit()
			cursor.execute('''INSERT IGNORE INTO Befriend(user_id1, user_id2) VALUES (%s, %s)''', (friend_uid,uid))
			conn.commit()
			return render_template('hello.html',name=flask_login.current_user.id, message='%s has been added as your friend'%getUsersNameFromID(friend_uid), base64=base64)
		return render_template('add-friend.html',message="Friend already added or does not exist")
	else:
		return render_template('add-friend.html')
#end befriend code
	

#begin friendCircle code
@app.route('/friendCircle',methods = ['Get','Post'])
@flask_login.login_required
def friendCircle():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	message = None
	cursor = conn.cursor()
	if request.method=='POST':
		fuid = request.form.get('friend_id')
		pid = request.form.get('picture_id')
		
		if fuid != None: #unfriend
			friendName = getUsersNameFromID(uid)
			cursor.execute("DELETE FROM Befriend WHERE (user_id1='{0}' AND user_id2='{1}') OR (user_id1='{1}' AND user_id2='{0}')".format(uid,fuid))
			conn.commit()
			message = "You have unfriended %s"%friendName
		
		elif pid!=None: #like/comment
			comment = request.form.get('comment')
			if (comment!=None): #this is a comment
				cursor.execute("INSERT INTO Leave_comment(comment_date,comment_txt,user_id,picture_id) VALUES (%s,%s,%s,%s)",(datetime.date.today(),comment,uid,pid))
				conn.commit()
				message = "Comment published"
			elif (cursor.execute("INSERT IGNORE INTO Like_pic (user_id, picture_id) VALUES (%s,%s)",(uid,pid))):
				conn.commit()
			else: message = "You have already liked the picture"
	
	fuids = getUsersFriends(uid)
	if not fuids: #no friends
		return render_template('friendCircle.html', name=getUsersNameFromID(uid), base64=base64)
	
	format_str = ','.join(['%s']*len(fuids))
	cursor.execute("SELECT user_id, email, firstName, lastName FROM Users WHERE user_id IN (%s)"%format_str,fuids)
	print(type(fuids[0][0]))
	print(fuids)
	
	
	
	friends = cursor.fetchall()
	recfriends = friendrecommend(uid)
	print("recphotos")
	recphotos = photorec(uid)
	
	pid_list = [x[0] for x in recphotos]
	tag_list = getTagsOfPhotos(pid_list)
	like_list = getLikePeopleOfPhotos(pid_list)
	liken_list = [len(x) for x in like_list]
	comment_list = getCommentsOfPhotos(pid_list)
	
	return render_template('friendCircle.html', message=message, name=getUsersNameFromID(uid), friends=friends, recfriends = recfriends, recphotos=recphotos, tags=tag_list, likes = like_list, likens = liken_list, comments = comment_list, base64=base64)

#recommend friend to user
def friendrecommend(uid):
	cursor = conn.cursor()
	
	fuids = getUsersFriends(uid)
	dict_friends = {}
	for fuid in fuids:
		ffuids=getUsersFriends(fuid[0])
		for ffuid in ffuids:
			if ffuid[0]==uid:
				continue
			if (ffuid in dict_friends):
				dict_friends[ffuid] +=1
			else:
				dict_friends[ffuid] = 1
	#top_friends = nlargest(5,dict_friends,key=dict_friends.get)
	top_friends = tuple(sorted(dict_friends, key=dict_friends.get,reverse=True))

	if not top_friends: #empty list, no rec
		return ()
	
	format_str = ','.join(['%s']*len(top_friends))
	cursor.execute("SELECT user_id, email FROM Users WHERE user_id IN (%s)"%format_str,top_friends)
	top_friends = [3,31]
	#cursor.execute("SELECT user_id,email FROM Users WHERE user_id IN (%s,%s)"%(str(3),str(31)))
	
	#print(fuids)
	#cursor.execute("SELECT user_id, email, firstName, lastName FROM Users WHERE user_id IN (%s)"%format_str,fuids)
	
	
	#cursor.execute("SELECT user_id, email FROM Users WHERE user_id IN (3,31)")
	
	recfriends=cursor.fetchall()
	return recfriends

def photorec(uid):
	"""You-may-also-like functionality
	take five most commonly used tags
	search thru all photos for these 5 tags
	order by higher number of satisfactory
	between two that is a tie: the one with fewer tags is preferred"""
	cursor=conn.cursor()
	
	#5mostcommonlyusedtags
	cursor.execute("SELECT tag_description FROM Hashtag, Contain_picture WHERE Hashtag.picture_id=Contain_picture.picture_id AND Contain_picture.user_id='{0}' GROUP BY tag_description ORDER BY COUNT(*) DESC LIMIT 5".format(uid))
	top5tags_user = cursor.fetchall()
	
	top5tags_user = [tag[0] for tag in top5tags_user]
	top5tags = ",".join([str(i) for i in top5tags_user])
	
	#search thru all photos for top5tags
	format_str = ','.join(['%s']*len(top5tags_user))
	#dictionary: {picture_id: number of tags in top5tag}
	cursor.execute("SELECT picture_id, user_id, album_id, imgdata, caption FROM Contain_picture WHERE user_id<>'{0}'".format(uid))
	allPhotosNotMine = cursor.fetchall()
	list_photos = []
	for photo in allPhotosNotMine:
		#get num of tags in top5tag
		cursor.execute("SELECT Count(*) FROM Hashtag WHERE picture_id='{0}' AND tag_description IN ('{1}')".format(photo[0], top5tags))
		n_tags_in_top5tag = cursor.fetchone()[0]
		if n_tags_in_top5tag == 0:
			continue
		cursor.execute("SELECT Count(*) FROM Hashtag WHERE picture_id=%s "%photo[0])
		n_tags_all = cursor.fetchone()[0]
		list_photos.append((photo,n_tags_in_top5tag,n_tags_all))
	sorted_list_photos = sorted(list_photos,key=lambda x:(-x[1],x[2]))
	recphotos = [x[0] for x in sorted_list_photos]
	return recphotos
#end friendCircle code

	
#other user album photos page
def getTagsOfPhotos(pid_list):
	cursor = conn.cursor()
	tag_list = []
	for pid in pid_list:
		cursor.execute("SELECT tag_description FROM Hashtag WHERE picture_id = '{0}'".format(pid))
		tag_list.append(cursor.fetchall())
	return tag_list

def getLikePeopleOfPhotos(pid_list):
	cursor = conn.cursor()
	like_list = []
	for pid in pid_list:
		cursor.execute("SELECT email from Users, Like_pic WHERE picture_id = '{0}' AND Users.user_id = Like_pic.user_id".format(pid))
		like_list.append(cursor.fetchall())
	return like_list

def getCommentsOfPhotos(pid_list):
	cursor = conn.cursor()
	comment_list = []
	for pid in pid_list:
		cursor.execute("SELECT comment_id, comment_date, comment_txt, email FROM Leave_comment, Users WHERE picture_id = '{0}' AND Users.user_id = Leave_comment.user_id".format(pid))
		comment_list.append(cursor.fetchall())
	return comment_list

def getOwnershipOfPhotos(pid_list,uid):
	cursor = conn.cursor()
	my_list = []
	for pid in pid_list:
		cursor.execute("SELECT user_id FROM Contain_picture WHERE picture_id = '{0}'".format(pid))
		owner = cursor.fetchone()[0]
		if int(owner)==int(uid):
			my_list.append(True)
		else:
			my_list.append(False)
	return my_list

@app.route('/user<uid>/album<aid>',methods=['GET','POST'])
def photos_for_user_album(uid,aid):
	"""Page displays caption, tags<href>,
	the image, like functionality, comment functionality"""
	message = None
	my=None
	cursor = conn.cursor()
	try:
		poster_id = getUserIdFromEmail(flask_login.current_user.id)
	except AttributeError:
		cursor.execute("INSERT INTO Users (email, firstName, lastName, password, dob) VALUES ('unreg_visitor@bu.edu','visitor','visitor','visitor','2000-01-01')")
		conn.commit()
		cursor.execute("SELECT LAST_INSERT_ID()")
		poster_id = cursor.fetchone()[0]
	if int(uid)==poster_id:
		my=1
		
	if request.method == 'POST':
		pid = request.form.get("picture_id")
		comment = request.form.get('comment')
		re_caption = request.form.get('edit_caption')
		re_tags = request.form.get('edit_tags')
		delete = request.form.get('delete')
		
		if (comment!=None): #this is a comment
			cursor.execute("INSERT INTO Leave_comment(comment_date,comment_txt,user_id,picture_id) VALUES (%s,%s,%s,%s)",(datetime.date.today(),comment,poster_id,pid))
			conn.commit()
			message = "Comment published"
			
		elif(re_caption!=None): #this is a caption modification
			cursor.execute("UPDATE Contain_picture SET caption = '{0}' WHERE picture_id='{1}'".format(re_caption,pid))
			conn.commit()
			message="Caption modified"
		
		elif(re_tags!=None): #this is a tag modification
			#delete all old tags
			cursor.execute("DELETE FROM Hashtag WHERE picture_id = '{0}'".format(pid))
			conn.commit()
			#insert new ones
			new_tags_list = re_tags.split()
			for new_tag in new_tags_list:
				if(cursor.execute("INSERT INTO Hashtag (picture_id, tag_description) VALUES (%s,%s)",(pid,new_tag))):
					conn.commit()
			message="Tags modified"
		
		elif(delete): #delete pic
			cursor.execute("DELETE FROM Contain_picture WHERE picture_id = %s",pid)
			conn.commit()
			message = "You have deleted a picture"
			
		elif (cursor.execute("INSERT IGNORE INTO Like_pic (user_id, picture_id) VALUES (%s,%s)",(poster_id,pid))):
			conn.commit()
		else: message = "You have already liked the picture"
	
	#user_id,email
	cursor.execute("SELECT user_id, email FROM Users WHERE user_id = '{0}'".format(uid))
	uinfo = cursor.fetchone()
	#album_id,album_name,doc,user_id
	ainfo = getAlbumInfoFromAID(aid) 
	#(picture_id, user_id, album_id, imgdata, caption)
	cursor.execute("SELECT picture_id, user_id, album_id, imgdata, caption FROM Contain_picture WHERE user_id = '{0}' AND album_id = '{1}'".format(uid,aid))
	photos = cursor.fetchall()
	pid_list = [x[0] for x in photos]
	# [tuple of tags of p1, tuple of tags of p2,...]
	# like list
	tag_list = getTagsOfPhotos(pid_list)
	like_list = getLikePeopleOfPhotos(pid_list)
	comment_list = getCommentsOfPhotos(pid_list)
	liken_list = [len(x) for x in like_list]
		
	return render_template('user_photos.html', message = message, user=uinfo, album=ainfo, photos=photos, tags = tag_list, likens = liken_list, likes = like_list, comments = comment_list, my=my,base64=base64)


#other user profile page
@app.route('/user<uid>',methods=['GET','POST'])
def albums_for_user(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, email FROM Users WHERE user_id = '{0}'".format(uid))
	uinfo = cursor.fetchone()
	#album: album_id, album_name, doc, user_id 
	return render_template('user_albums.html', user=uinfo, albums = getUsersAlbums(uid), base64=base64)


#(picture_id, user_id, album_id, imgdata, caption)
def getPhotosFromTag(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT picture_id, user_id, album_id, imgdata, caption FROM Contain_picture WHERE picture_id IN (SELECT picture_id FROM Hashtag WHERE tag_description='{0}')".format(tag))
	return cursor.fetchall()

#page that displays all photos with that tag
@app.route('/tag-<tag>',methods=['GET','POST'])
def photos_of_tag(tag):
	message =  None
	cursor = conn.cursor()
	my=False
	try:
		poster_id = getUserIdFromEmail(flask_login.current_user.id)
	except AttributeError:
		cursor.execute("INSERT INTO Users (email, firstName, lastName, password, dob) VALUES ('unreg_visitor@bu.edu','visitor','visitor','visitor','2000-01-01')")
		conn.commit()
		cursor.execute("SELECT LAST_INSERT_ID()")
		poster_id = cursor.fetchone()[0]

	if request.method == 'POST':
		pid = request.form.get("picture_id")
		if (pid != None): #it was a like/comment
			comment = request.form.get('comment')
			if (comment!=None): #this is a comment
				cursor.execute("INSERT INTO Leave_comment(comment_date,comment_txt,user_id,picture_id) VALUES (%s,%s,%s,%s)",(datetime.date.today(),comment,poster_id,pid))
				conn.commit()
				message = "Comment published"
			elif (cursor.execute("INSERT IGNORE INTO Like_pic (user_id, picture_id) VALUES (%s,%s)",(poster_id,pid))): 
				conn.commit()
			else: message = "You have already liked the picture all"
		else: 
			my = int(request.form.get('switch'))
		
	photos = getPhotosFromTag(tag) #(picture_id, user_id, album_id, imgdata, caption)
	pid_list = [x[0] for x in photos]
	tag_list = getTagsOfPhotos(pid_list)
	like_list = getLikePeopleOfPhotos(pid_list)
	liken_list = [len(x) for x in like_list]
	comment_list = getCommentsOfPhotos(pid_list)
	my_list = getOwnershipOfPhotos(pid_list,poster_id) #boolean list, true means this pic is mine
	
	return render_template('tag.html',message = message, tag=tag, photos=photos, tags=tag_list, likes=like_list, likens = liken_list, comments = comment_list, mys = my_list, my=my, base64=base64)

#returns user_id by desc contribution scores
def Users_by_DESC_contribution():
	"""contribution score = #comments + #photos"""
	cursor = conn.cursor()
	if (cursor.execute("SELECT Users.user_id, Users.email FROM Users WHERE Users.email <> %s ORDER BY (SELECT COUNT(*) FROM Leave_comment WHERE Leave_comment.user_id = Users.user_id) + (SELECT COUNT(*) FROM Contain_picture WHERE Contain_picture.user_id = Users.user_id) DESC ",'unreg_visitor@bu.edu')):
		return cursor.fetchall()
	else: return ()

#lobby, for both visitors and users
def Top3Tags():
	cursor = conn.cursor()
	cursor.execute("""SELECT tag_description FROM Hashtag GROUP BY tag_description ORDER BY Count(*) DESC LIMIT 3""")
	top3tags = cursor.fetchall()
	return top3tags
	
@app.route('/lobby',methods=['GET'])
def lobby_get():
	"""
	Should display:
	- top 3 popular tags as urls
	- top 10 active users as urls to their profiles
	- photo search box
	- comment search box
	- url to home
	"""
	top3tags = Top3Tags()
	top10users = Users_by_DESC_contribution()[:10] #uid,email
	return render_template('lobby.html', top3tags=top3tags, users=top10users, base64=base64)

@app.route('/lobby',methods=['POST'])
def lobby_post():
	"""
	photo search or
	comment search 
	"""
	searchtags = request.form.get('searchtags')
	comment = request.form.get('comment_search')
	pid = request.form.get("picture_id")
	photo_list = None
	user_list = None
	commenter_list = None
	
	top3tags = Top3Tags()
	top10users = Users_by_DESC_contribution()[:10] #uid,email
	message = None
	
	cursor = conn.cursor()
			
	#new comment search
	if(comment!=None):
		cursor.execute("SELECT Leave_comment.user_id FROM Leave_comment WHERE comment_txt = '{0}' GROUP BY user_id ORDER BY Count(comment_id) DESC".format(comment) )
		user_list = cursor.fetchall()
		commenter_list = []
		for user in user_list:
			cursor.execute("SELECT user_id,email,firstName,lastName FROM Users WHERE user_id = '{0}'".format(user[0]))
			commenter_list.append(cursor.fetchone())
		return render_template('lobby.html', commenters = commenter_list, top3tags=top3tags, users=top10users, base64=base64)
	
	try:
		poster_id = getUserIdFromEmail(flask_login.current_user.id)
	except AttributeError:
		cursor.execute("INSERT INTO Users (email, firstName, lastName, password, dob) VALUES ('unreg_visitor@bu.edu','visitor','visitor','visitor','2000-01-01')")
		conn.commit()
		cursor.execute("SELECT LAST_INSERT_ID()")
		poster_id = cursor.fetchone()[0]
					
	#like/comment after photosearch
	if(pid!=None):
		comment = request.form.get('comment')
		if (comment!=None): #this is a comment
			cursor.execute("INSERT INTO Leave_comment(comment_date,comment_txt,user_id,picture_id) VALUES (%s,%s,%s,%s)",(datetime.date.today(),comment,poster_id,pid))
			conn.commit()
			message = "Comment published"
		elif (cursor.execute("INSERT IGNORE INTO Like_pic (user_id, picture_id) VALUES (%s,%s)",(poster_id,pid))):
			conn.commit()
		else: message = "You have already liked the picture"
	
	#photo search 
	photo_list = []
	searchtag_list = searchtags.split()
	for tag in searchtag_list:
		photos = getPhotosFromTag(tag)
		if not photos: #photos is empty, no photo with such tag
			continue
		photo_list += photos
	pid_list = [x[0] for x in photo_list]
	tag_list = getTagsOfPhotos(pid_list)
	like_list = getLikePeopleOfPhotos(pid_list)
	liken_list = [len(x) for x in like_list]
	comment_list = getCommentsOfPhotos(pid_list)
	my_list = getOwnershipOfPhotos(pid_list, poster_id)
	
	return render_template('lobby.html', message=message, searchtags=searchtags,photos = photo_list, tags = tag_list, likes = like_list, likens = liken_list, comments=comment_list, top3tags=top3tags, users=top10users, mys=my_list,base64=base64)
	


#default page
@app.route('/', methods=['GET','POST'])
def home():
	if request.method == 'POST':
		flask_login.logout_user()
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
	except AttributeError: #not logged in
		return render_template('hello.html', message=None,base64=base64)
	return render_template('hello.html', name=getUsersNameFromID(uid), message='welcome to Photoshare',base64=base64)


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.debug=True
	app.run(port=5000, debug=True)
	