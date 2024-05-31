from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_socketio import SocketIO, send, emit
from datetime import datetime, timedelta
import json
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
socketio = SocketIO(app)

QUESTION_MASTER = []

with open('questions.json', 'r') as file:
    QUESTION_MASTER = json.load(file)


userlevel = dict()
userquestions = dict()
userstarttime = dict()
userprogress = dict()


def init_db():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserScore (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            score INTEGER NOT NULL,
            num_questions INTEGER NOT NULL,
            level TEXT NOT NULL,
            predicted_level INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserProgress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            progress TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()



def update_user_progress(username, progress):
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM UserProgress WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user is None:
        cursor.execute('INSERT INTO UserProgress (username, progress) VALUES (?, ?)', (username, progress))
    else:
        cursor.execute('UPDATE UserProgress SET progress = ? WHERE username = ?', (progress, username))
    conn.commit()
    conn.close()
    socketio.emit('progress', {'username': username, 'progress': progress})
    


def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        if session['username'] != 'admin':
            return redirect('/')
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@app.get('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username is None:
            return redirect('/login')
        session['username'] = username
        if username == 'admin':
            return redirect('/dashboard')
        
        update_user_progress(username, "Signed In")
        return redirect('/quiz')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/quiz/get_remaining_time')
def get_remaining_time():
    username = session.get('username')
    if username not in userstarttime:
        return redirect('/quiz')
    starttime = userstarttime[username]
    endtime = starttime + timedelta(seconds=10)
    time = max(0,(endtime - datetime.now()).total_seconds())
    print(time)
    return {'remaining_time': int(time)}


@app.post('/quiz/start')
def start_quiz():
    level = request.form.get('level')
    if level not in [ 'level 1-2' , 'level 3-4' ]:
        return redirect('/quiz')
    
    username = session.get('username')
    userlevel[username] = level
    update_user_progress(username, "In Progress")
    userstarttime[username] = datetime.now()
    return redirect('/quiz')


def grade(correct, total, level):
    if level == 'level 1-2':
        if correct/total >= 0.8:
            return 'level 3-4'
    elif level == 'level 3-4':
        if correct/total < 0.6:
            return 'level 1-2'
    return level


@app.post('/quiz/submit')
def submit_quiz():
    username = session.get('username')
    update_user_progress(username, "Completed")
    answers = request.form.getlist('answers')
    if username not in userquestions:
        return redirect('/quiz')
    questions = userquestions[username]
    score = 0
    cur = 0
    for question in questions:
        
        if question['Type'] == 'single':
            answer = answers[cur]
            if answer == question['Answer']:
                score += 1
            cur += 1

        elif question['Type'] == 'multi':
            for subquestion in question['Sub-Questions']:
                answer = answers[cur]
                if answer == subquestion['Answer']:
                    score += 1
                cur += 1
    
    predicted_level = 1

    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM UserScore WHERE username = ?', (username,))
    user = cursor.fetchone()
    if user is None:
        cursor.execute('INSERT INTO UserScore (username, score, num_questions, level, predicted_level) VALUES (?, ?, ?, ?, ?)', (username, score, cur, userlevel[username], predicted_level))
    else:
        cursor.execute('UPDATE UserScore SET score = ?, num_questions = ?, level = ?, predicted_level = ? WHERE username = ?', (score, cur, userlevel[username], predicted_level, username))
    conn.commit()
    conn.close()
    print(score, cur)
    
    return redirect('/leaderboard')

@app.get('/quiz')
@login_required
def quiz():
    username = session.get('username')
    # Select Level
    # Select Category
    # Select Number of Questions



   # questions = []
   # conn = sqlite3.connect('questions.db')
   # cursor = conn.cursor()
   # cursor.execute('SELECT question, options FROM Questions')
   # questions = cursor.fetchall()
   # conn.close()
    if username not in userlevel:
        return render_template('quiz.html', levelselect= False )
    
    questions = []
    if userlevel[username] == 'level 1-2':
        for question in QUESTION_MASTER["Level1"]:
            questions.append(question)
        for question in QUESTION_MASTER["Level2"]:
            questions.append(question)
    elif userlevel[username] == 'level 3-4':
        for question in QUESTION_MASTER["Level3"]:
            questions.append(question)
        for question in QUESTION_MASTER["Level4"]:
            questions.append(question)
    userquestions[username] = questions
    return render_template('quiz.html', levelselect= True , questions=questions)

@app.get('/dashboard')
@admin_required
def dashboard():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, progress FROM UserProgress')
    progress = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', progress=progress)

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, score, level, predicted_level FROM UserScore ORDER BY score DESC')
    scores = cursor.fetchall()
    conn.close()
    return render_template('leaderboard.html', scores=scores)
    

@app.route('/scores')
def scores():
    user = request.cookies.get('username')

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    init_db()
    #init_questions()
    #pp.run(debug=True, port=6868)
    socketio.run(app, debug=True, port=6868)
