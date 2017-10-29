from flask import Flask, render_template, redirect, url_for,request, session, flash
import sqlite3
from utils import dbLibrary
import hashlib, uuid, os
from datetime import datetime




def hash_password(password):
    key = uuid.uuid4().hex
    return hashlib.sha256(key.encode() + password.encode()).hexdigest() + ':' + key

def check_password(hashed_password, user_password):
    password,key = hashed_password.split(":")
    return password == hashlib.sha256(key.encode() + user_password.encode()).hexdigest()


story_app = Flask(__name__)
story_app.secret_key = os.urandom(32)


#------------------------LOGIN----------------------------------
@story_app.route("/")
def root():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@story_app.route("/login", methods = ['POST' , 'GET'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template("login.html")

@story_app.route("/authenticate",methods = ['POST','GET'])
def authenticate():
    dbStories = dbLibrary.openDb("data/stories.db")
    cursor = dbLibrary.createCursor(dbStories)
    input_username = request.form['username']
    input_password = request.form['password']

    if input_username=='' or input_password=='' :
        flash("Please Fill In All Fields")
        return redirect(url_for('login'))

    hashed_passCursor = cursor.execute("SELECT password FROM accounts WHERE username = '" + input_username + "'")
    numPasses = 0 #should end up being 1 if all fields were filled

    for item in hashed_passCursor:
        numPasses += 1
        hashed_pass = item[0]
        print item[0]

    dbLibrary.closeFile(dbStories)

    if  numPasses == 0:
        flash ("User doesn't exist")
        return redirect(url_for('login'))

    elif check_password(hashed_pass, input_password):
        flash("Login Successful")
        session["username"] = input_username;#in order to keep track of user
        return redirect(url_for('home'))

    else:
        flash("Invalid Login Information")
        return redirect(url_for('login'))
    
@story_app.route("/home",methods = ['POST','GET'])
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("base.html",username = session['username'])

#-------------------------------------------------------------------



#---------------CREATING AN ACCOUNT----------------------------------
@story_app.route("/account", methods = ['POST' , 'GET'])
def account():
    return render_template("account.html")

@story_app.route("/accountSubmit", methods = ['POST' , 'GET'])
def accountSubmit():
    dbStories = dbLibrary.openDb("data/stories.db")
    cursor = dbLibrary.createCursor(dbStories)
    #print request.form
    username = request.form['username']
    password = request.form['password']

    if username == '' or password == '':
        dbLibrary.closeFile(dbStories)
        flash("Please Fill In All Fields")
        return redirect(url_for('account'))

    elif len(password)< 6:
        dbLibrary.closeFile(dbStories)
        flash("Password must have at least 6 characters")
        return redirect(url_for('account'))

    elif (' ' in username or ' ' in password):
        dbLibrary.closeFile(dbStories)
        flash("Username and Password cannot contain the space character")
        return redirect(url_for('account'))

    password = hash_password(password)
    sameUser = cursor.execute("SELECT username FROM accounts WHERE username = '" + username +"'")

    counter = 0 #should remain 0 if valid username since username needs to be unique
    for item in sameUser:
        counter += 1

    if counter == 0:
        dbLibrary.insertRow('accounts',['username', 'password'],[username, password],cursor)
        flash("Account Successfully Created")
        dbLibrary.commit(dbStories)
        dbLibrary.closeFile(dbStories)
        return redirect(url_for('login'))

    else:
        flash("Invalid: Username taken")
        dbLibrary.commit(dbStories)
        dbLibrary.closeFile(dbStories)
        return redirect(url_for('account'))

#-----------------------------------------------------------



#---------------CREATING STORY----------------------------

@story_app.route("/create")
def create_story():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("create.html")

@story_app.route("/new_submit", methods = ['POST'])
def new_submit():

    dbStories = dbLibrary.openDb("data/stories.db")
    cursor = dbLibrary.createCursor(dbStories)

    title = request.form['title']
    body = request.form['body']

    #Creating story file:
    story_obj = open('stories/' + title + '.txt', "w+")
    story_obj.write(body)
    story_obj.close()

    datetime2 = str(datetime.now())[0:-7]#date and time (w/o milliseconds)
    last_editor = session["username"]
    dbLibrary.insertRow('mainStories', ['title', 'timeLast', 'lastAdd', 'storyFile', 'lastEditor'], [title, datetime2, body, title + ".txt", last_editor], cursor)


    #Fix the table to add the story id too
    command = "SELECT * FROM mainStories WHERE title = '" + title + "'AND timeLast = '" + datetime2 + "';"
    #There should only be one row from this command
    for fieldrow in cursor.execute(command):
        storyID = fieldrow[1]

    dbLibrary.insertRow('userStories', ['username', 'storyIDs','myAddition'], [last_editor, storyID, body], cursor)

    dbLibrary.commit(dbStories)
    dbLibrary.closeFile(dbStories)

    return redirect(url_for('home'))

#---------------------------------------------------------

#---------------VIEWING STORY----------------------------

@story_app.route("/view")
def view_stories():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    dbStories = dbLibrary.openDb("data/stories.db")
    cursor = dbLibrary.createCursor(dbStories)

    stories_raw = dbLibrary.display('mainStories', ['title', 'storyID', 'timeLast', 'storyFile', 'lastEditor'], cursor)
   

    entries_list = stories_raw.split("$|$\n")#list of entries
    header = entries_list.pop(0)

    print "RAW"
    print entries_list

    split_entries_list = [line.split("| ") for line in entries_list] #list of lists of entries
    split_entries_list.pop(-1)#delete empty field created by split

    your_split_entries = []

    #users_raw = dbLibrary.display('userStories', ['title', 'storyIDs', 'myAddition'], cursor)
    command = "SELECT username, storyIDs, myAddition FROM userStories"
    cursor.execute(command)

    print "FETCHALL"
    userdata = cursor.fetchall()
    print userdata

    for story in userdata:#maybe we can do this in not O(n^2)
        if story[0] == session["username"]:
            print story[0]
            print story[1]
            for entry in split_entries_list:
                if entry[1] == story[1]:
                    print entry
                    your_split_entries.append(entry)#append only your additions


    print your_split_entries


    dbLibrary.commit(dbStories)
    dbLibrary.closeFile(dbStories)

    return render_template("view.html", username = session['username'],story_list = your_split_entries)


@story_app.route("/view/<id>")#create route to view each story
def view_single(id):
    dbStories = dbLibrary.openDb("data/stories.db")
    cursor = dbLibrary.createCursor(dbStories)

    command = "SELECT storyFile FROM mainStories WHERE storyID =" + str(id) + ";"#match story IDs
    cursor.execute(command)

    filename = cursor.fetchall()[0][0]#extract from tuple from list
    print "FILENAME"
    print filename
    readobj = open("stories/" + filename, "r")
    body = readobj.read()
    print body

    dbLibrary.commit(dbStories)
    dbLibrary.closeFile(dbStories)

    return render_template("view_single.html", title = filename[:-4], body = body)


#-------------------------------------------------------
@story_app.route("/edit")
def edit_stories():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    dbStories = dbLibrary.openDb("data/stories.db")
    cursor = dbLibrary.createCursor(dbStories)

    stories_raw = dbLibrary.display('mainStories', ['title', 'storyID', 'timeLast', 'storyFile', 'lastEditor'], cursor)

    print stories_raw

    entries_list = stories_raw.split("$|$\n")#list of entries
    header = entries_list.pop(0)

    print "RAW"
    print entries_list

    split_entries_list = [line.split("| ") for line in entries_list] #list of lists of entries
    split_entries_list.pop(-1)#delete empty field created by split

    available_split_entries = []

    command = "SELECT username, storyIDs, myAddition FROM userStories"
    cursor.execute(command)

    print "FETCHALL"
    userdata = cursor.fetchall()
    print userdata

    ids_edited = []
    for story in userdata:
        if story[0] == session["username"]:
            print story[0]
            print story[1]
            ids_edited.append(story[1])
            print "IDS EDITED"
            print ids_edited

    for story in userdata:#maybe we can do this in not O(n^2)
        if story[0] != session["username"]:
            #print story[0]
            #print story[1]
            for entry in split_entries_list:
                if entry[1] not in ids_edited and entry not in available_split_entries:
                    #print entry
                    available_split_entries.append(entry)#append only your additions

    print available_split_entries

    dbLibrary.commit(dbStories)
    dbLibrary.closeFile(dbStories)

    return render_template("edit.html", username = session['username'], story_list = available_split_entries)

@story_app.route("/edit/<id>")#create route to view each story
def edit_single(id):
    dbStories = dbLibrary.openDb("data/stories.db")
    cursor = dbLibrary.createCursor(dbStories)

    command = "SELECT * FROM mainStories WHERE storyID =" + str(id) + ";"#match story IDs

    #There should only be one row with a given storyID
    for row in cursor.execute(command):
        title = row[0]
        lastaddition = row[3]

    dbLibrary.commit(dbStories)
    dbLibrary.closeFile(dbStories)

    return render_template("edit_single.html", id = id, title = title, lastaddition = lastaddition)

@story_app.route("/edit_submit", methods = ['POST'])
def edit_submit():

    dbStories = dbLibrary.openDb("data/stories.db")
    cursor = dbLibrary.createCursor(dbStories)

    title = request.form['title']
    id = request.form['id']
    newAdd = request.form['addition']
    last_editor = session["username"]

    #Updating story file:
    story_obj = open('stories/' + title + '.txt', "a+")
    story_obj.write(newAdd)
    story_obj.close()

    #Updating the last addition and editor
    command = "UPDATE mainStories SET lastAdd = '" + newAdd + "' WHERE storyID =" + id + ";" #update lastAdd
    cursor.execute(command)
    command = "UPDATE mainStories SET lastEditor = '" + last_editor + "' WHERE storyID =" + id + ";" #update lastAdd
    cursor.execute(command)

    #Update the table of all the user additions
    dbLibrary.insertRow('userStories', ['username', 'storyIDs','myAddition'], [last_editor, id, newAdd], cursor)

    dbLibrary.commit(dbStories)
    dbLibrary.closeFile(dbStories)

    return redirect(url_for('home'))


@story_app.route('/logout',methods = ['GET'])
def logout():
    username = session.pop('username')
    msg = "Successfully logged out " + username
    flash(msg)
    return redirect(url_for('login'))

if __name__ == "__main__":
    story_app.run(debug=True)
