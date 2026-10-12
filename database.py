import sqlite3


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def create_database():

    connection = sqlite3.connect("gym.db")

    cursor = connection.cursor()


    # -------------------------
    # GYMS TABLE
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            price INTEGER NOT NULL,
            rating REAL NOT NULL,
            opening_time TEXT,
            closing_time TEXT,
            description TEXT
        )
    """)


    # -------------------------
    # USERS TABLE
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'trainee'
        )
    """)


    # -------------------------
    # MEMBERSHIP PLANS TABLE
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS membership_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gym_id INTEGER NOT NULL,
            plan_name TEXT NOT NULL,
            duration TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            FOREIGN KEY (gym_id) REFERENCES gyms(id)
        )
    """)


    # -------------------------
    # TRAINERS TABLE
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trainers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gym_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            specialization TEXT,
            experience INTEGER,
            phone TEXT,
            availability TEXT,
            FOREIGN KEY (gym_id) REFERENCES gyms(id)
        )
    """)


    # -------------------------
    # TRAINER BOOKINGS TABLE
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trainer_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainee_id INTEGER NOT NULL,
            trainer_id INTEGER NOT NULL,
            gym_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (trainee_id) REFERENCES users(id),
            FOREIGN KEY (trainer_id) REFERENCES trainers(id),
            FOREIGN KEY (gym_id) REFERENCES gyms(id)
        )
    """)


    connection.commit()

    connection.close()


# =========================================================
# SAMPLE GYMS
# =========================================================

def add_sample_gyms():

    connection = sqlite3.connect("gym.db")

    cursor = connection.cursor()


    cursor.execute(
        "SELECT COUNT(*) FROM gyms"
    )

    count = cursor.fetchone()[0]


    if count == 0:

        gyms = [

            (
                "Iron House Fitness",
                "Kurla, Mumbai",
                1500,
                4.8,
                "6:00 AM",
                "11:00 PM",
                "Modern gym with strength and cardio equipment."
            ),

            (
                "PowerZone Gym",
                "Ghatkopar, Mumbai",
                1800,
                4.6,
                "6:00 AM",
                "10:00 PM",
                "Fitness centre with trainers and modern equipment."
            ),

            (
                "FitZone Studio",
                "Sion, Mumbai",
                1200,
                4.5,
                "7:00 AM",
                "10:00 PM",
                "Affordable gym suitable for beginners."
            )

        ]


        cursor.executemany("""
            INSERT INTO gyms
            (
                name,
                location,
                price,
                rating,
                opening_time,
                closing_time,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, gyms)


    connection.commit()

    connection.close()


# =========================================================
# RUN DATABASE SETUP
# =========================================================

if __name__ == "__main__":

    create_database()

    add_sample_gyms()

    print("Database updated successfully!")