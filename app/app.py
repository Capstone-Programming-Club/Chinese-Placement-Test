from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('userscores.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserScore (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            score INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('userscores.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, score FROM UserScore')
    scores = cursor.fetchall()
    conn.close()
    return render_template('index.html', scores=scores)

@app.route('/add', methods=['POST'])
def add_score():
    username = request.form['username']
    score = request.form['score']
    try:
        conn = sqlite3.connect('userscores.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO UserScore (username, score) VALUES (?, ?)', (username, score))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return "Username already exists!"
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=6868)
