from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

conn = psycopg2.connect(
    host="db-amal.c32geugqgvkj.ap-southeast-1.rds.amazonaws.com",
    dbname="postgres",
    user="postgres",
    password="postgres",
    port=5432
)

@app.route('/data')
def get_data():
    cur = conn.cursor()
    cur.execute("SELECT * FROM tbl_amal_netflix")
    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)

@app.route('/add', methods=['POST'])
def add_data():
    data = request.json
    cur = conn.cursor()
    cur.execute("INSERT INTO tbl_amal_netflix (area, years, revenue) VALUES (%s, %s, %s)", (data['area'], data['years'], data['revenue']))
    conn.commit()
    cur.close()
    return jsonify({'message': 'Added'})

@app.route('/delete', methods=['POST'])
def delete_data():
    cur = conn.cursor()
    cur.execute("DELETE FROM tbl_amal_netflix WHERE id = (SELECT MAX(id) FROM tbl_amal_netflix)")
    conn.commit()
    cur.close()
    return jsonify({'message': 'Deleted'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)