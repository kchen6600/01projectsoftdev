from flask import Flask, render_template
import sqlite3
from utils import dbLibrary

story_app = Flask(__name__)

#Creating the database 
openDB("data/stories.db")
cursor = createCursor(db)
createTable(mainStories,['title','storyID', 'timeLast', 'lastAdd','storyFile','lastEditor'] ,['TEXT', 'INTEGER PRIMARY KEY AUTOINCREMENT','datetime2', 'TEXT', 'TEXT', 'TEXT'])

createTable (userStories, ['username', 'storyIDs' , 'myAddition'], ['TEXT' , 'TEXT' , 'TEXT'])

            
@story_app.route("/")
def login():
    return render_template("login.html")

@story_app.route("/home",methods = ['POST','GET'])
def homepage():
    return render_template("base.html")

@story_app.route("/create")
def create_story():
    return render_template("create.html")

if __name__ == "__main__":
    story_app.run(debug=True)
