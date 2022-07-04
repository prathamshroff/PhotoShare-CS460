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
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

import mysql.connector

mydb = mysql.connector.connect(
    host="localhost", user ="root", password="p301102s"
)

mycursor = mydb.cursor()
mycursor.execute("use photoshare")
str = "INSERT INTO USERS Values (3011, 'pshroff@bu.edu', 'Ps@301102', 'Pratham', 'Shroff', 'Mumbai', 'M', '2002-11-30');"
mycursor.execute(str)
str2 = "select * from users;"
mycursor.execute(str2)
data = mycursor.fetchall()
print(data)


