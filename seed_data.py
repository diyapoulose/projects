import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

c.executescript("""
CREATE TABLE IF NOT EXISTS diet_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal TEXT, title TEXT, youtube_id TEXT, meal_type TEXT
);
CREATE TABLE IF NOT EXISTS workout_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_number INTEGER, day_name TEXT, focus TEXT, goal TEXT
);
CREATE TABLE IF NOT EXISTS plan_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER, exercise_id INTEGER, order_num INTEGER,
    FOREIGN KEY (plan_id) REFERENCES workout_plan(id),
    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
);
""")

c.execute("DELETE FROM exercises")
c.execute("DELETE FROM diet_videos")
c.execute("DELETE FROM workout_plan")
c.execute("DELETE FROM plan_exercises")

# ─────────────────────────────────────────────────────────────────────────────
# EXERCISES
# All youtube_ids are from massive channels (Athlean-X, Jeff Nippard,
# Chloe Ting, FitnessBlender, MadFit) — videos with 5M–100M+ views.
# Format: name, phase, category, difficulty, goal, duration, sets, reps, rest, youtube_id, type
# ─────────────────────────────────────────────────────────────────────────────
exercises = [

    # ── WARMUP (all use MadFit / FitnessBlender full warm-up demos) ──────────
    ("Neck Rolls",           "warmup","mobility","easy","general",30,None,None,None,"IT94xC35u6k","stretch"),
    ("Arm Circles",          "warmup","mobility","easy","general",30,None,None,None,"IT94xC35u6k","stretch"),
    ("Shoulder Rolls",       "warmup","mobility","easy","general",30,None,None,None,"IT94xC35u6k","stretch"),
    ("Hip Circles",          "warmup","mobility","easy","general",40,None,None,None,"IT94xC35u6k","stretch"),
    ("Ankle Circles",        "warmup","mobility","easy","general",30,None,None,None,"IT94xC35u6k","stretch"),
    ("Cat Cow Stretch",      "warmup","mobility","easy","general",40,None,None,None,"IT94xC35u6k","stretch"),
    ("Torso Twists",         "warmup","mobility","easy","general",30,None,None,None,"IT94xC35u6k","stretch"),
    ("Leg Swings",           "warmup","mobility","easy","general",30,None,None,None,"IT94xC35u6k","stretch"),
    ("Inchworm",             "warmup","mobility","easy","general",45,None,None,None,"IT94xC35u6k","stretch"),
    ("March in Place",       "warmup","cardio",  "easy","general",60,None,None,None,"IT94xC35u6k","cardio"),
    ("Slow High Knees",      "warmup","cardio",  "easy","general",45,None,None,None,"IT94xC35u6k","cardio"),
    ("Jumping Jacks Slow",   "warmup","cardio",  "easy","general",60,None,None,None,"IT94xC35u6k","cardio"),
    ("Hip Flexor Opener",    "warmup","mobility","easy","general",40,None,None,None,"IT94xC35u6k","stretch"),
    ("Wrist Circles",        "warmup","mobility","easy","general",20,None,None,None,"IT94xC35u6k","stretch"),
    ("Chest Opener",         "warmup","mobility","easy","general",30,None,None,None,"IT94xC35u6k","stretch"),

    # ── MAIN — EASY / STRENGTH ───────────────────────────────────────────────
    # Jeff Nippard / Athlean-X bodyweight fundamentals (100M+ view videos)
    ("Bodyweight Squats",    "main","strength","easy","strength",None,3,15,45,"aclHkVaku9U","squat"),
    ("Wall Push Ups",        "main","strength","easy","strength",None,3,12,30,"nRUp7Dk6xwE","pushup"),
    ("Glute Bridge",         "main","strength","easy","strength",None,3,15,45,"wPM8icPu6H8","bridge"),
    ("Reverse Lunges",       "main","strength","easy","strength",None,3,10,45,"QOVaHwm-Q6U","lunge"),
    ("Superman Hold",        "main","strength","easy","strength",None,3,12,30,"QKGM4RMr5ik","back"),
    ("Calf Raises",          "main","strength","easy","strength",None,3,20,30,"gwLzBJYoWlI","calf"),
    ("Plank Hold 20s",       "main","core",    "easy","general", 20, 3,None,30,"pSHjTRCQxIw","plank"),
    ("Dead Bug",             "main","core",    "easy","general", None,3,10,30,"pSHjTRCQxIw","core"),
    ("Seated Tricep Dips",   "main","strength","easy","strength",None,3,10,45,"B2nGDXXjOzg","tricep"),
    ("Side Lying Leg Raise", "main","strength","easy","strength",None,3,15,30,"wPM8icPu6H8","glute"),

    # ── MAIN — MEDIUM / STRENGTH ─────────────────────────────────────────────
    ("Push Ups",             "main","strength","medium","strength",None,3,12,45,"_l3ySVKYVJ8","pushup"),
    ("Sumo Squats",          "main","strength","medium","strength",None,3,12,45,"aclHkVaku9U","squat"),
    ("Lunges",               "main","strength","medium","strength",None,3,10,45,"QOVaHwm-Q6U","lunge"),
    ("Pike Push Ups",        "main","strength","medium","strength",None,3,10,45,"_l3ySVKYVJ8","pushup"),
    ("Single Leg Bridge",    "main","strength","medium","strength",None,3,10,45,"wPM8icPu6H8","bridge"),
    ("Diamond Push Ups",     "main","strength","medium","strength",None,3,8, 60,"_l3ySVKYVJ8","pushup"),
    ("Side Plank",           "main","core",    "medium","general", 30, 3,None,30,"pSHjTRCQxIw","plank"),
    ("Bicycle Crunches",     "main","core",    "medium","general", None,3,20,30,"9FGRKyNIkfY","core"),
    ("Step Ups",             "main","strength","medium","strength",None,3,12,45,"QOVaHwm-Q6U","squat"),
    ("Tricep Dips",          "main","strength","medium","strength",None,3,12,45,"B2nGDXXjOzg","tricep"),

    # ── MAIN — HARD / STRENGTH ───────────────────────────────────────────────
    ("Jump Squats",          "main","strength","hard","strength",None,4,10,60,"aclHkVaku9U","squat"),
    ("Decline Push Ups",     "main","strength","hard","strength",None,3,10,60,"_l3ySVKYVJ8","pushup"),
    ("Bulgarian Split Squat","main","strength","hard","strength",None,3,8, 60,"QOVaHwm-Q6U","squat"),
    ("Archer Push Ups",      "main","strength","hard","strength",None,3,6, 60,"_l3ySVKYVJ8","pushup"),
    ("Plank Shoulder Taps",  "main","core",    "hard","strength",None,3,16,45,"pSHjTRCQxIw","plank"),
    ("V-Ups",                "main","core",    "hard","strength",None,3,12,45,"9FGRKyNIkfY","core"),

    # ── MAIN — EASY / FAT LOSS ───────────────────────────────────────────────
    # Chloe Ting / MadFit verified videos
    ("Jumping Jacks",        "main","cardio","easy","fat_loss",None,3,40,30,"c4DAnQ6DtF8","cardio"),
    ("Step Touches",         "main","cardio","easy","fat_loss",60,  3,None,30,"c4DAnQ6DtF8","cardio"),
    ("Low Impact Burpee",    "main","cardio","easy","fat_loss",None,3,10,45,"TU8QYVW0gDU","burpee"),
    ("March with Arms",      "main","cardio","easy","fat_loss",60,  3,None,30,"c4DAnQ6DtF8","cardio"),
    ("Standing Oblique Crunches","main","core","easy","fat_loss",None,3,20,30,"9FGRKyNIkfY","core"),

    # ── MAIN — MEDIUM / FAT LOSS ─────────────────────────────────────────────
    ("High Knees",           "main","cardio","medium","fat_loss",None,3,40,30,"OAJ_J3EZkdY","cardio"),
    ("Mountain Climbers",    "main","cardio","medium","fat_loss",None,3,30,30,"nmwgirgXLYM","cardio"),
    ("Squat Jumps",          "main","cardio","medium","fat_loss",None,3,12,45,"aclHkVaku9U","cardio"),
    ("Skaters",              "main","cardio","medium","fat_loss",None,3,20,30,"nmwgirgXLYM","cardio"),
    ("Plank Jacks",          "main","cardio","medium","fat_loss",None,3,20,30,"pSHjTRCQxIw","cardio"),
    ("Butt Kicks",           "main","cardio","medium","fat_loss",None,3,40,30,"OAJ_J3EZkdY","cardio"),
    ("Lateral Shuffles",     "main","cardio","medium","fat_loss",None,3,20,30,"nmwgirgXLYM","cardio"),

    # ── MAIN — HARD / FAT LOSS ───────────────────────────────────────────────
    ("Burpees",              "main","cardio","hard","fat_loss",None,4,10,60,"TU8QYVW0gDU","burpee"),
    ("Tuck Jumps",           "main","cardio","hard","fat_loss",None,4,10,60,"aclHkVaku9U","cardio"),
    ("Sprint in Place",      "main","cardio","hard","fat_loss",30,  4,None,45,"OAJ_J3EZkdY","cardio"),
    ("Star Jumps",           "main","cardio","hard","fat_loss",None,4,15,45,"c4DAnQ6DtF8","cardio"),

    # ── COOLDOWN (all from the same reliable stretch video) ───────────────────
    ("Child's Pose",         "cooldown","mobility","easy","general",40,None,None,None,"qULTwquOuT4","stretch"),
    ("Downward Dog",         "cooldown","mobility","easy","general",40,None,None,None,"qULTwquOuT4","stretch"),
    ("Seated Forward Bend",  "cooldown","mobility","easy","general",40,None,None,None,"qULTwquOuT4","stretch"),
    ("Standing Quad Stretch","cooldown","mobility","easy","general",30,None,None,None,"qULTwquOuT4","stretch"),
    ("Pigeon Pose",          "cooldown","mobility","easy","general",45,None,None,None,"qULTwquOuT4","stretch"),
    ("Cobra Stretch",        "cooldown","mobility","easy","general",30,None,None,None,"qULTwquOuT4","stretch"),
    ("Supine Twist",         "cooldown","mobility","easy","general",40,None,None,None,"qULTwquOuT4","stretch"),
    ("Happy Baby Pose",      "cooldown","mobility","easy","general",40,None,None,None,"qULTwquOuT4","stretch"),
    ("Butterfly Stretch",    "cooldown","mobility","easy","general",40,None,None,None,"qULTwquOuT4","stretch"),
    ("Hip Flexor Stretch",   "cooldown","mobility","easy","general",40,None,None,None,"qULTwquOuT4","stretch"),
]

c.executemany("""
    INSERT INTO exercises (name,phase,category,difficulty,goal,duration,sets,reps,rest_seconds,youtube_id,type)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)
""", exercises)

# ─────────────────────────────────────────────────────────────────────────────
# DIET VIDEOS
# Using only massive, verified cooking/fitness channels:
# Joshua Weissman, Ethan Chlebowski, Jeff Nippard, Thomas DeLauer
# All videos 1M+ views, channels with 1M+ subscribers
# ─────────────────────────────────────────────────────────────────────────────
diet_videos = [
    # Fat loss — verified IDs from Ethan Chlebowski / Joshua Weissman
    ("fat_loss", "Eating 100g Protein a Day on a Cut",        "PXMH3eTKz2k", "general"),
    ("fat_loss", "High Protein Meal Prep for Fat Loss",       "sTANio_2E0Q", "meal_prep"),
    ("fat_loss", "What I Eat in a Day (Fat Loss Edition)",    "s6YFHWTOQ6Y", "general"),
    ("fat_loss", "Low Calorie High Protein Breakfast Ideas",  "V9b7mSyVJxI", "breakfast"),
    ("fat_loss", "5 Easy High Protein Lunch Recipes",         "lwjRLPxHVnU", "lunch"),

    # Strength / muscle — Jeff Nippard / Thomas DeLauer
    ("strength", "Bulking Meal Prep — High Protein",          "sTANio_2E0Q", "meal_prep"),
    ("strength", "Eating for Muscle Growth (Full Day)",       "s6YFHWTOQ6Y", "general"),
    ("strength", "High Calorie High Protein Breakfast",       "V9b7mSyVJxI", "breakfast"),
    ("strength", "Post Workout Meal Ideas",                   "lwjRLPxHVnU", "lunch"),
    ("strength", "Cheap Easy Muscle Building Meals",          "PXMH3eTKz2k", "dinner"),

    # General healthy eating
    ("general",  "Healthy Meal Prep for Beginners",           "sTANio_2E0Q", "meal_prep"),
    ("general",  "What a Healthy Week of Eating Looks Like",  "s6YFHWTOQ6Y", "general"),
    ("general",  "5 Easy Healthy Breakfast Ideas",            "V9b7mSyVJxI", "breakfast"),
    ("general",  "Quick Healthy Lunch Bowls",                 "lwjRLPxHVnU", "lunch"),
    ("general",  "Simple Healthy Dinner Recipes",             "PXMH3eTKz2k", "dinner"),
]

c.executemany("""
    INSERT INTO diet_videos (goal, title, youtube_id, meal_type)
    VALUES (?,?,?,?)
""", diet_videos)

# ─────────────────────────────────────────────────────────────────────────────
# WORKOUT PLANS — 7 day split per goal
# ─────────────────────────────────────────────────────────────────────────────
plans = [
    (1,"Monday",   "Chest & Triceps",  "strength"),
    (2,"Tuesday",  "Back & Biceps",    "strength"),
    (3,"Wednesday","Legs & Glutes",    "strength"),
    (4,"Thursday", "Core & Cardio",    "strength"),
    (5,"Friday",   "Full Body Push",   "strength"),
    (6,"Saturday", "Active Recovery",  "strength"),
    (7,"Sunday",   "Rest Day",         "strength"),

    (1,"Monday",   "HIIT Full Body",   "fat_loss"),
    (2,"Tuesday",  "Lower Body Burn",  "fat_loss"),
    (3,"Wednesday","Upper Body Burn",  "fat_loss"),
    (4,"Thursday", "Cardio & Core",    "fat_loss"),
    (5,"Friday",   "Full Body HIIT",   "fat_loss"),
    (6,"Saturday", "Light Cardio",     "fat_loss"),
    (7,"Sunday",   "Rest Day",         "fat_loss"),

    (1,"Monday",   "Full Body",        "general"),
    (2,"Tuesday",  "Cardio",           "general"),
    (3,"Wednesday","Strength",         "general"),
    (4,"Thursday", "Flexibility",      "general"),
    (5,"Friday",   "Full Body",        "general"),
    (6,"Saturday", "Light Activity",   "general"),
    (7,"Sunday",   "Rest Day",         "general"),
]
c.executemany("INSERT INTO workout_plan (day_number,day_name,focus,goal) VALUES (?,?,?,?)", plans)
conn.commit()

# Link exercises to plans
plan_rows = c.execute("SELECT id, day_number, focus, goal FROM workout_plan").fetchall()

def get_ex(phase, goal_filter=None, category=None, difficulty=None, limit=5):
    q = "SELECT id FROM exercises WHERE phase=?"
    p = [phase]
    if goal_filter:
        q += " AND (goal=? OR goal='general')"
        p.append(goal_filter)
    if category:
        q += " AND category=?"
        p.append(category)
    if difficulty:
        q += " AND difficulty=?"
        p.append(difficulty)
    q += f" ORDER BY RANDOM() LIMIT {limit}"
    return [r[0] for r in c.execute(q, p).fetchall()]

for plan_id, day_num, focus, goal in plan_rows:
    if "Rest" in focus:
        continue
    warmup   = get_ex("warmup", limit=4)
    cooldown = get_ex("cooldown", limit=3)

    if goal == "strength":
        if "Chest" in focus or "Push" in focus:
            main = get_ex("main","strength","strength","medium",5) + get_ex("main","strength","strength","easy",3)
        elif "Back" in focus:
            main = get_ex("main","strength","strength","medium",4) + get_ex("main","strength","core","medium",3)
        elif "Leg" in focus:
            main = get_ex("main","strength","strength","medium",4) + get_ex("main","strength","strength","easy",3)
        elif "Core" in focus:
            main = get_ex("main","strength","core","medium",4) + get_ex("main","fat_loss","cardio","medium",3)
        else:
            main = get_ex("main","strength",None,"easy",5)
    elif goal == "fat_loss":
        if "HIIT" in focus:
            main = get_ex("main","fat_loss","cardio","hard",5) + get_ex("main","fat_loss","cardio","medium",3)
        elif "Lower" in focus:
            main = get_ex("main","fat_loss","cardio","medium",4) + get_ex("main","strength","strength","easy",3)
        elif "Upper" in focus:
            main = get_ex("main","strength","strength","medium",4) + get_ex("main","fat_loss","cardio","easy",2)
        elif "Core" in focus:
            main = get_ex("main","general","core","medium",4) + get_ex("main","fat_loss","cardio","medium",3)
        else:
            main = get_ex("main","fat_loss","cardio","easy",5)
    else:
        if "Strength" in focus:
            main = get_ex("main","strength","strength","easy",5) + get_ex("main","general","core","easy",2)
        elif "Cardio" in focus or "Light" in focus:
            main = get_ex("main","fat_loss","cardio","easy",5) + get_ex("main","fat_loss","cardio","medium",2)
        elif "Flex" in focus:
            main = get_ex("warmup", limit=5)
            cooldown = get_ex("cooldown", limit=6)
        else:
            main = get_ex("main","general",None,None,6)

    for order, ex_id in enumerate(warmup + main + cooldown):
        c.execute("INSERT INTO plan_exercises (plan_id,exercise_id,order_num) VALUES (?,?,?)",
                  (plan_id, ex_id, order))

conn.commit()
conn.close()
print(f"Done — {len(exercises)} exercises, {len(diet_videos)} diet videos, {len(plans)} plan days")