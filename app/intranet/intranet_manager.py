from datetime import datetime

from app.intranet.intranet_api import IntranetApi
from app.model.Student import Student
from app.myepitech.myepitech_api import MyEpitechApi


class IntranetManager:
    def __init__(self):
        self.api = IntranetApi()

    def fetch_student(self, student: Student):
        return self.api.api_request("user/?format=json", student)
