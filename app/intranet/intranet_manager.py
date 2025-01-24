from datetime import datetime

from app.intranet.intranet_api import IntranetApi
from app.logger import log_info
from app.model.Student import Student
from app.myepitech.myepitech_api import MyEpitechApi
from app.tools.date_spliter import split_dates


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

        dates = split_dates(start_str, end_str, 70)

        for (s_start, s_end )in dates:
            log_info(f"[INTRA] Fetching student planning for {student.student_label} from {s_start} to {s_end}")
            res =  self.api.api_request(f"planning/load?start={s_start}&end={s_end}&format=json", student)

            for event in res:
                if "calendar_type" in event and event["calendar_type"] == "perso":
                    continue
                if not event['event_registered'] in ['present', 'registered'] and (event['rdv_indiv_registered'] is None and event['rdv_group_registered'] is None):
                    continue # Skip events without registered students
                final.append(event)
        # Remove duplicates
        return final

    def fetch_projects(self, student: Student, start_date: datetime, end_date: datetime):
        log_info(f"[INTRA] Fetching student projects for {student.student_label}")
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        final = []

        dates = split_dates(start_str, end_str, 70)

        for (s_start, s_end )in dates:
            log_info(f"[INTRA] Fetching student projects for {student.student_label} from {s_start} to {s_end}")
            res = self.api.api_request(f"module/board/?start={s_start}&end={s_end}&format=json", student)

            for activity in res:
                if not activity['registered']:
                    continue
                if activity['type_acti_code'] not in ["proj", "tp"]:
                    continue
                final.append(activity)
        return final

    def fetch_project_slug(self, ask_json: dict, student: Student):
        scolyear = ask_json['year']
        codemodule = ask_json['module']
        codeinstance = ask_json['instance']
        codeacti = ask_json['code_acti']

        url = f"module/{scolyear}/{codemodule}/{codeinstance}/{codeacti}/project/?format=json"

        log_info(f"[INTRA] Fetching project slug for {codeacti}")
        result =  self.api.api_request(url, student)

        if not "slug" in result:
            return None
        return result["slug"]

    def fetch_student_picture(self, student_login: str, student: Student) -> bytes:
        """
        Fetch the student picture from the intranet
        :param student_login:
        :param student:
        :return: Image bytes
        """
        log_info(f"[INTRA] Fetching student picture for {student_login}")
        url = f"file/userprofil/profilview/{student_login}.jpg"
        img_bytes = self.api.api_request(url, student)
        return img_bytes
