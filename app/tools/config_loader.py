import json
import os

import requests

from app.intranet.intranet_antiddos_bypass import IntranetAntiDDoSBypasser
from app.logger import log_info, log_error, log_warning
from app.model.Student import Student

def get_or_create(token, students):
    for student in students:
        if student.tekbetter_token == token:
            return student, False
    s = Student()
    s.antiddos = IntranetAntiDDoSBypasser()
    return s, True

def load_configuration(main):
    json_data = {}

    # Load data from config file or from the API
    if os.getenv("SCRAPER_MODE") == "private":
        path = os.getenv("SCRAPER_CONFIG_FILE")
        file_content = open(path, "r").read()
        if file_content:
            try:
                json_data = json.loads(file_content)
            except:
                log_error("Config file is not a valid JSON file")
                return False
        else:
            json_data = {}
    else:
        res = requests.get(f"{os.getenv('TEKBETTER_API_URL')}/api/scraper/config", headers={
            "Authorization": f"Bearer {os.getenv('PUBLIC_SCRAPER_TOKEN')}"
        })
        if res.status_code != 200:
            log_error("Failed to fetch config from TekBetter API")
            return False
        json_data = res.json()

    # Create config keys if they don't exist
    if not "student_interval" in json_data:
        json_data["student_interval"] = 60
    if not "students" in json_data:
        json_data["students"] = []
    for student in json_data["students"]:
        if not "microsoft_session" in student:
            student["microsoft_session"] = ""
        if not "tekbetter_token" in student:
            student["tekbetter_token"] = ""

    # --- Apply the configuration ---
    main.student_interval = json_data["student_interval"]

    # Add new students to the list
    for student in json_data["students"]:
        student_obj, created = get_or_create(student["tekbetter_token"], main.students)
        student_obj.microsoft_session = student["microsoft_session"]
        student_obj.tekbetter_token = student["tekbetter_token"]
        if "." in student_obj.tekbetter_token and "_" in student_obj.tekbetter_token:
            student_obj.student_label = student_obj.tekbetter_token.split("_")[0]
        if created:
            main.students.append(student_obj)

    # Remove students that are not in the config anymore
    for student in main.students:
        if len([s for s in json_data["students"] if s["tekbetter_token"] == student.tekbetter_token]) == 0:
            main.students.remove(student)
    log_info("Config reload successful: " + str(len(main.students)) + " students loaded")


    if "intervals" in json_data:
        for key in json_data["intervals"]:
            if key not in main["intervals"]:
                log_warning(f"Unknown interval key: {key}")
                continue
            main.intervals[key] = json_data["intervals"][key]
    return True