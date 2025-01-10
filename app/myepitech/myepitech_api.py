import requests

from app.config import MYEPITECH_LOGIN_URL
from app.model.Student import Student


class MyEpitechLoginError(Exception):
    pass


class MyEpitechNotFoundError(Exception):
    pass


class MyEpitechApi:
    def __init__(self):
        pass
        # self.microsoft_cookies = {
        #     'ESTSAUTHPERSISTENT': '',
        # }

    def login(self, student):
        """
        Create a my.epitech.eu session using the given Microsoft cookies
        :param student: Student object
        :return: string token if the session is created
        """
        request = requests.get(MYEPITECH_LOGIN_URL, cookies={
            "ESTSAUTHPERSISTENT": student.microsoft_session
        })
        if request.status_code != 200:
            raise Exception("Failed to create myepitech session")
        # Get the "Location" response header
        location = request.url
        # Extract the token from the location
        token = location.split("id_token=")[1].split("&")[0]
        student.myepitech_token = token
        return token

    def api_request(self, url, student_obj: Student, allow_retry=True):
        if student_obj.myepitech_token is None:
            self.login(student_obj)
        res = requests.get(f"https://api.epitest.eu/{url}",
                           headers={"Authorization": f"Bearer {student_obj.myepitech_token}", "Content-Type": "application/json"})
        if res.status_code == 200:
            return res.json()

        if res.status_code == 403:
            if allow_retry:
                self.login(student_obj)
                return self.api_request(url, student_obj, allow_retry=False)
            raise MyEpitechLoginError("Failed to login to MyEpitech API")

        if res.status_code == 404:
            raise MyEpitechNotFoundError("Resource not found")

        raise Exception(f"Failed to fetch data from MyEpitech API: {res.status_code}")
