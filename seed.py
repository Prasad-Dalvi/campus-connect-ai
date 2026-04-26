# seed.py — Seed database with demo data for CampusConnect

from datetime import datetime, timedelta
import random

COLLEGES = [
    ("IIT Bombay",      "Mumbai",       19.1334, 72.9133),
    ("IIT Delhi",       "New Delhi",    28.5450, 77.1926),
    ("IIT Madras",      "Chennai",      12.9916, 80.2336),
    ("IIT Kharagpur",   "Kharagpur",    22.3149, 87.3105),
    ("BITS Pilani",     "Pilani",       28.3670, 75.5882),
    ("NIT Trichy",      "Tiruchirappalli", 10.7605, 78.8083),
    ("VIT Vellore",     "Vellore",      12.9690, 79.1555),
    ("Pune University", "Pune",         18.5204, 73.8567),
    ("Delhi University","New Delhi",    28.6879, 77.2147),
    ("Jadavpur Univ",   "Kolkata",      22.4988, 88.3714),
]

FIRST_NAMES = [
    "Aarav","Arjun","Vivaan","Aditya","Vihaan","Rohan","Siddharth","Karan",
    "Rahul","Vikram","Ananya","Priya","Divya","Sneha","Pooja","Riya","Meera",
    "Kavya","Ishaan","Dev","Tara","Nisha","Aisha","Zara","Krishna","Manav",
    "Yash","Harsh","Nikhil","Varun","Akash","Shivam","Kunal","Mohit","Gaurav",
    "Dhruv","Ritesh","Aakash","Chirag","Parth","Isha","Neha","Shruti","Aditi",
    "Bhavya","Tanvi","Simran","Pallavi","Swati","Anjali",
]

LAST_NAMES = [
    "Sharma","Verma","Gupta","Singh","Kumar","Patel","Shah","Mehta","Joshi",
    "Nair","Reddy","Rao","Iyer","Pillai","Menon","Bose","Ghosh","Das","Roy",
    "Chatterjee","Mishra","Pandey","Tiwari","Dubey","Yadav","Malhotra","Kapoor",
    "Agarwal","Bansal","Choudhary",
]

SKILLS_POOL = [
    "Communication","Marketing","Social Media","Content Creation","Leadership",
    "Event Management","Public Speaking","Photography","Video Editing","Branding",
    "Networking","Writing","Design","Analytics","Sales",
]

TASK_TEMPLATES = [
    ("Share a Campus Story",         "Post an engaging story about life at your campus on Instagram or LinkedIn.",     50),
    ("Host a Mini Workshop",         "Organise a 30-min workshop for 10+ students on any skill.",                    100),
    ("Recruit 3 New Members",        "Refer 3 friends to join CampusConnect and get them registered.",               150),
    ("Create a Reel",                "Make a 30-second campus reel showcasing your college culture.",                 75),
    ("Write a Blog Post",            "Publish a 500-word blog post about student life and tag CampusConnect.",         60),
    ("LinkedIn Post",                "Share a professional post about your CampusConnect journey on LinkedIn.",        40),
    ("Campus Survey",                "Collect 20+ responses to our campus engagement survey.",                        80),
    ("Instagram Takeover",           "Run a one-day Instagram story takeover for the CampusConnect account.",        120),
    ("Feedback Collection",          "Gather detailed feedback from 15 students about campus services.",               70),
    ("Event Coverage",               "Photograph or video a campus event and submit 10+ quality shots.",              90),
    ("Peer Referral Campaign",       "Run a referral drive and bring 5 new sign-ups in one week.",                   130),
    ("Monthly Report",               "Submit a detailed monthly engagement report for your college chapter.",          85),
    ("Social Media Audit",           "Audit your college's social media and provide a 1-page recommendation.",        65),
    ("Mentor a Junior",              "Spend 1 hour mentoring a junior ambassador.",                                    55),
    ("Community Poll",               "Create and share a poll that gets 50+ responses.",                              45),
    ("Podcast Appearance",           "Appear on any podcast or YouTube channel representing CampusConnect.",          110),
    ("Newsletter Feature",           "Get featured in your college newsletter with a CampusConnect mention.",          70),
    ("Data Collection Drive",        "Collect structured data about 30+ students' career aspirations.",               95),
    ("Collaboration Post",           "Collaborate with another ambassador on a joint post or project.",               80),
    ("Video Testimonial",            "Record a 60-second video testimonial about your CampusConnect experience.",     60),
    ("Flash Mob / Event",            "Organise a surprise event or flash mob on campus.",                            140),
    ("Campus Map Contribution",      "Submit geo-tagged activity photos from your campus location.",                   35),
    ("Skill Showcase",               "Demonstrate a skill live (coding, design, speaking) and share the video.",      75),
    ("Alumni Connect",               "Introduce 2 alumni to the CampusConnect network.",                             100),
    ("Weekly Check-in",              "Submit your weekly activity log with at least 5 completed micro-tasks.",         30),
]


def seed_data():
    """Idempotent seed — only runs once per fresh database."""
    from app import db
    from models import User, Ambassador, Task, TaskAssignment, Submission

    # Already seeded?
    if User.query.count() > 0:
        return

    print("🌱  Seeding CampusConnect database…")

    # ── Admin user ─────────────────────────────────────────────────────────
    admin = User(username='admin', email='admin@campusconnect.io', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()

    # ── Tasks (25) ─────────────────────────────────────────────────────────
    tasks = []
    for title, desc, pts in TASK_TEMPLATES:
        t = Task(
            title=title,
            description=desc,
            points=pts,
            created_by=admin.id,
            deadline=datetime.utcnow() + timedelta(days=random.randint(3, 14)),
        )
        db.session.add(t)
        tasks.append(t)
    db.session.flush()

    # ── Bob Kumar — at-risk ambassador (demo hero) ─────────────────────────
    bob_user = User(username='bob', email='bob@example.com', role='ambassador')
    bob_user.set_password('bob123')
    db.session.add(bob_user)
    db.session.flush()

    college_name, city, lat, lng = COLLEGES[0]  # IIT Bombay
    bob = Ambassador(
        user_id=bob_user.id,
        name='Bob Kumar',
        college=college_name,
        city=city,
        lat=lat,
        lng=lng,
        points=150,
        rank=15,
        risk_score=80,
        status='at_risk',
        inactive_days=4,
        completion_rate=0.25,
        response_time_hrs=28.0,
        portfolio_score=55,
        skills='Communication,Marketing',
        joined_at=datetime.utcnow() - timedelta(days=90),
        last_active=datetime.utcnow() - timedelta(days=4),
    )
    db.session.add(bob)
    db.session.flush()

    # Assign a pending task to Bob for demo
    demo_task = tasks[0]  # "Share a Campus Story"
    bob_assignment = TaskAssignment(
        task_id=demo_task.id,
        ambassador_id=bob.id,
        status='pending',
        auto_assigned=False,
    )
    db.session.add(bob_assignment)

    # ── 119 additional ambassadors ─────────────────────────────────────────
    used_names = {'bob'}
    ambassador_count = 0

    for i in range(119):
        # Generate unique username
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        full_name = f"{fn} {ln}"
        uname = f"{fn.lower()}{ln.lower()}{i}"

        # Risk profile distribution: ~10% high, ~20% medium, ~70% safe
        profile = random.choices(['high', 'medium', 'safe'], weights=[10, 20, 70])[0]

        if profile == 'high':
            inactive_days     = random.randint(4, 10)
            completion_rate   = round(random.uniform(0.1, 0.45), 2)
            response_time_hrs = round(random.uniform(25, 72), 1)
            points            = random.randint(50, 180)
            portfolio_score   = random.randint(30, 60)
        elif profile == 'medium':
            inactive_days     = random.randint(1, 4)
            completion_rate   = round(random.uniform(0.45, 0.74), 2)
            response_time_hrs = round(random.uniform(13, 25), 1)
            points            = random.randint(150, 300)
            portfolio_score   = random.randint(55, 75)
        else:
            inactive_days     = random.randint(0, 2)
            completion_rate   = round(random.uniform(0.74, 1.0), 2)
            response_time_hrs = round(random.uniform(1, 12), 1)
            points            = random.randint(250, 600)
            portfolio_score   = random.randint(70, 95)

        college_name, city, lat, lng = random.choice(COLLEGES)
        # Add slight jitter to coords so pins don't overlap
        lat_j = lat + random.uniform(-0.15, 0.15)
        lng_j = lng + random.uniform(-0.15, 0.15)

        skills = ','.join(random.sample(SKILLS_POOL, random.randint(2, 5)))

        user = User(username=uname, email=f"{uname}@example.com", role='ambassador')
        user.set_password('pass123')
        db.session.add(user)
        db.session.flush()

        amb = Ambassador(
            user_id=user.id,
            name=full_name,
            college=college_name,
            city=city,
            lat=lat_j,
            lng=lng_j,
            points=points,
            rank=0,
            inactive_days=inactive_days,
            completion_rate=completion_rate,
            response_time_hrs=response_time_hrs,
            portfolio_score=portfolio_score,
            skills=skills,
            joined_at=datetime.utcnow() - timedelta(days=random.randint(30, 180)),
            last_active=datetime.utcnow() - timedelta(days=inactive_days),
        )
        amb.calculate_risk()
        db.session.add(amb)
        db.session.flush()

        # Assign 1-3 random tasks
        assigned_tasks = random.sample(tasks, random.randint(1, 3))
        for t in assigned_tasks:
            status = random.choice(['pending', 'submitted', 'verified'])
            ta = TaskAssignment(
                task_id=t.id,
                ambassador_id=amb.id,
                status=status,
                auto_assigned=False,
            )
            db.session.add(ta)
            db.session.flush()

            if status in ('submitted', 'verified'):
                sub = Submission(
                    assignment_id=ta.id,
                    ambassador_id=amb.id,
                    proof_url=f"https://instagram.com/p/demo_{i}_{t.id}",
                    proof_text="Completed the task as required.",
                    submitted_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
                    status='pending' if status == 'submitted' else 'verified',
                    ai_confidence=round(random.uniform(0.80, 0.97), 2),
                    ai_verdict='verified',
                    points_awarded=t.points if status == 'verified' else 0,
                )
                db.session.add(sub)

        ambassador_count += 1

    db.session.flush()

    # ── Recalculate ranks ──────────────────────────────────────────────────
    all_ambs = Ambassador.query.order_by(Ambassador.points.desc()).all()
    for idx, a in enumerate(all_ambs, 1):
        a.rank = idx

    db.session.commit()
    print(f"✅  Seeded: 1 admin + {ambassador_count + 1} ambassadors + {len(tasks)} tasks.")