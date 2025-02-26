import os
import time

from app.intranet.intranet_antiddos_bypass import IntranetAntiDDoSBypasser
import requests

from app.logger import log_error


class TaskStatus:
    ERROR = "error"
    LOADING = "loading"
    SUCCESS = "success"

class TaskType:
    MOULI = "mouli"
    PLANNING = "planning"
    PROJECTS = "projects"
    SLUGS = "slugs"
    MODULES = "modules"
    AVATAR = "avatar"
    PROFILE = "profile"
    AUTH = "auth"
    SCRAPING = "scraping"



class Student:
    microsoft_session: str
    tekbetter_token: str = None
    myepitech_token: str = None
    intra_token: str = None
    last_sync: int = 0
    student_label: str = None
    antiddos: IntranetAntiDDoSBypasser = None
    main: None
    last_scrapes = {}

    def send_task_status(self, status: {TaskType: TaskStatus}):
        """
        Send to the server the current scraping status for a task
        """
        try:
            body = {}
            for key, value in status.items():
                body[key] = value
            requests.post(f"{os.getenv('TEKBETTER_API_URL')}/api/scraper/status", json=body, headers={
                "Authorization": f"Bearer {self.tekbetter_token}"
            })
        except Exception as e:
            log_error(f"Failed to send task status to the server for student: {self.student_label}")
            log_error(str(e))

    def save_scrape(self, key):
        self.last_scrapes[key] = time.time()

    def can_scrape(self, type, cooldown):
        if type in self.last_scrapes:
            return time.time() - self.last_scrapes[type] > cooldown
        return True

    def scrape_moulinettes(self, known_tests):
        result = None
        try:
            self.send_task_status({TaskType.MOULI: TaskStatus.LOADING})
            result = self.main.myepitech.fetch_student(self, known_tests=known_tests)
            self.send_task_status({TaskType.MOULI: TaskStatus.SUCCESS})
        except Exception as e:
            log_error(f"Failed to fetch MyEpitech data for student: {self.student_label}")
            self.send_task_status({TaskType.MOULI: TaskStatus.ERROR})
        return result

    def scrape_modules(self, known_modules):
        results = []
        try:
            self.send_task_status({TaskType.MODULES: TaskStatus.LOADING})
            all_modules = self.intranet.fetch_modules_list(self)
            for module in all_modules:
                if len([m for m in known_modules if m == module["id"]]) == 0:
                    m = self.main.intranet.fetch_module(module["scolaryear"], module["code"], module["codeinstance"], self)
                    m["id"] = module["id"] if "id" in module else None
                    results.append(m)
            self.send_task_status({TaskType.MODULES: TaskStatus.SUCCESS})
        except Exception as e:
            self.send_task_status({TaskType.MODULES: TaskStatus.ERROR})
            log_error(f"Failed to fetch Modules data for student: {self.student_label}")
        return results

    def scrape_intra_profile(self):
        profile = None
        try:
            self.send_task_status({TaskType.PROFILE: TaskStatus.LOADING})
            profile = self.main.intranet.fetch_student(self)
            self.send_task_status({TaskType.PROFILE: TaskStatus.SUCCESS})
        except Exception as e:
            log_error(f"Failed to fetch Intranet data for student: {self.student_label}")
        return profile

    def scrape_intra_planning(self, start, end):
        planning = None
        try:
            self.send_task_status({TaskType.PLANNING: TaskStatus.LOADING})
            planning = self.main.intranet.fetch_planning(self, start, end)
            self.send_task_status({TaskType.PLANNING: TaskStatus.SUCCESS})
        except Exception as e:
            log_error(f"Failed to fetch Intranet planning for student: {self.student_label}")
        return planning

    def scrape_intra_projects(self, start_date, end_date):
        projects = None
        try:
            self.send_task_status({TaskType.PROJECTS: TaskStatus.LOADING})
            projects = self.main.intranet.fetch_projects(self, start_date, end_date)
            self.send_task_status({TaskType.PROJECTS: TaskStatus.SUCCESS})
        except Exception as e:
            self.send_task_status({TaskType.PROJECTS: TaskStatus.ERROR})
            log_error(f"Failed to fetch Intranet projects for student: {self.student_label}")
        return projects