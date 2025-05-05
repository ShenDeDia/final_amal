# final_amal

## 1. Set up EC2 Instance

* Go to AWS Console → EC2 → “Launch Instance”
* Name: `webapp_amal`
* AMI: Ubuntu
* Instance type: `t2.micro`
* Key pair: Create or choose existing `.pem` file (e.g., `amal_key.pem`)

### Configure Security Group (Inbound Rules)

| Type       | Protocol | Port Range | Source              | Purpose                  |
| ---------- | -------- | ---------- | ------------------- | ------------------------ |
| SSH        | TCP      | 22         | Your IP             | Connect to EC2 using SSH |
| HTTP       | TCP      | 80         | 0.0.0.0/0           | Web server access        |
| Custom TCP | TCP      | 5000       | 0.0.0.0/0           | Access Flask API         |
| PostgreSQL | TCP      | 5432       | 0.0.0.0/0 or EC2 SG | Connect RDS from EC2     |

Click **Launch Instance**.

## 2. Set up RDS PostgreSQL Database

* Go to AWS Console → RDS → Create database
* Choose:

  * Creation method: **Standard create**
  * Engine: **PostgreSQL**
  * DB instance identifier: `db_amal`
  * Master username: `postgres`
  * Master password: `postgres`
  * Public access: **Yes**
* Expand “Connectivity”:

  * VPC: default
  * Subnet group: default
  * Security group: same as EC2
* Click **Create database**

### RDS Security Group

* Go to RDS → Databases → `db_amal` → Connectivity & security → VPC Security Group
* Edit inbound rules:

| Type       | Protocol | Port Range | Source (EC2 SG ID) | Purpose                 |
| ---------- | -------- | ---------- | ------------------ | ----------------------- |
| PostgreSQL | TCP      | 5432       | EC2 security group | Allow EC2 to access RDS |

## 3. Connect to RDS and Import Data Using DBeaver

### Step 1: Connect to RDS

1. Open DBeaver
2. Database → New Database Connection → Select PostgreSQL
3. Enter:

   * Host: `db-amal.c32geugqgvkj.ap-southeast-1.rds.amazonaws.com`
   * Database: `postgres`
   * User: `postgres`
   * Password: `postgres`
4. Test Connection → Finish

### Step 2: Create New Database

* Right-click on `postgres` → Create → Database
* Name: `db_amal`
* Click OK

### Step 3: Import CSV to New Table

* Right-click on `db_amal` → Tools → Import Data from CSV
* Select CSV file
* Table name: `tbl_amal_netflix`
* Columns: `area`, `years`, `revenue`
* Set `revenue` type to BIGINT
* Click Next → Finish

## 4. SSH into EC2

```bash
ssh -i "C:\path\to\amal_key.pem" ubuntu@<EC2_Public_IP>
```

## 5. Set up Flask Environment

```bash
sudo apt update
sudo apt install python3-pip python3.10-venv -y
```

## 6. Create Project Folder and Virtual Env

```bash
mkdir webapp_amal
cd webapp_amal
python3 -m venv venv
source venv/bin/activate
```

## 7. Install Python Dependencies

```bash
pip install flask flask-cors psycopg2-binary
```

## 8. Create Flask App (app.py)

```python
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
```

## 9. Run Flask App

```bash
python app.py
```

Expected: `Running on http://0.0.0.0:5000/`

## 10. Create index\_amal.html

Create file `index_amal.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Netflix Revenue Dashboard</title>
  <script>
    async function loadData() {
      const res = await fetch("http://<EC2_Public_IP>:5000/data");
      const data = await res.json();
      let table = "<table border='1'><tr><th>ID</th><th>Area</th><th>Years</th><th>Revenue</th></tr>";
      for (let row of data) {
        table += `<tr><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td><td>${row[3]}</td></tr>`;
      }
      table += "</table>";
      document.getElementById("result").innerHTML = table;
    }

    async function addDummy() {
      await fetch("http://<EC2_Public_IP>:5000/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ area: "Dummy", years: "Q3-2025", revenue: 123456789 })
      });
      loadData();
    }

    async function deleteDummy() {
      await fetch("http://<EC2_Public_IP>:5000/delete", { method: "POST" });
      loadData();
    }
  </script>
</head>
<body>
  <h1>Netflix Revenue Dashboard</h1>
  <button onclick="loadData()">Load Data</button>
  <button onclick="addDummy()">Add Dummy</button>
  <button onclick="deleteDummy()">Delete Last</button>
  <div id="result"></div>
</body>
</html>
```

## 11. Upload HTML to S3

* Go to AWS Console → S3 → Create bucket
* Name: `netflix-dashboard-amal`
* Uncheck: **Block all public access**
* Go to **Properties → Static website hosting**

  * Enable
  * Index document: `index_amal.html`
* Upload your `index_amal.html` file
* Go to **Permissions → Bucket Policy** and add:

```json
{
  "Version":"2012-10-17",
  "Statement":[{
    "Effect":"Allow",
    "Principal":"*",
    "Action":"s3:GetObject",
    "Resource":"arn:aws:s3:::netflix-dashboard-amal/*"
  }]
}
```

## 12. Final Test

Open:

```
http://netflix-dashboard-amal.s3-website-<region>.amazonaws.com
```

Click buttons:

* **Load Data** → fetches from RDS
* **Add Dummy** → inserts dummy row
* **Delete Dummy** → removes last row
