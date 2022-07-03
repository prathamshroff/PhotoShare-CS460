DROP DATABASE IF EXISTS photoshare;
CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE Users (
    user_id INT NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    firstName VARCHAR(255),
    lastName VARCHAR(255),
    hometown VARCHAR(255),
    gender ENUM('M', 'F'),
    dateOfBirth DATE
);

CREATE TABLE Friends (
 user_id INT NOT NULL,
 friend_id INT NOT NULL,
 PRIMARY KEY  (user_id, friend_id),
 FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
 FOREIGN KEY (friend_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Albums (
  album_id INT NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  date_created DATETIME NOT NULL DEFAULT NOW(),
  user_id INT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  UNIQUE KEY albumid (user_id, name)
);


CREATE TABLE Pictures (
  imgdata longblob,
  user_id INT NOT NULL,
  caption VARCHAR(255) NOT NULL,
  picture_id INT NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY,
  album_id INT,
  INDEX upid_idx (user_id),
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (album_id) REFERENCES Albums(album_id) ON DELETE CASCADE
);

CREATE TABLE Tags (
  tagname VARCHAR(255) NOT NULL UNIQUE PRIMARY KEY,
  picture_id INT NOT NULL,
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Comments (
  comment_id INT NOT NULL AUTO_INCREMENT UNIQUE PRIMARY KEY,
  text VARCHAR(255) NOT NULL,
  user_id INT DEFAULT '0',
  commentdate DATETIME NOT NULL DEFAULT NOW(),
  picture_id INT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Likes (
  picture_id INT NOT NULL,
  user_id INT NOT NULL DEFAULT '0',
  PRIMARY KEY (picture_id, user_id),
  FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
