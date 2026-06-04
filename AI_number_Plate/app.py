from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
import bcrypt
import subprocess
import pandas as pd
import re
import os
import time
import webbrowser
import sys

app = Flask(__name__)
app.secret_key = os.getenv(
    "SECRET_KEY",
    "fallback_secret_key"
)

# =====================================================
# DATABASE CONNECTION
# =====================================================
def get_db_connection():

    try:

        return psycopg2.connect(
            host="localhost",
            database="number_plate",
            user="postgres",
            password="Nandan@123"
        )

    except Exception as e:

        print("Database Connection Error:", e)

        return None
conn = get_db_connection()
cursor = conn.cursor()        

# =====================================================
# HOME PAGE
# =====================================================
@app.route('/')
def home():

    if "user" in session:

        return render_template(
            "index.html",
            user=session["user"]
        )

    return redirect(url_for("login"))

# =====================================================
# REGISTER USER
# =====================================================
@app.route('/register_user', methods=['GET', 'POST'])
def register_user():

    if request.method == 'POST':

        username = request.form['username']
        address = request.form['address']
        mobile_no = request.form['mobile_no']
        password = request.form['password']

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (username, address, mobile_no, password)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    username,
                    address,
                    mobile_no,
                    hashed_password
                )
            )

            conn.commit()

            return redirect(url_for("login"))

        except Exception as e:

            conn.rollback()

            return f"Error: {e}"

        finally:

            cursor.close()
            conn.close()

    return render_template("register.html")

# =====================================================
# LOGIN
# =====================================================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username=%s
            """,
            (username,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(
            password.encode('utf-8'),
            user[4].encode('utf-8')
        ):

            session["user"] = username

            return redirect(url_for("home"))

        return "Invalid Username or Password"

    return render_template("login.html")

# =====================================================
# LOGOUT
# =====================================================
@app.route('/logout')
def logout():

    session.pop("user", None)

    return redirect(url_for("login"))

# =====================================================
# REGISTER VEHICLE
# =====================================================
@app.route('/register', methods=['POST'])
def register_vehicle():

    data = request.get_json()

    name = data.get("name")
    address = data.get("address")

    vehicle_number = data.get(
    "vehicle_number",
    ""
    ).upper().strip()
    amount = float(data.get("amount", 0)
)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO vehicle_registration
            (
                name,
                address,
                vehicle_number,
                amount,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                name,
                address,
                vehicle_number,
                amount,
                "Paid"
            )
        )

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Vehicle Registered Successfully"
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        cursor.close()
        conn.close()

# =====================================================
# CHECK BALANCE PAGE
# =====================================================
@app.route('/check_balance')
def check_balance_page():

    return render_template("balance.html")

# =====================================================
# CHECK BALANCE API
# =====================================================
@app.route('/check_balance_api', methods=['POST'])
def check_balance_api():

    data = request.get_json()

    vehicle_number = data.get(
    "vehicle_number",
    ""
    ).upper().strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            name,
            vehicle_number,
            amount
        FROM vehicle_registration
        WHERE UPPER(vehicle_number)=%s
        """,
        (vehicle_number,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:

        return jsonify({
            "status": "success",
            "name": result[0],
            "vehicle_number": result[1],
            "balance": float(result[2])
        })

    return jsonify({
        "status": "error",
        "message": "Vehicle Not Found"
    })

# =====================================================
# RECHARGE BALANCE
# =====================================================
@app.route('/recharge_balance', methods=['POST'])
def recharge_balance():

    try:

        data = request.get_json()

        vehicle_number = data.get(
        "vehicle_number",
        ""
        ).upper().strip()

        recharge_amount = float(
            data.get("amount")
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT amount
            FROM vehicle_registration
            WHERE UPPER(vehicle_number)=%s
            """,
            (vehicle_number,)
        )

        result = cursor.fetchone()

        if result:

            current_balance = float(result[0])

            new_balance = (
                current_balance +
                recharge_amount
            )

            cursor.execute(
                """
                UPDATE vehicle_registration
                SET amount=%s
                WHERE UPPER(vehicle_number)=%s
                """,
                (
                    new_balance,
                    vehicle_number
                )
            )

            conn.commit()

            return jsonify({
                "status": "success",
                "message": "Recharge Successful",
                "vehicle_number": vehicle_number,

                "new_balance": new_balance
            })

        else:

            return jsonify({
                "status": "error",
                "message": "Vehicle Not Found"
            })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })

    finally:

        cursor.close()
        conn.close()

# =====================================================
# READ DETECTED NUMBER PLATE
# =====================================================
def get_detected_number_plate():

    try:

        if not os.path.exists("data.csv"):
            return None

        df = pd.read_csv("data.csv")

        if df.empty:
            return None

        detected_plate = df.iloc[-1]["number_plate"]

        detected_plate = re.sub(
            r'[^A-Z0-9]',
            '',
            str(detected_plate).upper()
        )

        print("Detected Plate:", detected_plate)

        return detected_plate

    except Exception as e:

        print("CSV Error:", e)

        return None

# =====================================================
# DEDUCT TOLL BALANCE
# =====================================================
def deduct_toll_balance(number_plate):

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        number_plate = number_plate.upper().strip()

        cursor.execute(
            """
            SELECT amount
            FROM vehicle_registration
            WHERE UPPER(vehicle_number)=%s
            """,
            (number_plate,)
        )

        result = cursor.fetchone()

        if result:

            current_balance = float(result[0])

            toll_amount = 100

            print("Current Balance:", current_balance)

            if current_balance >= toll_amount:

                new_balance = (
                    current_balance -
                    toll_amount
                )

                cursor.execute(
                    """
                    UPDATE vehicle_registration
                    SET amount=%s
                    WHERE UPPER(vehicle_number)=%s
                    """,
                    (
                        new_balance,
                        number_plate
                    )
                )

                conn.commit()

                print("New Balance:", new_balance)

                return {
                    "status": True,
                    "balance": new_balance
                }

            else:

                return {
                    "status": False,
                    "message": "Insufficient Balance"
                }

        else:

            return {
                "status": False,
                "message": "Vehicle Not Registered"
            }

    except Exception as e:

        print("Database Error:", e)

        return {
            "status": False,
            "message": str(e)
        }

    finally:

        cursor.close()
        conn.close()

# =====================================================
# START STREAMLIT
# =====================================================
@app.route('/detect')
def detect_number_plate():

    try:

        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "test1.py",
                "--server.headless",
                "true"
            ]
        )

        time.sleep(5)

        webbrowser.open(
            "http://localhost:8501"
        )

        return jsonify({
            "status": "success",
            "message": "Streamlit Started Successfully"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })

# =====================================================
# CHECK DETECTED PLATE
# =====================================================
@app.route('/check_detected_plate')
def check_detected_plate():

    try:

        detected_plate = get_detected_number_plate()

        if not detected_plate:

            return jsonify({
                "status": "error",
                "message": "No Plate Detected"
            })

        result = deduct_toll_balance(
            detected_plate
        )

        if result["status"]:

            return jsonify({
                "status": "success",
                "message": "Toll Deducted Successfully",
                "plate": detected_plate,
                "remaining_balance": result["balance"]
            })

        else:

            return jsonify({
                "status": "error",
                "message": result["message"],
                "plate": detected_plate
            })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })

# =====================================================
# DETECT VEHICLE
# =====================================================
@app.route('/detect_vehicle', methods=['POST'])
def detect_vehicle():

    try:

        subprocess.Popen(
            [
                sys.executable,
                "main12.py"
            ]
        )

        return jsonify({
            "status": "success",
            "message": "Vehicle Detection Started"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        })

# =====================================================
# MAIN
# =====================================================
if __name__ == '__main__':

    app.run(
        debug=True,
        port=5000
    )