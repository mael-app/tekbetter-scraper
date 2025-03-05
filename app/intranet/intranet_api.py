import time

import requests

from app.config import INTRANET_LOGIN_URL, USER_AGENT
from app.intranet.intranet_antiddos_bypass import IntranetAntiDDoSBypasser
from app.logger import log_info, log_error
from app.model.Student import Student, TaskType, TaskStatus


class IntranetLoginError(Exception):
    pass


class IntranetNotFoundError(Exception):
    pass


HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0"
}


class IntranetApi:
    def __init__(self):
        pass

    def _build_cookies(self, cookies: dict, student: Student):
        """
        Build the cookies dict for the antiddos page
        :param cookies: List of cookies tuples
        :return: dict
        """
        if cookies is None:
            cookies = {}
        cookies_dict = student.antiddos.saved_cookies
        for key, value in cookies.items():
            cookies_dict[key] = value
        return cookies_dict

    def pass_antiddos(self, student: Student):
        """
        Pass the anti-ddos page
        """
        log_info("Trying to pass the anti-ddos page")
        student.antiddos.regenerate_cookies()
        log_info("Anti-ddos page passed")

    def login(self, student, allow_retry=True):
        """
        Create a intra.epitech.eu session using the given Microsoft cookies
        :param allow_retry:
        :param student: Student object
        :return: string token if the session is created
        """

        log_info("[INTRA] Logging in the intranet of user " + student.student_label)
        # Microsoft request
        msoft_resp = requests.get(INTRANET_LOGIN_URL, cookies=self._build_cookies({
            "ESTSAUTHPERSISTENT": student.microsoft_session
        }, student), headers=HEADERS, allow_redirects=False)

        if msoft_resp.status_code != 302:
            student.err_scrap(f"Invalid Microsoft session for the student.")
            student.last_failed_auth = time.time()
            student.send_task_status({TaskType.AUTH: TaskStatus.ERROR})
            raise Exception(f"Invalid Microsoft session for the student: {student.student_label}")
        # Get the "Location" response header
        location = msoft_resp.headers["Location"]
        intra_resp = requests.get(location, headers=HEADERS, cookies=self._build_cookies({}, student), allow_redirects=False)

        if intra_resp.status_code == 503: # Anti-ddos page
            if allow_retry:
                self.pass_antiddos(student)
                return self.login(student, allow_retry=False)
            student.err_scrap("AntiDDoS already passed, but still got a 503 error")
            student.last_failed_auth = time.time()
            raise Exception("AntiDDoS already passed, but still got a 503 error")
        if intra_resp.status_code not in [204, 302]:
            student.err_scrap(f"Failed to login to Intranet API for the student: {student.student_label}")
            raise IntranetLoginError(f"Failed to login to Intranet API for the student: {student.student_label}")
        # Extract the token from the Set-Cookie header
        if not "Set-Cookie" in intra_resp.headers:
            log_error(f"Failed to login to Intranet API for the student: {student.student_label}")
            raise IntranetLoginError(f"Failed to login to Intranet API for the student: {student.student_label}")
        token = intra_resp.headers["Set-Cookie"].split("user=")[1].split(";")[0]
        student.intra_token = token
        student.send_task_status({TaskType.AUTH: TaskStatus.SUCCESS})
        return token

    def api_request(self, url, student_obj: Student, allow_retry=True, timeout=60):
        if student_obj.intra_token is None:
            self.login(student_obj)
        res = requests.get(f"https://intra.epitech.eu/{url}", headers=HEADERS, cookies=self._build_cookies({
            "user": student_obj.intra_token
        }, student_obj), timeout=timeout)
        if res.status_code == 200:
            if "application/json" in res.headers["Content-Type"]:
                return res.json()
            if res.headers["Content-Type"] == "image/jpeg":
                # return image bytes
                return res.content
            raise Exception("Invalid content type")
        if res.status_code == 503:
            if allow_retry:
                self.pass_antiddos(student=student_obj)
                return self.api_request(url, student_obj, allow_retry=False, timeout=timeout)
            raise Exception("Failed to pass the anti-ddos page")

        if res.status_code == 403:
            if allow_retry:
                self.login(student_obj)
                return self.api_request(url, student_obj, allow_retry=False)
            raise IntranetLoginError("Failed to login to Intranet API")

        if res.status_code == 404:
            raise IntranetNotFoundError("Resource not found")

        raise Exception(f"Failed to fetch data from Intranet API: {res.status_code}")
