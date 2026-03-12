import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT,
    google_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE onboarding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    workout_place TEXT,
    intent TEXT,
    time_available TEXT,
    energy_level TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS profile (
    user_id INTEGER PRIMARY KEY,

    age INTEGER,
    gender TEXT,
    dob TEXT,
    phone TEXT,
    about TEXT,
    profile_pic TEXT,

    height_cm REAL,
    weight_kg REAL,

    activity_level TEXT,
    health_notes TEXT,

    goal TEXT,

    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    streak INTEGER DEFAULT 0,
    last_active TEXT,
    steps_today INTEGER DEFAULT 0,
    calories_today REAL DEFAULT 0,
    distance_today REAL DEFAULT 0,

    last_period_date TEXT,
    cycle_length INTEGER DEFAULT 28,
    period_length INTEGER DEFAULT 5,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    points INTEGER,
    is_default INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER,
    date TEXT,
    completed INTEGER DEFAULT 0,
    FOREIGN KEY (habit_id) REFERENCES habits(id)
);

""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS diet_profile (
    user_id INTEGER PRIMARY KEY,
    food_preference TEXT,
    meals_per_day INTEGER,
    allergies TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);


""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    completed INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

cursor.execute("""

CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phase TEXT,
    category TEXT,
    difficulty TEXT,
    goal TEXT,
    duration INTEGER,
    youtube_id TEXT,
    sets INTEGER,
    reps INTEGER,
    rest_seconds INTEGER,
    type TEXT
);

""")
# ── NEW TABLES for diet videos and workout plan ──────────────────────────────
cursor.execute("""
CREATE TABLE IF NOT EXISTS diet_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal TEXT,
    title TEXT,
    youtube_id TEXT,
    meal_type TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS workout_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_number INTEGER,
    day_name TEXT,
    focus TEXT,
    goal TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS plan_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER,
    exercise_id INTEGER,
    order_num INTEGER,
    FOREIGN KEY (plan_id) REFERENCES workout_plan(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
""")

conn.commit()
conn.close()

print("Database created successfully")