from flask import Flask, render_template, request, redirect, session, g
import mysql.connector, re

app = Flask(__name__)
app.secret_key = "secret"

# --------- DB CONNECTION ---------
def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host="localhost",
            user="flaskuser",
            password="flaskpass",
            database="flaskapp"
        )
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()

# --------- REGISTER ---------
@app.route("/register", methods=["GET","POST"])
def register():
    error=""
    if request.method=="POST":
        name = request.form["name"]
        email = request.form["email"]
        gender = request.form["gender"]
        username = request.form["username"]
        password = request.form["password"]

        # VALIDATION
        if not name.replace(" ", "").isalpha():
            error="Name can only contain letters and spaces."
        elif not re.fullmatch(r"[a-zA-Z0-9_]{8,9}", username):
            error="Username must be 8–9 characters (letters, numbers, underscore)."
        elif not re.fullmatch(r"[0-9a-f]{8}", password):
            error="Password must be 8 digits or hex."
        else:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                error="Username already exists!"
            else:
                # INSERT including email and gender
                cursor.execute(
                    "INSERT INTO users (name, email, gender, username, password, role) VALUES (%s,%s,%s,%s,%s,'user')",
                    (name, email, gender, username, password)
                )
                db.commit()
            cursor.close()
            if not error:
                return redirect("/")

    return render_template("register.html", error=error)

# --------- LOGIN ---------
@app.route("/", methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session["user"] = user["username"]
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect("/packages")
        else:
            error="Wrong username or password!"

    return render_template("login.html", error=error)

# --------- PACKAGE SELECTION (MULTI) ---------
@app.route("/packages", methods=["GET","POST"])
def packages():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get all packages
    cursor.execute("SELECT * FROM packages")
    packages = cursor.fetchall()

    # Get user's current selections
    cursor.execute("SELECT package_id FROM user_packages WHERE user_id=%s", (session["user_id"],))
    user_packages = [row["package_id"] for row in cursor.fetchall()]

    if request.method == "POST":
        # Get selected package IDs (checkboxes)
        package_ids = request.form.getlist("package_ids")  # list of strings

        # Remove all old selections
        cursor.execute("DELETE FROM user_packages WHERE user_id=%s", (session["user_id"],))

        # Insert new selections
        for pid in package_ids:
            cursor.execute(
                "INSERT INTO user_packages (user_id, package_id) VALUES (%s,%s)",
                (session["user_id"], pid)
            )
        db.commit()
        return redirect("/summary")

    cursor.close()
    return render_template("packages.html", packages=packages, user_packages=user_packages, username=session["user"])

# --------- SUMMARY ---------
@app.route("/summary")
def summary():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email, gender, username FROM users WHERE id=%s", (session["user_id"],))
    user = cursor.fetchone()

    cursor.execute("""
        SELECT p.package_name, p.price FROM packages p
        JOIN user_packages up ON p.package_id = up.package_id
        WHERE up.user_id=%s
    """, (session["user_id"],))
    packages = cursor.fetchall()

    cursor.close()
    return render_template("summary.html", user=user, packages=packages)

# --------- EDIT PROFILE ---------
@app.route("/edit_profile", methods=["GET","POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    user = cursor.fetchone()
    error=""

    if request.method=="POST":
        name = request.form["name"]
        email = request.form["email"]
        gender = request.form["gender"]
        username = request.form["username"]
        password = request.form["password"]

        # VALIDATION
        if not name.replace(" ", "").isalpha():
            error = "Name can only contain letters and spaces."
        elif not re.fullmatch(r"[a-zA-Z0-9_]{8,9}", username):
            error = "Username must be 8–9 characters (letters, numbers, underscore)."
        elif not re.fullmatch(r"[0-9a-f]{8}", password):
            error = "Password must be 8 digits or hex."
        else:
            cursor.execute(
                "SELECT * FROM users WHERE username=%s AND id!=%s",
                (username, session["user_id"])
            )
            if cursor.fetchone():
                error="Username already exists!"
            else:
                cursor.execute(
                    "UPDATE users SET name=%s, email=%s, gender=%s, username=%s, password=%s WHERE id=%s",
                    (name, email, gender, username, password, session["user_id"])
                )
                db.commit()
                session["user"] = username
                cursor.close()
                return redirect("/summary")

    cursor.close()
    return render_template("edit_profile.html", user=user, error=error)

# --------- DELETE ACCOUNT ---------
@app.route("/delete_account")
def delete_account():
    if "user_id" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (session["user_id"],))
    db.commit()
    cursor.close()

    session.clear()
    return "Your account has been deleted. <a href='/'>Go to Login</a>"

# --------- LOGOUT ---------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)