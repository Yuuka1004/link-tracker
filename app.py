from flask import Flask, request, redirect, render_template_string
import sqlite3
import requests
from datetime import datetime
import os

app = Flask(__name__)

# Buat folder trackers jika belum ada
os.makedirs('trackers', exist_ok=True)

# Inisialisasi database
conn = sqlite3.connect('tracking.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracker_id TEXT,
                ip TEXT,
                city TEXT,
                region TEXT,
                country TEXT,
                timestamp TEXT,
                user_agent TEXT
            )''')
conn.commit()

# Halaman utama
@app.route('/')
def home():
    return '''
        <h1>Create Tracking Link</h1>
        <form action="/generate" method="post">
            Tracker ID: <input name="tracker_id"><br>
            Redirect URL: <input name="redirect_url"><br>
            <button type="submit">Generate</button>
        </form>
    '''

# Generate tracking link
@app.route('/generate', methods=['POST'])
def generate():
    tracker_id = request.form['tracker_id']
    redirect_url = request.form['redirect_url']
    with open(f'trackers/{tracker_id}.txt', 'w') as f:
        f.write(redirect_url)
    return f'Tracking link created: <a href="/track/{tracker_id}">/track/{tracker_id}</a>'

# Proses tracking
@app.route('/track/<tracker_id>')
def track(tracker_id):
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    try:
        geo_data = requests.get(f'https://ipinfo.io/{ip}/json').json()
    except:
        geo_data = {}

    city = geo_data.get('city', 'Unknown')
    region = geo_data.get('region', 'Unknown')
    country = geo_data.get('country', 'Unknown')
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('INSERT INTO visits (tracker_id, ip, city, region, country, timestamp, user_agent) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (tracker_id, ip, city, region, country, timestamp, user_agent))
    conn.commit()

    try:
        with open(f'trackers/{tracker_id}.txt') as f:
            redirect_url = f.read().strip()
        return redirect(redirect_url)
    except:
        return "Invalid tracker ID or redirect URL not set."

# Lihat log per tracker
@app.route('/logs/<tracker_id>')
def logs(tracker_id):
    c.execute('SELECT * FROM visits WHERE tracker_id = ?', (tracker_id,))
    logs = c.fetchall()
    return render_template_string('''
        <h2>Tracking Logs for {{ tracker_id }}</h2>
        <table border="1">
            <tr><th>ID</th><th>IP</th><th>City</th><th>Region</th><th>Country</th><th>Time</th><th>User Agent</th></tr>
            {% for row in logs %}
            <tr>{% for col in row[1:] %}<td>{{ col }}</td>{% endfor %}</tr>
            {% endfor %}
        </table>
    ''', tracker_id=tracker_id, logs=logs)

# Lihat semua log
@app.route('/data')
def view_data():
    conn = sqlite3.connect('tracking.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visits")
    rows = cursor.fetchall()
    conn.close()

    html = """
    <h2>All Tracking Results</h2>
    <table border="1" cellpadding="5">
        <tr><th>ID</th><th>Tracker ID</th><th>IP</th><th>City</th><th>Region</th><th>Country</th><th>Timestamp</th><th>User-Agent</th></tr>
        {% for row in rows %}
        <tr>
            <td>{{ row[0] }}</td>
            <td>{{ row[1] }}</td>
            <td>{{ row[2] }}</td>
            <td>{{ row[3] }}</td>
            <td>{{ row[4] }}</td>
            <td>{{ row[5] }}</td>
            <td>{{ row[6] }}</td>
            <td>{{ row[7] }}</td>
        </tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
