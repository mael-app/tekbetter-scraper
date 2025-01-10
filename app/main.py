import json

from app.intranet.intranet_api import IntranetApi
from app.intranet.intranet_manager import IntranetManager
from app.model.Student import Student
from app.myepitech.myepitech_manager import MyEpitechManager

class Main:
    def __init__(self):
        self.students = []
        self.student_interval = 0

        self.myepitech = MyEpitechManager()
        self.intranet = IntranetManager()

        self.load_config()

    def load_config(self):
        conf = json.loads(open("../config.json", "r").read())
        self.student_interval = conf["student_interval"] if "student_interval" in conf else 60
        if not "students" in conf:
            raise Exception("No students in config")
        for student in conf["students"]:
            if not "microsoft_session" in student or not "tekbetter_token" in student:
                raise Exception("Invalid student in config (missing microsoft_session or tekbetter_token)")
            student_obj = Student()
            student_obj.microsoft_session = student["microsoft_session"]
            student_obj.tekbetter_token = student["tekbetter_token"]
            self.students.append(student_obj)

    def sync_student(self, student):
        myepitech_data = self.myepitech.fetch_student(student, [])
        print(myepitech_data)
