import re
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

    def fetch_modules_list(self, student: Student):
        url = f"/course/filter?format=json"
        log_info(f"[INTRA] Fetching modules list")
        res = self.api.api_request(url, student)
        ret = []
        for m in res:
            ret.append({
                "code": m["code"],
                "scolaryear": m["scolaryear"],
                "codeinstance": m["codeinstance"],
            })
        return ret

    def fetch_module(self, scolar_year: int, code_module: str, code_instance: str, student: Student):
        url = f"module/{scolar_year}/{code_module}/{code_instance}/?format=json"
        log_info(f"[INTRA] Fetching module {code_module}")

        module_data = self.api.api_request(url, student)

        module_data["tb_is_roadblock"] = False
        module_data["tb_roadblock_submodules"] = None
        module_data["tb_required_credits"] = None

        if "-EPI-" in module_data["codemodule"]:
            # This module is a roadblock
            road_submodules = []

            for row in module_data["description"].split("\n"):
                # extract the code of the submodule, who have the format like "L-LLL-NNN" where L is a letter and N is a number
                mod_patten = re.compile(r"[A-Z]-[A-Z]{3}-\d{3}")
                match = mod_patten.search(row)
                if match:
                    road_submodules.append(match.group())

                # As a reminder, to validate this unit you must acquire at least 3 credits with the units listed below:
                cred_pattern = re.compile(r"validate this unit you must acquire at least (\d+) credits")
                match = cred_pattern.search(row)
                if match:
                    module_data["tb_required_credits"] = int(match.group(1))

            module_data["tb_roadblock_submodules"] = road_submodules
            module_data["tb_is_roadblock"] = len(road_submodules) > 0 and module_data["tb_required_credits"] is not None
        return module_data

