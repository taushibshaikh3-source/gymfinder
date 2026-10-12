from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)

app.secret_key = "gymfinder_secret_key"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    connection = sqlite3.connect(
        "gym.db",
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA busy_timeout = 10000"
    )

    return connection


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# ALL GYMS
# =========================================================

@app.route("/gyms")
def gyms():

    connection = get_db_connection()

    gyms = connection.execute(
        "SELECT * FROM gyms"
    ).fetchall()

    connection.close()

    return render_template(
        "gyms.html",
        gyms=gyms
    )


# =========================================================
# GYM DETAILS
# =========================================================

@app.route("/gym/<int:gym_id>")
def gym_details(gym_id):

    connection = get_db_connection()

    gym = connection.execute(
        """
        SELECT *
        FROM gyms
        WHERE id = ?
        """,
        (gym_id,)
    ).fetchone()

    connection.close()

    if not gym:

        return "Gym not found"

    return render_template(
        "gym_details.html",
        gym=gym
    )


# =========================================================
# GYM MEMBERSHIP PLANS - PUBLIC
# =========================================================

@app.route("/gym/<int:gym_id>/plans")
def gym_plans(gym_id):

    connection = get_db_connection()

    gym = connection.execute(
        """
        SELECT *
        FROM gyms
        WHERE id = ?
        """,
        (gym_id,)
    ).fetchone()

    if not gym:

        connection.close()

        return "Gym not found"

    plans = connection.execute(
        """
        SELECT *
        FROM membership_plans
        WHERE gym_id = ?
        ORDER BY id DESC
        """,
        (gym_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "gym_plans.html",
        gym=gym,
        plans=plans
    )


# =========================================================
# GYM TRAINERS - PUBLIC
# =========================================================

@app.route("/gym/<int:gym_id>/trainers")
def gym_trainers(gym_id):

    connection = get_db_connection()

    gym = connection.execute(
        """
        SELECT *
        FROM gyms
        WHERE id = ?
        """,
        (gym_id,)
    ).fetchone()

    if not gym:

        connection.close()

        return "Gym not found"

    trainers = connection.execute(
        """
        SELECT *
        FROM trainers
        WHERE gym_id = ?
        ORDER BY id DESC
        """,
        (gym_id,)
    ).fetchall()

    connection.close()

    return render_template(
        "gym_trainers.html",
        gym=gym,
        trainers=trainers
    )


# =========================================================
# BOOK TRAINER
# =========================================================

@app.route(
    "/book-trainer/<int:trainer_id>",
    methods=["GET", "POST"]
)
def book_trainer(trainer_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if session.get("user_role") != "trainee":

        return "Only trainees can book trainers.", 403

    connection = get_db_connection()

    try:

        trainer = connection.execute(
            """
            SELECT *
            FROM trainers
            WHERE id = ?
            """,
            (trainer_id,)
        ).fetchone()

        if not trainer:

            return "Trainer not found"


        gym = connection.execute(
            """
            SELECT *
            FROM gyms
            WHERE id = ?
            """,
            (trainer["gym_id"],)
        ).fetchone()

        if not gym:

            return "Gym not found"


        if request.method == "POST":

            booking_date = request.form.get(
                "booking_date"
            )

            booking_time = request.form.get(
                "booking_time"
            )


            if not booking_date or not booking_time:

                return "Please select a date and time."


            connection.execute(
                """
                INSERT INTO trainer_bookings
                (
                    trainee_id,
                    trainer_id,
                    gym_id,
                    booking_date,
                    booking_time,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    trainer_id,
                    trainer["gym_id"],
                    booking_date,
                    booking_time,
                    "Pending"
                )
            )


            connection.commit()


            return redirect(
                url_for("dashboard")
            )


        return render_template(
            "book_trainer.html",
            trainer=trainer,
            gym=gym
        )


    finally:

        connection.close()


# =========================================================
# TRAINEE SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                password,
                "trainee"
            )
        )

        connection.commit()

        connection.close()

        return "Account created successfully!"


    return render_template(
        "signup.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    selected_role = request.args.get(
        "role",
        "trainee"
    )


    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        selected_role = request.form["role"]

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            AND role = ?
            """,
            (
                email,
                password,
                selected_role
            )
        ).fetchone()

        connection.close()


        if user:

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            session["user_role"] = user["role"]

            return redirect(
                url_for("dashboard")
            )


        return "Invalid email, password, or account type."


    return render_template(
        "login.html",
        role=selected_role
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    if not user:

        connection.close()

        session.clear()

        return redirect(
            url_for("login")
        )


    # =====================================================
    # TRAINEE BOOKINGS
    # =====================================================

    bookings = []

    if user["role"] == "trainee":

        bookings = connection.execute(
            """
            SELECT
                trainer_bookings.*,
                trainers.name AS trainer_name,
                gyms.name AS gym_name

            FROM trainer_bookings

            JOIN trainers
                ON trainer_bookings.trainer_id = trainers.id

            JOIN gyms
                ON trainer_bookings.gym_id = gyms.id

            WHERE trainer_bookings.trainee_id = ?

            ORDER BY trainer_bookings.id DESC
            """,
            (session["user_id"],)
        ).fetchall()


    connection.close()


    return render_template(
        "dashboard.html",
        name=user["name"],
        role=user["role"],
        bookings=bookings
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# ROLE LOGIN
# =========================================================

@app.route("/role-login")
def role_login():

    return render_template(
        "role_login.html"
    )


# =========================================================
# TRAINER SIGNUP
# =========================================================

@app.route(
    "/trainer-signup",
    methods=["GET", "POST"]
)
def trainer_signup():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                password,
                "trainer"
            )
        )

        connection.commit()

        connection.close()

        return "Trainer account created successfully!"


    return render_template(
        "trainer_signup.html"
    )


# =========================================================
# OWNER SIGNUP
# =========================================================

@app.route(
    "/owner-signup",
    methods=["GET", "POST"]
)
def owner_signup():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO users
            (name, email, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                password,
                "owner"
            )
        )

        connection.commit()

        connection.close()

        return "Gym owner account created successfully!"


    return render_template(
        "owner_signup.html"
    )


# =========================================================
# OWNER - MY GYM
# =========================================================

@app.route(
    "/owner-gym",
    methods=["GET", "POST"]
)
def owner_gym():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("user_role") != "owner":

        return "Access denied", 403


    connection = get_db_connection()


    if request.method == "POST":

        name = request.form["name"]

        location = request.form["location"]

        price = request.form["price"]

        opening_time = request.form["opening_time"]

        closing_time = request.form["closing_time"]

        description = request.form["description"]


        connection.execute(
            """
            INSERT INTO gyms
            (
                owner_id,
                name,
                location,
                price,
                rating,
                opening_time,
                closing_time,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                name,
                location,
                price,
                0,
                opening_time,
                closing_time,
                description
            )
        )


        connection.commit()

        connection.close()


        return redirect(
            url_for("owner_gym")
        )


    gym = connection.execute(
        """
        SELECT *
        FROM gyms
        WHERE owner_id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    connection.close()


    return render_template(
        "owner_gym.html",
        gym=gym
    )


# =========================================================
# OWNER - EDIT GYM
# =========================================================

@app.route(
    "/edit-gym",
    methods=["GET", "POST"]
)
def edit_gym():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("user_role") != "owner":

        return "Access denied", 403


    connection = get_db_connection()


    gym = connection.execute(
        """
        SELECT *
        FROM gyms
        WHERE owner_id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    if not gym:

        connection.close()

        return redirect(
            url_for("owner_gym")
        )


    if request.method == "POST":

        name = request.form["name"]

        location = request.form["location"]

        price = request.form["price"]

        opening_time = request.form["opening_time"]

        closing_time = request.form["closing_time"]

        description = request.form["description"]


        connection.execute(
            """
            UPDATE gyms

            SET name = ?,
                location = ?,
                price = ?,
                opening_time = ?,
                closing_time = ?,
                description = ?

            WHERE id = ?
            AND owner_id = ?
            """,
            (
                name,
                location,
                price,
                opening_time,
                closing_time,
                description,
                gym["id"],
                session["user_id"]
            )
        )


        connection.commit()

        connection.close()


        return redirect(
            url_for("owner_gym")
        )


    connection.close()


    return render_template(
        "edit_gym.html",
        gym=gym
    )


# =========================================================
# OWNER - MEMBERSHIP PLANS
# =========================================================

@app.route(
    "/owner-plans",
    methods=["GET", "POST"]
)
def owner_plans():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("user_role") != "owner":

        return "Access denied", 403


    connection = get_db_connection()


    gym = connection.execute(
        """
        SELECT *
        FROM gyms
        WHERE owner_id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    if not gym:

        connection.close()

        return "No gym is linked to this owner."


    if request.method == "POST":

        plan_name = request.form["plan_name"]

        duration = request.form["duration"]

        price = request.form["price"]

        description = request.form.get(
            "description",
            ""
        )


        connection.execute(
            """
            INSERT INTO membership_plans
            (
                gym_id,
                plan_name,
                duration,
                price,
                description
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                gym["id"],
                plan_name,
                duration,
                int(price),
                description
            )
        )


        connection.commit()

        connection.close()


        return redirect(
            url_for("owner_plans")
        )


    plans = connection.execute(
        """
        SELECT *
        FROM membership_plans
        WHERE gym_id = ?
        ORDER BY id DESC
        """,
        (gym["id"],)
    ).fetchall()


    connection.close()


    return render_template(
        "owner_plans.html",
        gym=gym,
        plans=plans
    )


# =========================================================
# OWNER - MANAGE TRAINERS
# =========================================================

@app.route(
    "/manage-trainers",
    methods=["GET", "POST"]
)
def manage_trainers():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    if session.get("user_role") != "owner":

        return "Access denied", 403


    connection = get_db_connection()


    gym = connection.execute(
        """
        SELECT *
        FROM gyms
        WHERE owner_id = ?
        """,
        (session["user_id"],)
    ).fetchone()


    if not gym:

        connection.close()

        return "No gym is linked to this owner."


    if request.method == "POST":

        name = request.form["name"]

        specialization = request.form.get(
            "specialization",
            ""
        )

        experience = request.form.get(
            "experience"
        )

        phone = request.form.get(
            "phone",
            ""
        )

        availability = request.form.get(
            "availability",
            ""
        )


        if not experience:

            experience = 0


        connection.execute(
            """
            INSERT INTO trainers
            (
                gym_id,
                name,
                specialization,
                experience,
                phone,
                availability
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                gym["id"],
                name,
                specialization,
                int(experience),
                phone,
                availability
            )
        )


        connection.commit()

        connection.close()


        return redirect(
            url_for("manage_trainers")
        )


    trainers = connection.execute(
        """
        SELECT *
        FROM trainers
        WHERE gym_id = ?
        ORDER BY id DESC
        """,
        (gym["id"],)
    ).fetchall()


    connection.close()


    return render_template(
        "manage_trainers.html",
        gym=gym,
        trainers=trainers
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)