"""Seed demo coaches and slots.

Usage: python manage.py seed_coaches
Safe to re-run; existing coach slots are refreshed.
"""

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    User, Category, Skill, Area,
    CoachProfile, CoachSubscription, SessionSlot,
)


COACHES = [

    # Grinds (core)
    {
        "username": "john_maths", "forename": "John", "surname": "Murphy",
        "email": "john.murphy@example.com",
        "bio": "Experienced Leaving Cert Maths teacher with 10 years in secondary schools. Specialist in Higher Level Paper 2. In-person in Dublin City and Dublin 2.",
        "category": "Grinds", "skills": ["Maths"], "rate": 45, "areas": ["Dublin City", "Dublin 2"], "verified": True,
    },
    {
        "username": "aoife_english", "forename": "Aoife", "surname": "Kelly",
        "email": "aoife.kelly@example.com",
        "bio": "English and Irish tutor specialising in Junior Cert and Leaving Cert. Studied at UCD, tutoring for 6 years. In-person in Dublin and Tallaght.",
        "category": "Grinds", "skills": ["English", "Irish"], "rate": 40, "areas": ["Dublin City", "Tallaght"], "verified": True,
    },
    {
        "username": "sean_science", "forename": "Sean", "surname": "O'Brien",
        "email": "sean.obrien@example.com",
        "bio": "Biology grinds for Leaving Cert. Graduated from Trinity with a degree in Natural Sciences. In-person in Dublin City and Swords.",
        "category": "Grinds", "skills": ["Biology"], "rate": 42, "areas": ["Dublin City", "Swords"], "verified": False,
    },
    {
        "username": "niamh_tutor", "forename": "Niamh", "surname": "Walsh",
        "email": "niamh.walsh@example.com",
        "bio": "Qualified primary school teacher offering Junior Cert grinds in Maths and English. Based in Cork City, also available online.",
        "category": "Grinds", "skills": ["Maths", "English"], "rate": 38, "areas": ["Cork City"], "verified": False,
    },
    {
        "username": "patrick_maths", "forename": "Patrick", "surname": "Dillon",
        "email": "patrick.dillon@example.com",
        "bio": "Maths grinds for Leaving Cert. DCU graduate, 4 years tutoring experience. In-person in Swords and Dublin City.",
        "category": "Grinds", "skills": ["Maths"], "rate": 40, "areas": ["Swords", "Dublin City"], "verified": False,
    },
    {
        "username": "laura_irish", "forename": "Laura", "surname": "Ni Fhaolain",
        "email": "laura.nifhaolain@example.com",
        "bio": "Native Irish speaker offering Irish grinds for Junior and Leaving Cert. In-person in Dublin City and Dublin 2.",
        "category": "Grinds", "skills": ["Irish"], "rate": 44, "areas": ["Dublin City", "Dublin 2"], "verified": True,
    },
    {
        "username": "tom_biology", "forename": "Tom", "surname": "Kavanagh",
        "email": "tom.kavanagh@example.com",
        "bio": "Biology Leaving Cert tutor. UCC graduate, secondary school teacher offering evening grinds. In-person in Cork City.",
        "category": "Grinds", "skills": ["Biology"], "rate": 41, "areas": ["Cork City"], "verified": False,
    },

    # Grinds (additional)
    {
        "username": "emma_chemistry", "forename": "Emma", "surname": "Collins",
        "email": "emma.collins@example.com",
        "bio": "Chemistry and Physics Leaving Cert tutor. Graduated from UCD with a degree in Chemical Science. In-person in Dublin City and Dublin 2.",
        "category": "Grinds", "skills": ["Chemistry"], "rate": 45, "areas": ["Dublin City", "Dublin 2"], "verified": True,
    },
    {
        "username": "james_physics", "forename": "James", "surname": "Burke",
        "email": "james.burke@example.com",
        "bio": "Physics and Applied Maths grinds for Leaving Cert. Former secondary school teacher with 12 years experience. In-person in Swords and Dublin City.",
        "category": "Grinds", "skills": ["Physics"], "rate": 46, "areas": ["Swords", "Dublin City"], "verified": True,
    },
    {
        "username": "claire_french", "forename": "Claire", "surname": "Martin",
        "email": "claire.martin@example.com",
        "bio": "Native French speaker offering Leaving Cert French grinds. Lived in Paris for 10 years. Focused on oral and written exams. In-person in Dublin City.",
        "category": "Grinds", "skills": ["French"], "rate": 42, "areas": ["Dublin City", "Tallaght"], "verified": False,
    },
    {
        "username": "carlos_spanish", "forename": "Carlos", "surname": "Rivera",
        "email": "carlos.rivera@example.com",
        "bio": "Native Spanish speaker from Madrid offering Leaving Cert Spanish grinds. Online and in-person in Dublin City.",
        "category": "Grinds", "skills": ["Spanish"], "rate": 42, "areas": ["Dublin City", "Dublin 2"], "verified": True,
    },
    {
        "username": "sarah_accounting", "forename": "Sarah", "surname": "Byrne",
        "email": "sarah.byrne@example.com",
        "bio": "Accounting and Business Leaving Cert tutor. Qualified accountant with 5 years teaching experience. In-person in Cork City and online.",
        "category": "Grinds", "skills": ["Accounting"], "rate": 40, "areas": ["Cork City"], "verified": False,
    },
    {
        "username": "michael_business", "forename": "Michael", "surname": "Dunne",
        "email": "michael.dunne@example.com",
        "bio": "Business and Economics grinds for Leaving Cert. MBA graduate and former business teacher. In-person in Tallaght and Dublin City.",
        "category": "Grinds", "skills": ["Business"], "rate": 40, "areas": ["Tallaght", "Dublin City"], "verified": False,
    },
    {
        "username": "grace_geography", "forename": "Grace", "surname": "O'Sullivan",
        "email": "grace.osullivan@example.com",
        "bio": "Geography and History Leaving Cert grinds. Geography graduate from Maynooth University. In-person in Dublin City and Swords.",
        "category": "Grinds", "skills": ["Geography"], "rate": 38, "areas": ["Dublin City", "Swords"], "verified": False,
    },
    {
        "username": "daniel_history", "forename": "Daniel", "surname": "Flood",
        "email": "daniel.flood@example.com",
        "bio": "History and Politics and Society Leaving Cert tutor. History graduate from Trinity College Dublin. Strong focus on essay technique and exam skills.",
        "category": "Grinds", "skills": ["History"], "rate": 39, "areas": ["Dublin City", "Dublin 2"], "verified": True,
    },
    {
        "username": "anna_german", "forename": "Anna", "surname": "Schmidt",
        "email": "anna.schmidt@example.com",
        "bio": "Native German speaker offering Leaving Cert German grinds. Originally from Munich, based in Dublin. Online and in-person sessions available.",
        "category": "Grinds", "skills": ["German"], "rate": 43, "areas": ["Dublin City", "Dublin 2"], "verified": True,
    },
    {
        "username": "kevin_compsci", "forename": "Kevin", "surname": "Hayes",
        "email": "kevin.hayes@example.com",
        "bio": "Computer Science and Applied Maths Leaving Cert tutor. Software engineer offering grinds in the evenings. In-person in Dublin City and online.",
        "category": "Grinds", "skills": ["Computer Science"], "rate": 50, "areas": ["Dublin City", "Dublin 2"], "verified": False,
    },
    {
        "username": "fiona_homeec", "forename": "Fiona", "surname": "Murphy",
        "email": "fiona.murphy@example.com",
        "bio": "Home Economics Leaving Cert tutor. Qualified Home Economics teacher with 8 years in secondary schools. In-person in Tallaght and Dublin City.",
        "category": "Grinds", "skills": ["Home Economics"], "rate": 37, "areas": ["Tallaght", "Dublin City"], "verified": False,
    },
    {
        "username": "stephen_appliedmaths", "forename": "Stephen", "surname": "Carroll",
        "email": "stephen.carroll@example.com",
        "bio": "Applied Maths and Maths Leaving Cert grinds. Maths PhD student at UCD. Specialist in higher level problem solving. In-person in Dublin City.",
        "category": "Grinds", "skills": ["Applied Maths"], "rate": 48, "areas": ["Dublin City", "Swords"], "verified": True,
    },
    {
        "username": "mary_art", "forename": "Mary", "surname": "Hennessy",
        "email": "mary.hennessy@example.com",
        "bio": "Art Leaving Cert tutor. Fine Art graduate from NCAD. Offering grinds in drawing, painting and art history. In-person in Dublin City.",
        "category": "Grinds", "skills": ["Art"], "rate": 38, "areas": ["Dublin City", "Dublin 2"], "verified": False,
    },
    {
        "username": "paul_economics", "forename": "Paul", "surname": "Sheridan",
        "email": "paul.sheridan@example.com",
        "bio": "Economics and Business Leaving Cert tutor. Economics graduate from UCC. Online and in-person in Cork City.",
        "category": "Grinds", "skills": ["Economics"], "rate": 41, "areas": ["Cork City"], "verified": False,
    },
    {
        "username": "helen_pe", "forename": "Helen", "surname": "Brady",
        "email": "helen.brady@example.com",
        "bio": "Physical Education Leaving Cert tutor. PE teacher with focus on written exam and performance analysis. In-person in Dublin City.",
        "category": "Grinds", "skills": ["Physical Education"], "rate": 38, "areas": ["Dublin City", "Tallaght"], "verified": False,
    },

    # Sports
    {
        "username": "padraig_padel", "forename": "Padraig", "surname": "Connolly",
        "email": "padraig.connolly@example.com",
        "bio": "Certified padel coach with 5 years experience. All levels from beginners to competitive players.",
        "category": "Sports", "skills": ["Padel"], "rate": 55, "areas": ["Dublin City", "Dublin 2"], "verified": True, "eircode": "D04 AX12",
    },
    {
        "username": "ciara_pt", "forename": "Ciara", "surname": "Brennan",
        "email": "ciara.brennan@example.com",
        "bio": "Personal trainer and fitness coach. Specialising in strength training and weight loss. REPS Ireland certified.",
        "category": "Sports", "skills": ["Gym PT"], "rate": 50, "areas": ["Dublin City", "Tallaght"], "verified": True, "eircode": "D24 BX45",
    },
    {
        "username": "liam_football", "forename": "Liam", "surname": "Fitzgerald",
        "email": "liam.fitzgerald@example.com",
        "bio": "FAI qualified football coach. Individual coaching sessions for players aged 8-18.",
        "category": "Sports", "skills": ["Football Coaching"], "rate": 45, "areas": ["Dublin City", "Swords"], "verified": False, "eircode": "K67 XY89",
    },
    {
        "username": "orla_golf", "forename": "Orla", "surname": "Hennessy",
        "email": "orla.hennessy@example.com",
        "bio": "Golf instructor with a 4 handicap. PGA qualified. Lessons for complete beginners through to single-figure handicap players.",
        "category": "Sports", "skills": ["Golf"], "rate": 60, "areas": ["Dublin City", "Dublin 2"], "verified": True, "eircode": "D18 KP34",
    },
    {
        "username": "kevin_pt", "forename": "Kevin", "surname": "Burke",
        "email": "kevin.burke@example.com",
        "bio": "Personal trainer specialising in strength and conditioning. 8 years experience. Based in Tallaght.",
        "category": "Sports", "skills": ["Gym PT"], "rate": 48, "areas": ["Tallaght", "Dublin City"], "verified": False, "eircode": "D24 KX78",
    },
    {
        "username": "emma_padel", "forename": "Emma", "surname": "Nolan",
        "email": "emma.nolan@example.com",
        "bio": "Padel coach based in Dublin 2. Beginner and intermediate lessons available at weekends.",
        "category": "Sports", "skills": ["Padel"], "rate": 52, "areas": ["Dublin 2", "Dublin City"], "verified": True, "eircode": "D02 YK45",
    },

    # Music
    {
        "username": "declan_guitar", "forename": "Declan", "surname": "Ryan",
        "email": "declan.ryan@example.com",
        "bio": "Guitar tutor teaching rock, blues, and classical styles. Studied at BIMM Dublin. Teaching for 8 years. In-person in Dublin City and Dublin 2.",
        "category": "Music", "skills": ["Guitar"], "rate": 40, "areas": ["Dublin City", "Dublin 2"], "verified": False,
    },
    {
        "username": "sinead_piano", "forename": "Sinead", "surname": "Byrne",
        "email": "sinead.byrne@example.com",
        "bio": "RIAM qualified piano teacher. Preparing students for ABRSM exams. Online and in-person in Tallaght and Dublin City.",
        "category": "Music", "skills": ["Piano"], "rate": 45, "areas": ["Dublin City", "Tallaght"], "verified": True,
    },
    {
        "username": "conor_violin", "forename": "Conor", "surname": "McCarthy",
        "email": "conor.mccarthy@example.com",
        "bio": "Violinist with the RTE Concert Orchestra. Beginners to advanced. In-person in Swords and Dublin City.",
        "category": "Music", "skills": ["Violin"], "rate": 50, "areas": ["Dublin City", "Swords"], "verified": True,
    },
    {
        "username": "fiona_music", "forename": "Fiona", "surname": "Gallagher",
        "email": "fiona.gallagher@example.com",
        "bio": "Multi-instrumentalist offering guitar and piano lessons. Galway based, in-person in Galway City and available online.",
        "category": "Music", "skills": ["Guitar", "Piano"], "rate": 38, "areas": ["Galway City"], "verified": False,
    },
    {
        "username": "brian_guitar", "forename": "Brian", "surname": "Doyle",
        "email": "brian.doyle@example.com",
        "bio": "Acoustic and electric guitar lessons for all ages. 15 years teaching experience. In-person in Cork City.",
        "category": "Music", "skills": ["Guitar"], "rate": 36, "areas": ["Cork City"], "verified": False,
    },
    {
        "username": "rachel_piano", "forename": "Rachel", "surname": "Quinn",
        "email": "rachel.quinn@example.com",
        "bio": "Piano and keyboard teacher based in Swords. Classical and contemporary styles.",
        "category": "Music", "skills": ["Piano"], "rate": 42, "areas": ["Swords", "Dublin City"], "verified": True,
    },
    {
        "username": "mark_violin", "forename": "Mark", "surname": "Sheridan",
        "email": "mark.sheridan@example.com",
        "bio": "Violin and viola teacher with a Masters from the Royal Irish Academy of Music. In-person in Dublin 2 and Dublin City.",
        "category": "Music", "skills": ["Violin"], "rate": 55, "areas": ["Dublin 2", "Dublin City"], "verified": True,
    },
]


GRINDS_SCHEDULE = [
    (1, 16, 1), (1, 17, 1),
    (3, 16, 1), (3, 17, 1),
    (6, 10, 1), (6, 11, 1),
]
SPORTS_SCHEDULE = [
    (1, 9,  1), (3, 9,  1),
    (5, 10, 1), (5, 11, 1),
    (5, 12, 1), (6, 9,  1),
]
MUSIC_SCHEDULE = [
    (1, 15, 1), (1, 16, 1),
    (2, 15, 1), (3, 15, 1),
    (5, 11, 1), (6, 14, 1),
]
SCHEDULE_BY_CATEGORY = {
    "Grinds": GRINDS_SCHEDULE,
    "Sports": SPORTS_SCHEDULE,
    "Music":  MUSIC_SCHEDULE,
}


class Command(BaseCommand):
    help = "Seeds the database with fake coaches and session slots."

    def handle(self, *args, **options):
        self.stdout.write("Seeding lookup data...")
        self._seed_lookup_data()

        created = refreshed = 0
        for data in COACHES:
            if User.objects.filter(username=data["username"]).exists():
                self.stdout.write(f"  {data['username']} exists — refreshing slots")
                user = User.objects.get(username=data["username"])
                coach = user.coach_profile
                coach.slots.filter(status="AVAILABLE").delete()
                self._create_slots(coach, data)
                refreshed += 1
            else:
                self._create_coach(data)
                self.stdout.write(f"  Created {data['forename']} {data['surname']}")
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {created} coaches created, {refreshed} slots refreshed."
        ))

    def _seed_lookup_data(self):
        grinds, _ = Category.objects.get_or_create(name="Grinds")
        sports, _ = Category.objects.get_or_create(name="Sports")
        music,  _ = Category.objects.get_or_create(name="Music")

        for s in [
            "Maths", "Irish", "English", "Biology", "Chemistry", "Physics",
            "Agricultural Science", "Accounting", "Business", "Economics",
            "Geography", "History", "Art", "Music", "Home Economics",
            "French", "German", "Spanish", "Italian", "Japanese", "Mandarin Chinese",
            "Latin", "Classical Studies", "Religious Education",
            "Physical Education", "Computer Science", "Design and Communication Graphics",
            "Construction Studies", "Engineering", "Technology",
            "Applied Maths", "Politics and Society",
        ]:
            Skill.objects.get_or_create(category=grinds, name=s)

        for s in ["Padel", "Gym PT", "Football Coaching", "Golf"]:
            Skill.objects.get_or_create(category=sports, name=s)

        for s in ["Guitar", "Piano", "Violin"]:
            Skill.objects.get_or_create(category=music, name=s)

        for a in ["Dublin City", "Dublin 2", "Tallaght", "Swords", "Cork City", "Galway City"]:
            Area.objects.get_or_create(name=a)

    def _create_coach(self, data):
        user = User.objects.create_user(
            username=data["username"], email=data["email"], password="LevelUp2024!",
            forename=data["forename"], surname=data["surname"], bio=data["bio"],
            role=User.Role.COACH,
        )
        category = Category.objects.get(name=data["category"])
        coach = CoachProfile.objects.create(
            user=user, category=category, hourly_rate=data["rate"],
            is_verified=data.get("verified", False),
            base_location_eircode=data.get("eircode", ""),
        )
        for skill_name in data["skills"]:
            coach.teaches.add(Skill.objects.get(name=skill_name, category=category))
        for area_name in data["areas"]:
            coach.travel_areas.add(Area.objects.get(name=area_name))
        CoachSubscription.objects.create(coach_user=user, tier="FREE")
        self._create_slots(coach, data)

    def _create_slots(self, coach, data):
        category_name = data["category"]
        schedule = SCHEDULE_BY_CATEGORY[category_name]
        category = Category.objects.get(name=category_name)
        skill = Skill.objects.get(name=data["skills"][0], category=category)
        coach_areas = [Area.objects.get(name=n) for n in data["areas"]]
        eircode = data.get("eircode", "")
        today = datetime.date.today()

        for week in range(4):
            for i, (weekday, hour, duration_hours) in enumerate(schedule):
                days_ahead = (weekday - today.weekday()) % 7 or 7
                slot_date = today + datetime.timedelta(days=days_ahead + (week * 7))
                start_dt = timezone.make_aware(
                    datetime.datetime(slot_date.year, slot_date.month, slot_date.day, hour, 0, 0)
                )
                end_dt = start_dt + datetime.timedelta(hours=duration_hours)

                if category_name == "Sports":
                    mode = SessionSlot.Mode.IN_PERSON
                    slot_area = coach_areas[i % len(coach_areas)]
                    slot_eircode = eircode
                elif i % 2 == 0:
                    mode = SessionSlot.Mode.ONLINE
                    slot_area = None
                    slot_eircode = ""
                else:
                    mode = SessionSlot.Mode.IN_PERSON
                    slot_area = coach_areas[(i // 2) % len(coach_areas)]
                    slot_eircode = ""

                slot = SessionSlot(
                    coach=coach, skill=skill, mode=mode,
                    area=slot_area, venue_eircode=slot_eircode,
                    start_datetime=start_dt, end_datetime=end_dt,
                )
                try:
                    slot.full_clean()
                    slot.save()
                except Exception as e:
                    self.stdout.write(f"    Skipped: {e}")
