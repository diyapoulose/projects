print(">>> FITBOT PRO app.py — ALL ROUTES ACTIVE <<<")

from flask import Flask, render_template, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
import sqlite3
from datetime import date, datetime, timedelta
from posture_engine import analyze_posture
import os

app = Flask(__name__)
app.secret_key = "fitbot-secret-key-12345"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def update_xp(user_id, amount, reason=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT xp, streak, last_active FROM profile WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return
    current_xp = row["xp"] if row["xp"] else 0
    current_streak = row["streak"] if row["streak"] else 0
    last_active = row["last_active"]
    today = date.today()
    if last_active:
        last_date = datetime.strptime(last_active, "%Y-%m-%d").date()
        diff = (today - last_date).days
        if diff == 1:
            current_streak += 1
        elif diff > 1:
            current_streak = 1
    else:
        current_streak = 1
    new_xp = current_xp + amount
    new_level = (new_xp // 200) + 1
    cursor.execute("""
        UPDATE profile SET xp=?, level=?, streak=?, last_active=? WHERE user_id=?
    """, (new_xp, new_level, current_streak, today, user_id))
    db.commit()

def has_onboarding(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM onboarding WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id="120192920106-8cp02ikflu97om9g1f17d3iaud6b5irk.apps.googleusercontent.com",
    client_secret="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",
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "email profile"},
    authorize_params={"prompt": "select_account"},
)

@app.route("/debug-routes")
def debug_routes():
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    return "<pre>" + "\n".join(sorted(routes)) + "</pre>"

@app.route("/")
def auth():
    return render_template("auth.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        if user:
            session["user_id"] = user["id"]
            session["user_email"] = email
            return redirect("/dashboard" if has_onboarding(user["id"]) else "/about")
        return render_template("login.html", error="Invalid email or password.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            return render_template("register.html", error="Please fill in all fields.")
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email=?", (email,))
        if cursor.fetchone():
            return render_template("register.html", error="An account with that email already exists.")
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?,?)", (email, password))
            db.commit()
        except Exception:
            return render_template("register.html", error="Registration failed. Please try again.")
        session["user_id"] = cursor.lastrowid
        session["user_email"] = email
        return redirect(url_for("about"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/google/login")
def google_login():
    return google.authorize_redirect(url_for("google_callback", _external=True))

@app.route("/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = google.get("userinfo").json()
    email = user_info["email"]
    google_id = user_info["id"]
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (email, google_id) VALUES (?,?)", (email, google_id))
        db.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user["id"]
    session["user_id"] = user_id
    session["user_email"] = email
    return redirect("/dashboard" if has_onboarding(user_id) else "/about")

@app.route("/about", methods=["GET", "POST"])
def about():
    if "user_id" not in session:
        return redirect("/")
    if request.method == "POST":
        db = get_db()
        cursor = db.cursor()
        uid = session["user_id"]
        cursor.execute("""
            INSERT OR REPLACE INTO onboarding
            (user_id, name, workout_place, intent, time_available, energy_level)
            VALUES (?,?,?,?,?,?)
        """, (uid, request.form.get("name",""), request.form.get("workout_place",""),
              request.form.get("intent",""), request.form.get("time_available",""),
              request.form.get("energy_level","")))
        cursor.execute("SELECT user_id FROM profile WHERE user_id=?", (uid,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE profile SET age=?,gender=?,height_cm=?,weight_kg=?,activity_level=?,goal=?
                WHERE user_id=?
            """, (request.form.get("age"), request.form.get("gender"),
                  request.form.get("height"), request.form.get("weight"),
                  request.form.get("activity"), request.form.get("intent"), uid))
        else:
            cursor.execute("""
                INSERT INTO profile (user_id,age,gender,height_cm,weight_kg,activity_level,goal)
                VALUES (?,?,?,?,?,?,?)
            """, (uid, request.form.get("age"), request.form.get("gender"),
                  request.form.get("height"), request.form.get("weight"),
                  request.form.get("activity"), request.form.get("intent")))
        db.commit()
        return redirect("/dashboard")
    return render_template("about.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT o.name, o.workout_place, o.intent, o.time_available, o.energy_level,
               p.age, p.gender, p.height_cm, p.weight_kg, p.activity_level, p.goal,
               p.steps_today, IFNULL(p.distance_today,0) as distance_today, IFNULL(p.xp,0) as xp, IFNULL(p.level,1) as level,
               IFNULL(p.streak,0) as streak,
               p.last_period_date, IFNULL(p.cycle_length,28) as cycle_length,
               IFNULL(p.period_length,5) as period_length,
               p.profile_pic
        FROM onboarding o LEFT JOIN profile p ON o.user_id=p.user_id
        WHERE o.user_id=?
    """, (session["user_id"],))
    user = cursor.fetchone()
    if not user:
        return redirect("/about")
    assistant_message = "You're on Level " + str(user["level"]) + " — keep pushing!"

    # ── Pre-compute period calendar data (server-side, no JS needed) ──────
    from datetime import date as dt_date, datetime as dt_datetime
    import calendar as cal_mod

    today = dt_date.today()
    cal_year  = today.year
    cal_month = today.month
    cal_month_name = today.strftime("%B %Y")

    last_period_date = user["last_period_date"]
    cycle_length     = user["cycle_length"] or 28
    period_length    = user["period_length"] or 5

    period_days_set  = set()
    fertile_days_set = set()

    if last_period_date:
        try:
            last = dt_datetime.strptime(last_period_date, "%Y-%m-%d").date()
            for offset in range(-2, 3):
                cycle_start = dt_date.fromordinal(last.toordinal() + offset * cycle_length)
                for d in range(period_length):
                    dd = dt_date.fromordinal(cycle_start.toordinal() + d)
                    if dd.year == cal_year and dd.month == cal_month:
                        period_days_set.add(dd.day)
                for d in range(10, 17):
                    dd = dt_date.fromordinal(cycle_start.toordinal() + d)
                    if dd.year == cal_year and dd.month == cal_month:
                        fertile_days_set.add(dd.day)
        except:
            pass

    # Build calendar grid rows: each cell = (day_num, classes)
    first_weekday = cal_mod.monthrange(cal_year, cal_month)[0]  # Mon=0
    first_weekday = (first_weekday + 1) % 7  # convert to Sun=0
    days_in_month = cal_mod.monthrange(cal_year, cal_month)[1]
    prev_days = cal_mod.monthrange(cal_year, cal_month - 1 if cal_month > 1 else 12)[1]

    cal_cells = []
    for i in range(first_weekday):
        cal_cells.append({"day": prev_days - first_weekday + 1 + i, "cls": "mc-day other-month"})
    for d in range(1, days_in_month + 1):
        cls = "mc-day"
        if d == today.day:          cls += " today"
        elif d in period_days_set:  cls += " period"
        elif d in fertile_days_set: cls += " fertile"
        cal_cells.append({"day": d, "cls": cls})
    while len(cal_cells) % 7 != 0:
        cal_cells.append({"day": len(cal_cells) - days_in_month - first_weekday + 1, "cls": "mc-day other-month"})

    # Week dots for current week
    week_day_labels = ["S","M","T","W","T","F","S"]
    today_dow = today.weekday()
    today_dow = (today_dow + 1) % 7  # Sun=0
    week_start_ord = today.toordinal() - today_dow
    week_dots = []
    for i in range(7):
        day = dt_date.fromordinal(week_start_ord + i)
        cls = "wdot"
        if i == today_dow: cls += " on"
        elif day.month == cal_month and day.day in period_days_set: cls += " on"
        elif day.month == cal_month and day.day in fertile_days_set: cls += " mid"
        week_dots.append({"label": week_day_labels[i], "cls": cls})

    # Phase label
    if last_period_date and period_days_set or fertile_days_set:
        try:
            last = dt_datetime.strptime(last_period_date, "%Y-%m-%d").date()
            days_since = (today - last).days % cycle_length
            if days_since < period_length:     phase_label = "🔴 Period phase"
            elif days_since < 13:              phase_label = "🌱 Follicular phase"
            elif days_since < 16:              phase_label = "✨ Ovulation window"
            else:                              phase_label = "🌙 Luteal phase"
        except:
            phase_label = "Cycle tracking active"
    else:
        phase_label = "Set up tracking →"

    return render_template("dashboard.html",
        assistant_message=assistant_message,
        cal_month_name=cal_month_name,
        cal_cells=cal_cells,
        week_dots=week_dots,
        phase_label=phase_label,
        **user)

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():
    if "user_id" not in session:
        return redirect("/")
    db = get_db()
    cursor = db.cursor()
    uid = session["user_id"]

    if request.method == "POST":
        # ── Profile pic upload ────────────────────────────────────────────
        pic_path = None
        if "profile_pic" in request.files:
            f = request.files["profile_pic"]
            if f and f.filename:
                import uuid, os
                ext = f.filename.rsplit(".", 1)[-1].lower()
                fname = f"{uid}_{uuid.uuid4().hex[:8]}.{ext}"
                save_dir = os.path.join(app.root_path, "static", "uploads", "profile_pics")
                os.makedirs(save_dir, exist_ok=True)
                f.save(os.path.join(save_dir, fname))
                pic_path = f"uploads/profile_pics/{fname}"

        # ── Helper: None if empty string ─────────────────────────────────
        def val(key):
            v = request.form.get(key, "").strip()
            return v if v else None

        # ── Upsert profile row ────────────────────────────────────────────
        cursor.execute("SELECT user_id FROM profile WHERE user_id=?", (uid,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute("""
                UPDATE profile SET
                    age            = COALESCE(?, age),
                    gender         = COALESCE(?, gender),
                    dob            = COALESCE(?, dob),
                    phone          = COALESCE(?, phone),
                    about          = COALESCE(?, about),
                    height_cm      = COALESCE(?, height_cm),
                    weight_kg      = COALESCE(?, weight_kg),
                    activity_level = COALESCE(?, activity_level),
                    goal           = COALESCE(?, goal),
                    health_notes   = COALESCE(?, health_notes),
                    profile_pic    = COALESCE(?, profile_pic)
                WHERE user_id = ?
            """, (val("age"), val("gender"), val("dob"), val("phone"),
                   val("about"), val("height"), val("weight"),
                   val("activity"), val("goal"), val("health_notes"),
                   pic_path, uid))
        else:
            cursor.execute("""
                INSERT INTO profile
                    (user_id, age, gender, dob, phone, about,
                     height_cm, weight_kg, activity_level, goal, health_notes, profile_pic)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (uid, val("age"), val("gender"), val("dob"), val("phone"),
                   val("about"), val("height"), val("weight"),
                   val("activity"), val("goal"), val("health_notes"), pic_path))

        # ── Update name in onboarding ─────────────────────────────────────
        if val("name"):
            cursor.execute("UPDATE onboarding SET name=? WHERE user_id=?", (val("name"), uid))

        db.commit()
        return redirect("/edit-profile?saved=1")

    # ── GET — load existing data ──────────────────────────────────────────
    cursor.execute("SELECT * FROM profile WHERE user_id=?", (uid,))
    profile = cursor.fetchone()
    cursor.execute("SELECT name FROM onboarding WHERE user_id=?", (uid,))
    onb = cursor.fetchone()
    name = onb["name"] if onb else ""
    saved = request.args.get("saved") == "1"
    return render_template("edit_profile.html", profile=profile, name=name, saved=saved)

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/about_app")
def about_app():
    return render_template("about_app.html")

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return {"reply": "Please log in first."}
    data     = request.json or {}
    message  = data.get("message", "").strip()
    history  = data.get("history", [])[-10:]   # keep last 10 turns
    user_ctx = data.get("user", {})
    if not message:
        return {"reply": "Ask me something!"}

    system = (
        "You are FitBot Coach, a knowledgeable and friendly fitness assistant built into the FitBot Pro app. "
        "You specialise in workout programming, exercise form, nutrition, diet, recovery, and general fitness. "
        "Keep answers clear, practical and concise — use short paragraphs or bullet points when helpful. "
        "You ONLY answer questions related to fitness, workouts, diet, nutrition, health, and recovery. "
        "If asked anything unrelated, politely redirect back to fitness topics. "
        f"The user's name is {user_ctx.get('name','there')}, "
        f"their goal is {user_ctx.get('goal','general fitness')}, "
        f"they are Level {user_ctx.get('level',1)} in the app. "
        "Personalise your advice to their goal when relevant."
    )

    messages = []
    for turn in history[:-1]:   # everything except the last (current) message
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    try:
        import google.generativeai as genai
        import os
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system
        )
        # Build chat history for Gemini format
        gemini_history = []
        for turn in history[:-1]:
            role = "user" if turn["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [turn["content"]]})
        chat = model.start_chat(history=gemini_history)
        resp = chat.send_message(message)
        reply = resp.text
    except Exception as e:
        reply = f"Sorry, I couldn't connect right now. ({str(e)[:80]})"

    return {"reply": reply}

@app.route("/learn")
def learn():
    if "user_id" not in session:
        return redirect("/")
    return render_template("learn.html")

@app.route("/xp-status")
def xp_status():
    if "user_id" not in session:
        return {"xp": 0, "level": 1, "streak": 0}
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT IFNULL(xp,0) as xp, IFNULL(level,1) as level, IFNULL(streak,0) as streak
        FROM profile WHERE user_id=?
    """, (session["user_id"],))
    row = cursor.fetchone()
    if row:
        return {"xp": row["xp"], "level": row["level"], "streak": row["streak"]}
    return {"xp": 0, "level": 1, "streak": 0}

@app.route("/diet")
def diet():
    if "user_id" not in session:
        return redirect("/")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM profile WHERE user_id=?", (session["user_id"],))
    profile = cursor.fetchone()
    if not profile:
        return redirect("/edit-profile")
    height_cm = profile["height_cm"] or 170
    weight = profile["weight_kg"] or 65
    height_m = height_cm / 100
    bmi = round(weight / (height_m ** 2), 1)
    base_calories = 22 * weight
    daily_calories = int(base_calories * 1.4)
    goal = profile["goal"] or ""
    if goal == "Fat loss":
        daily_calories -= 300
        protein_per_kg = 1.8
    elif goal == "Strength":
        daily_calories += 300
        protein_per_kg = 2.2
    else:
        protein_per_kg = 1.5
    intensity = session.get("today_intensity", 2)
    if intensity == 3:
        daily_calories += 150
    elif intensity == 1:
        daily_calories -= 100
    protein_grams = round(weight * protein_per_kg)
    protein_calories = protein_grams * 4
    fat_calories = int(daily_calories * 0.25)
    fat_grams = round(fat_calories / 9)
    carb_grams = round((daily_calories - protein_calories - fat_calories) / 4)
    goal_key = "fat_loss" if goal == "Fat loss" else "strength" if goal == "Strength" else "general"
    cursor.execute("SELECT title, youtube_id, meal_type FROM diet_videos WHERE goal=? ORDER BY RANDOM() LIMIT 4", (goal_key,))
    video_rows = cursor.fetchall()
    if not video_rows:
        cursor.execute("SELECT title, youtube_id, meal_type FROM diet_videos WHERE goal='general' ORDER BY RANDOM() LIMIT 4")
        video_rows = cursor.fetchall()
    videos = [{"title": r["title"], "id": r["youtube_id"], "meal_type": r["meal_type"]} for r in video_rows]
    return render_template("diet.html", bmi=bmi, calories=daily_calories,
                           goal=goal or "General", protein=protein_grams,
                           carbs=carb_grams, fats=fat_grams, videos=videos)

@app.route("/save-walk", methods=["POST"])
def save_walk():
    if "user_id" not in session:
        return {"success": False}
    data = request.json
    steps = int(data.get("steps", 0))
    calories = float(data.get("calories", 0))
    distance = float(data.get("distance", 0))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE profile
        SET steps_today=IFNULL(steps_today,0)+?,
            calories_today=IFNULL(calories_today,0)+?,
            distance_today=IFNULL(distance_today,0)+?
        WHERE user_id=?
    """, (steps, calories, distance, session["user_id"]))
    db.commit()
    xp_from_run = steps // 100
    if xp_from_run > 0:
        update_xp(session["user_id"], xp_from_run, "run")
    return {"success": True}

@app.route("/run")
def run():
    if "user_id" not in session:
        return redirect("/")
    return render_template("run.html")

@app.route("/period", methods=["GET", "POST"])
def period():
    if "user_id" not in session:
        return redirect("/")
    db = get_db()
    cursor = db.cursor()
    if request.method == "POST":
        cursor.execute("""
            UPDATE profile SET last_period_date=?,cycle_length=?,period_length=?
            WHERE user_id=?
        """, (request.form["last_period_date"], request.form["cycle_length"],
              request.form["period_length"], session["user_id"]))
        db.commit()
    cursor.execute("""
        SELECT last_period_date,cycle_length,period_length FROM profile WHERE user_id=?
    """, (session["user_id"],))
    data = cursor.fetchone()
    phase = message = notification = None
    if data and data["last_period_date"]:
        last_date = datetime.strptime(data["last_period_date"], "%Y-%m-%d")
        today = datetime.today()
        cycle_length = data["cycle_length"] or 28
        period_length = data["period_length"] or 5
        days_passed = (today - last_date).days
        cycle_day = days_passed % cycle_length
        if cycle_day < period_length:
            phase = "Menstrual"
            message = "You are currently on your period. Light workouts recommended."
            notification = "You're currently on your period."
        next_period = last_date + timedelta(days=cycle_length)
        days_left = (next_period - today).days
        if days_left == 0:
            notification = "Your period is expected today."
        elif days_left == 1:
            notification = "Your period may start tomorrow."
        elif days_left == 2:
            notification = "Your period is likely in 2 days."
    return render_template("period.html",
                           last_period_date=data["last_period_date"] if data else None,
                           cycle_length=data["cycle_length"] if data else 28,
                           period_length=data["period_length"] if data else 5,
                           phase=phase, message=message, notification=notification)

@app.route("/workout")
def workout():
    if "user_id" not in session:
        return redirect("/")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT intent,energy_level,time_available FROM onboarding WHERE user_id=?",
                   (session["user_id"],))
    user = cursor.fetchone()
    if not user:
        return redirect("/about")
    energy = user["energy_level"]
    cursor.execute("""
        SELECT gender,last_period_date,cycle_length,period_length FROM profile WHERE user_id=?
    """, (session["user_id"],))
    profile = cursor.fetchone()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    cursor.execute("SELECT completed FROM workout_logs WHERE user_id=? AND date=?",
                   (session["user_id"], yesterday))
    y_log = cursor.fetchone()
    missed_yesterday = not y_log or y_log["completed"] == 0
    cycle_modifier = 0
    if profile and profile["gender"] == "Female" and profile["last_period_date"]:
        last_date = datetime.strptime(profile["last_period_date"], "%Y-%m-%d")
        today_dt = datetime.today()
        cycle_length = profile["cycle_length"] or 28
        period_length = profile["period_length"] or 5
        days_passed = (today_dt - last_date).days
        cycle_day = days_passed % cycle_length
        if cycle_day < period_length:
            cycle_modifier = -1
        elif cycle_day < 14:
            cycle_modifier = +1
        elif cycle_day < 21:
            cycle_modifier = +2
        else:
            cycle_modifier = -1
    if missed_yesterday:
        base_intensity = 1
    elif energy == "High":
        base_intensity = 3
    elif energy == "Low":
        base_intensity = 1
    else:
        base_intensity = 2
    final_intensity = max(1, min(3, base_intensity + cycle_modifier))
    if final_intensity == 1:
        difficulty, main_count = "easy", 5
    elif final_intensity == 2:
        difficulty, main_count = "easy", 7
    else:
        difficulty, main_count = "medium", 10
    # Get user goal for targeted exercise selection
    cursor.execute("SELECT goal FROM profile WHERE user_id=?", (session["user_id"],))
    prof = cursor.fetchone()
    user_goal = "general"
    if prof and prof["goal"]:
        g = prof["goal"].lower()
        if "fat" in g: user_goal = "fat_loss"
        elif "strength" in g: user_goal = "strength"

    # Get today's plan day (Mon=0 -> day_number=1)
    from datetime import date as _date
    day_num = _date.today().weekday() + 1  # 1=Mon ... 7=Sun

    cursor.execute("SELECT id, focus FROM workout_plan WHERE day_number=? AND goal=?", (day_num, user_goal))
    plan = cursor.fetchone()

    if plan and "Rest" not in plan["focus"]:
        # Pull exercises in order from this day's plan
        cursor.execute("""
            SELECT e.* FROM exercises e
            JOIN plan_exercises pe ON pe.exercise_id = e.id
            WHERE pe.plan_id = ?
            ORDER BY pe.order_num
        """, (plan["id"],))
        all_ex = cursor.fetchall()
        warmup   = [e for e in all_ex if e["phase"] == "warmup"]
        main     = [e for e in all_ex if e["phase"] == "main"]
        cooldown = [e for e in all_ex if e["phase"] == "cooldown"]
        day_focus = plan["focus"]
        rest_day = False
    else:
        # Rest day or no plan — show light recovery
        cursor.execute("SELECT * FROM exercises WHERE phase='warmup' ORDER BY RANDOM() LIMIT 4")
        warmup = cursor.fetchall()
        cursor.execute("SELECT * FROM exercises WHERE phase='main' AND difficulty='easy' ORDER BY RANDOM() LIMIT 4")
        main = cursor.fetchall()
        cursor.execute("SELECT * FROM exercises WHERE phase='cooldown' ORDER BY RANDOM() LIMIT 4")
        cooldown = cursor.fetchall()
        day_focus = plan["focus"] if plan else "Rest Day"
        rest_day = True

    session["today_intensity"] = final_intensity
    return render_template("workout.html", warmup=warmup, main=main, cooldown=cooldown,
                           day_focus=day_focus, rest_day=rest_day, day_num=day_num)

@app.route("/complete-workout", methods=["POST"])
def complete_workout():
    if "user_id" not in session:
        return {"success": False}
    today = date.today().isoformat()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM workout_logs WHERE user_id=? AND date=?",
                   (session["user_id"], today))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO workout_logs (user_id,date,completed) VALUES (?,?,1)",
                       (session["user_id"], today))
        update_xp(session["user_id"], 40, "workout")
        db.commit()
    return {"success": True}

@app.route("/checklist", methods=["GET", "POST"])
def checklist():
    if "user_id" not in session:
        return redirect("/")
    today = date.today().isoformat()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM habits WHERE user_id=?", (session["user_id"],))
    if cursor.fetchone()[0] == 0:
        for name, pts in [("Drink enough water",10),("Stretch or mobility",5),
                          ("Move your body",10),("Sleep on time",10),("Avoid junk food",5)]:
            cursor.execute("INSERT INTO habits (user_id,name,points,is_default) VALUES (?,?,?,1)",
                           (session["user_id"], name, pts))
        db.commit()
    if request.method == "POST":
        cursor.execute("INSERT INTO habits (user_id,name,points) VALUES (?,?,?)",
                       (session["user_id"], request.form["name"], request.form["points"]))
        db.commit()
        return redirect("/checklist")
    cursor.execute("""
        SELECT h.id, h.name, h.points, IFNULL(d.completed,0) completed
        FROM habits h
        LEFT JOIN daily_habits d ON h.id=d.habit_id AND d.date=?
        WHERE h.user_id=?
    """, (today, session["user_id"]))
    habits = cursor.fetchall()
    total = sum(h["points"] for h in habits if h["completed"])
    return render_template("checklist.html", habits=habits, total=total,
                           completed_count=sum(1 for h in habits if h["completed"]),
                           total_count=len(habits))

@app.route("/toggle-habit/<int:habit_id>", methods=["POST"])
def toggle_habit(habit_id):
    if "user_id" not in session:
        return {"success": False, "completed": 0, "xp": 0}
    today = date.today().isoformat()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT points FROM habits WHERE id=?", (habit_id,))
    habit = cursor.fetchone()
    habit_points = habit["points"] if habit else 0
    cursor.execute("SELECT id,completed FROM daily_habits WHERE habit_id=? AND date=?",
                   (habit_id, today))
    row = cursor.fetchone()
    if row:
        new_state = 0 if row["completed"] else 1
        cursor.execute("UPDATE daily_habits SET completed=? WHERE id=?", (new_state, row["id"]))
    else:
        new_state = 1
        cursor.execute("INSERT INTO daily_habits (habit_id,date,completed) VALUES (?,?,1)",
                       (habit_id, today))
    xp_gained = 0
    if new_state == 1:
        xp_gained = habit_points
        db.commit()
        update_xp(session["user_id"], xp_gained, "habit")
    else:
        db.commit()
    return {"success": True, "completed": new_state, "xp": xp_gained}

@app.route("/form-check/<exercise_type>")
def form_check(exercise_type):
    feedback = analyze_posture(exercise_type)
    return {"message": feedback}

# START SERVER — always keep this last
if __name__ == "__main__":
    app.run(debug=True)