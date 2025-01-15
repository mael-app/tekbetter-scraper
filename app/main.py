import os
import time
import traceback
from datetime import datetime, timedelta
import requests
from app.intranet.intranet_manager import IntranetManager
from app.logger import log_info, log_error, log_warning
from app.myepitech.myepitech_manager import MyEpitechManager
from app.tools.config_loader import load_configuration
from app.tools.env_loader import check_env_variables

class Main:
    def __init__(self):
        log_info("Welcome to the TekBetter scraper")
        self.students = []
        self.threads = []
        self.student_interval = 0

        self.myepitech = MyEpitechManager()
        self.intranet = IntranetManager()

        if not check_env_variables() or not load_configuration(self):
            exit(1)

    def sync_student(self, student):
        res = requests.get(f"{os.getenv('TEKBETTER_API_URL')}/api/scraper/infos", headers={
            "Authorization": f"Bearer {student.tekbetter_token}"
        })

        if res.status_code != 200:
            log_error(f"Failed to fetch known tests for student: {student.student_label}")
            return
        known_tests = res.json()["known_tests"]
        asked_slugs = res.json()["asked_slugs"]

        body = {
            "new_moulis": None,
            "intra_profile": None,
            "intra_planning": None,
            "intra_projects": None,
            "projects_slugs": {},
        }

        try:
            body["new_moulis"] = self.myepitech.fetch_student(student, known_tests=known_tests)
        except Exception as e:
            log_error(f"Failed to fetch MyEpitech data for student: {student.student_label}")
            traceback.print_exc()
        start_date = datetime.now() - timedelta(days=365*3)
        end_date = datetime.now() + timedelta(days=365)

        try:
            body["intra_profile"] = self.intranet.fetch_student(student)
        except Exception as e:
            log_error(f"Failed to fetch Intranet data for student: {student.student_label}")
            traceback.print_exc()
        try:
            body["intra_planning"] = self.intranet.fetch_planning(student, start_date, end_date)
        except Exception as e:
            log_error(f"Failed to fetch Intranet planning for student: {student.student_label}")
            traceback.print_exc()
        try:
            body["intra_projects"] = self.intranet.fetch_projects(student, start_date, end_date)
        except Exception as e:
            log_error(f"Failed to fetch Intranet projects for student: {student.student_label}")
            traceback.print_exc()

        # Fetch project slugs for the asked projects
        if body["intra_projects"]:
            try:
                for proj in body["intra_projects"]:
                    if proj["codeacti"] in asked_slugs:
                        slug = self.intranet.fetch_project_slug(proj, student)
                        body["projects_slugs"][proj["codeacti"]] = slug
            except Exception as e:
                log_error(f"Failed to fetch Intranet project slugs for student: {student.student_label}")
                traceback.print_exc()
        log_info(f"Pushing data for student: {student.student_label}")

        res = requests.post(f"{os.getenv('TEKBETTER_API_URL')}/api/scraper/push", json=body, headers={
            "Authorization": f"Bearer {student.tekbetter_token}"
        })

        if res.status_code != 200:
            log_error(f"Failed to push data for student: {student.student_label}")
            return
        log_info(f"Data pushed for student: {student.student_label}")

    def sync_passage(self):
        for student in self.students:
            if student.last_sync + self.student_interval < datetime.now().timestamp():
                try:
                    self.sync_student(student)
                    student.last_sync = datetime.now().timestamp()
                except Exception as e:
                    log_error(f"Failed to sync student: {student.student_label}")
                    log_error(str(e))


if __name__ == "__main__":

    main = Main()
    last_config_update = datetime.now()
    CONFIG_RELOAD_INTERVAL = 2

    try:
        while True:
            try:
                time.sleep(5)
                main.sync_passage()

                if last_config_update + timedelta(minutes=CONFIG_RELOAD_INTERVAL) < datetime.now():
                    last_config_update = datetime.now()
                    load_configuration(main)
            except Exception as e:
                log_error("An error occured in the main loop")
                log_error(str(e))
                time.sleep(60)
                continue
    except KeyboardInterrupt:
        log_error("Received keyboard interrupt, exiting.")
        for t in main.threads:
            t.join()
        exit(0)