
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super_secret_watchlist_key'

# Конфигурация
VIEW_ONLY_PASS = "ISBAC-2"
ADMIN_PASS = "ISBM&R29"
DB_NAME = "database.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roblox_user TEXT NOT NULL,
                discord_id TEXT NOT NULL,
                reason TEXT,
                date_start TEXT,
                date_end TEXT,
                investigation TEXT,
                priority TEXT
            )
        ''')
    conn.close()

@app.route('/')
def login():
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def do_login():
    password = request.form.get('password')
    if password == ADMIN_PASS:
        session['role'] = 'admin'
        return redirect(url_for('index'))
    elif password == VIEW_ONLY_PASS:
        session['role'] = 'viewer'
        return redirect(url_for('index'))
    else:
        flash('Неверный пароль!')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/watchlist')
def index():
    if 'role' not in session:
        return redirect(url_for('login'))
    
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT * FROM watchlist ORDER BY id DESC')
        rows = cur.fetchall()
    return render_template_string(INDEX_HTML, rows=rows, role=session['role'])

@app.route('/add', methods=['POST'])
def add_entry():
    if session.get('role') != 'admin':
        return "Access Denied", 403
    
    data = (
        request.form.get('roblox_user'),
        request.form.get('discord_id'),
        request.form.get('reason'),
        request.form.get('date_start'),
        request.form.get('date_end'),
        request.form.get('investigation'),
        request.form.get('priority')
    )
    
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''
            INSERT INTO watchlist (roblox_user, discord_id, reason, date_start, date_end, investigation, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_entry(id):
    if session.get('role') != 'admin':
        return "Access Denied", 403
    
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('DELETE FROM watchlist WHERE id = ?', (id,))
    return redirect(url_for('index'))

# HTML Templates
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Watchlist Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #121212; color: white; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .card { background: #1e1e1e; border: 1px solid #333; width: 350px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .btn-primary { background: #6200ee; border: none; }
    </style>
</head>
<body>
    <div class="card text-center">
        <h3>Watchlist Access</h3>
        <hr>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="alert alert-danger">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form action="/login" method="post">
            <input type="password" name="password" class="form-control mb-3" placeholder="Enter Password" required>
            <button type="submit" class="btn btn-primary w-100">Login</button>
        </form>
    </div>
</body>
</html>
'''

INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Watchlist Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0f0f0f; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .container { margin-top: 30px; }
        .table { background: #1a1a1a; color: #e0e0e0; border-radius: 8px; overflow: hidden; }
        .table th { background: #252525; border-color: #333; }
        .table td { border-color: #333; vertical-align: middle; }
        .badge-high { background-color: #b00020; }
        .badge-medium { background-color: #fb8c00; color: black; }
        .badge-low { background-color: #4caf50; }
        .admin-section { background: #1a1a1a; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #333; }
        .logout-btn { color: #888; text-decoration: none; }
        .logout-btn:hover { color: #fff; }
    </style>
</head>
<body>
<div class="container">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>🛡️ Watchlist System <small class="text-muted" style="font-size: 0.5em;">({{ role.upper() }} MODE)</small></h2>
        <a href="/logout" class="logout-btn">Log out</a>
    </div>

    {% if role == 'admin' %}
    <div class="admin-section">
        <h5>Add New Entry</h5>
        <form action="/add" method="post" class="row g-3">
            <div class="col-md-3">
                <input type="text" name="roblox_user" class="form-control bg-dark text-white border-secondary" placeholder="Roblox Username" required>
            </div>
            <div class="col-md-3">
                <input type="text" name="discord_id" class="form-control bg-dark text-white border-secondary" placeholder="Discord ID" required>
            </div>
            <div class="col-md-2">
                <input type="text" name="date_start" class="form-control bg-dark text-white border-secondary" placeholder="Start DD/MM/YY" required>
            </div>
            <div class="col-md-2">
                <input type="text" name="date_end" class="form-control bg-dark text-white border-secondary" placeholder="End DD/MM/YY" required>
            </div>
            <div class="col-md-2">
                <select name="priority" class="form-select bg-dark text-white border-secondary">
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                </select>
            </div>
            <div class="col-12">
                <input type="text" name="reason" class="form-control bg-dark text-white border-secondary" placeholder="Placement Reason" required>
            </div>
            <div class="col-12">
                <input type="text" name="investigation" class="form-control bg-dark text-white border-secondary" placeholder="Investigation (Link or Message)">
            </div>
            <div class="col-12 text-end">
                <button type="submit" class="btn btn-success px-4">Add to List</button>
            </div>
        </form>
    </div>
    {% endif %}

    <div class="table-responsive">
        <table class="table">
            <thead>
                <tr>
                    <th>Roblox User</th>
                    <th>Discord ID</th>
                    <th>Reason</th>
                    <th>Duration</th>
                    <th>Investigation</th>
                    <th>Priority</th>
                    {% if role == 'admin' %}<th>Action</th>{% endif %}
                </tr>
            </thead>
            <tbody>
                {% for row in rows %}
                <tr>
                    <td><strong>{{ row['roblox_user'] }}</strong></td>
                    <td><code>{{ row['discord_id'] }}</code></td>
                    <td>{{ row['reason'] }}</td>
                    <td><small>{{ row['date_start'] }} — {{ row['date_end'] }}</small></td>
                    <td>
                        {% if row['investigation'].startswith('http') %}
                            <a href="{{ row['investigation'] }}" target="_blank">View File</a>
                        {% else %}
                            {{ row['investigation'] }}
                        {% endif %}
                    </td>
                    <td>
                        <span class="badge badge-{{ row['priority'].lower() }}">
                            {{ row['priority'] }}
                        </span>
                    </td>
                    {% if role == 'admin' %}
                    <td>
                        <a href="/delete/{{ row['id'] }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Удалить?')">Delete</a>
                    </td>
                    {% endif %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
'''

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
