import base64
import os
import time
from datetime import datetime, timedelta
import requests
from app.intranet.intranet_manager import IntranetManager
from app.logger import log_info, log_error, log_warning
from app.myepitech.myepitech_manager import MyEpitechManager
from app.tools.config_loader import load_configuration
from app.tools.env_loader import check_env_variables
from app.model.Student import Student, TaskStatus, TaskType

class Main:
    def __init__(self):
        log_info("Welcome to the TekBetter scraper")
        self.students = []
        self.threads = []
        self.student_interval = 0

        self.myepitech = MyEpitechManager()
        self.intranet = IntranetManager()
        self.intervals = {
            "moulinettes": 25,
            "modules": 25,
            "profile": 25,
            "planning": 25,
            "projects": 25,
            "avatar": 25,
            "slugs": 25,
        }

        if not check_env_variables() or not load_configuration(self):
            exit(1)

        for student in self.students:
            student.main = self

    def sync_student(self, student):
        res = requests.get(f"{os.getenv('TEKBETTER_API_URL')}/api/scraper/infos", headers={
            "Authorization": f"Bearer {student.tekbetter_token}"
        })
        if res.status_code != 200:
            log_error(f"Failed to fetch known tests for student: {student.student_label}")
            return

        student.send_task_status({TaskType.SCRAPING: TaskStatus.LOADING})

        known_tests = res.json()["known_tests"]
        known_modules = res.json()["known_modules"] if "known_modules" in res.json() else []
        asked_slugs = res.json()["asked_slugs"]
        asked_pictures = res.json()["asked_pictures"] if "asked_pictures" in res.json() else []


        body = {
            "new_moulis": None,
            "intra_profile": None,
            "intra_planning": None,
            "intra_projects": None,
            "modules": None,
            "projects_slugs": {},
        }


        body["new_moulis"] = student.scrape_moulinettes(known_tests)
        body["modules"] = student.scrape_modules(known_modules)

        start_date = datetime.now() - timedelta(days=365*5)
        end_date = datetime.now() + timedelta(days=365)
        if "fetch_start" in res.json():
            start_date = datetime.strptime(res.json()["fetch_start"], "%Y-%m-%d")
        if "fetch_end" in res.json():
            end_date = datetime.strptime(res.json()["fetch_end"], "%Y-%m-%d")


        body["intra_profile"] = self.intranet.fetch_student(student)
        body["intra_planning"] = self.intranet.fetch_planning(student, start_date, end_date)

        try:
            body["students_pictures"] = {}
            if len(asked_pictures) > 0:
                student.send_task_status({TaskType.AVATAR: TaskStatus.LOADING})
            for student_login in asked_pictures:
                picture = self.intranet.fetch_student_picture(student_login, student)
                body["students_pictures"][student_login] = base64.b64encode(picture).decode("utf-8")
            student.send_task_status({TaskType.AVATAR: TaskStatus.SUCCESS})
        except Exception as e:
            student.send_task_status({TaskType.AVATAR: TaskStatus.ERROR})
            log_error(f"Failed to fetch Intranet student pictures for student: {student.student_label}")

        # Fetch project slugs for the asked projects
        try:
            if len(asked_slugs) > 0:
                student.send_task_status({TaskType.SLUGS: TaskStatus.LOADING})
            for proj in asked_slugs:
                slug = self.intranet.fetch_project_slug(proj, student)
                body["projects_slugs"][proj["code_acti"]] = slug
            student.send_task_status({TaskType.SLUGS: TaskStatus.SUCCESS})
        except Exception as e:
            log_error(f"Failed to fetch Intranet project slugs for student: {student.student_label}")
            log_error(str(e))
            student.send_task_status({TaskType.SLUGS: TaskStatus.ERROR})
        log_info(f"Pushing data for student: {student.student_label}")

        res = requests.post(f"{os.getenv('TEKBETTER_API_URL')}/api/scraper/push", json=body, headers={
            "Authorization": f"Bearer {student.tekbetter_token}"
        })

        if res.status_code != 200:
            log_error(f"Failed to push data for student: {student.student_label}")
            student.send_task_status({TaskType.SCRAPING: TaskStatus.ERROR})
            return
        log_info(f"Data pushed for student: {student.student_label}")
        student.send_task_status({TaskType.SCRAPING: TaskStatus.SUCCESS})


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