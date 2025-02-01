import os

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
