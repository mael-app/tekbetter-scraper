from datetime import datetime

from app.intranet.intranet_api import IntranetApi
from app.logger import log_info
from app.model.Student import Student
from app.myepitech.myepitech_api import MyEpitechApi


class IntranetManager:
    def __init__(self):
        self.api = IntranetApi()

    def fetch_student(self, student: Student):
        log_info(f"[INTRA] Fetching student profile {student.student_label}")
        return self.api.api_request("user/?format=json", student)

    def fetch_planning(self, student: Student, start_date: datetime, end_date: datetime):
        log_info(f"[INTRA] Fetching student planning for {student.student_label}")
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        final = []
        res =  self.api.api_request(f"planning/load?start={start_str}&end={end_str}&format=json", student)

        for event in res:
            if "calendar_type" in event and event["calendar_type"] == "perso":
                continue
            if not event['event_registered'] in ['present', 'registered'] and (event['rdv_indiv_registered'] is None and event['rdv_group_registered'] is None):
                continue # Skip events without registered students
            final.append(event)
        return final

    def fetch_projects(self, student: Student, start_date: datetime, end_date: datetime):
        log_info(f"[INTRA] Fetching student projects for {student.student_label}")
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        final = []
        res = self.api.api_request(f"module/board/?start={start_str}&end={end_str}&format=json", student)

        for activity in res:
            if not activity['registered']:
                continue
            if not activity['type_acti_code'] == "proj":
                continue
            final.append(activity)
        return final

    def fetch_project_slug(self, intra_project_json: dict, student: Student):
        scolyear = intra_project_json['scolaryear']
        codemodule = intra_project_json['codemodule']
        codeinstance = intra_project_json['codeinstance']
        codeacti = intra_project_json['codeacti']

        url = f"module/{scolyear}/{codemodule}/{codeinstance}/{codeacti}/project/?format=json"

        log_info(f"[INTRA] Fetching project slug for {codeacti}")
        result =  self.api.api_request(url, student)

        if not "slug" in result:
            return None
        return result["slug"]