import time

import requests

from app.config import INTRANET_LOGIN_URL
from app.logger import log_info, log_error
from app.model.Student import Student, TaskType, TaskStatus


class IntranetLoginError(Exception):
    pass


class IntranetNotFoundError(Exception):
    pass


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0"
}


def _build_cookies(cookies: dict, student: Student):
    """
    Build the cookies dict for the antiddos page
    :param cookies: List of cookies tuples
    :return: dict
    """
    if cookies is None:
        cookies = {}
    cookies_dict = student.antiddos.saved_cookies
    cookies_dict.update(cookies)
    return cookies_dict


def pass_antiddos(student: Student):
    """
    Pass the anti-ddos page
    """
    log_info("Trying to pass the anti-ddos page")
    student.antiddos.regenerate_cookies()
    log_info("Anti-ddos page passed")


class IntranetApi:
    def __init__(self):
        pass

    def login(self, student: Student, allow_retry=True):
        """
        Create a intra.epitech.eu session using the given Microsoft cookies
        :param allow_retry:
        :param student: Student object
        :return: string token if the session is created
        """
        log_info(f"[INTRA] Logging in the intranet of user {student.student_label}")

        # Microsoft request
        msoft_resp = requests.get(
            INTRANET_LOGIN_URL,
            cookies=_build_cookies({"ESTSAUTHPERSISTENT": student.microsoft_session}, student),
            headers=DEFAULT_HEADERS,
            allow_redirects=False
        )

        if msoft_resp.status_code != 302:
            student.err_scrap("Invalid Microsoft session for the student.")
            student.last_failed_auth = time.time()
            student.send_task_status({TaskType.AUTH: TaskStatus.ERROR})
            raise Exception(f"Invalid Microsoft session for the student: {student.student_label}")

        # Get the "Location" response header
        location = msoft_resp.headers.get("Location")
        intra_resp = requests.get(location, headers=DEFAULT_HEADERS, cookies=_build_cookies({}, student),
                                  allow_redirects=False)

        if intra_resp.status_code == 503:  # Anti-ddos page
            if allow_retry:
                pass_antiddos(student)
                return self.login(student, allow_retry=False)
            student.err_scrap("AntiDDoS already passed, but still got a 503 error")
            student.last_failed_auth = time.time()
            raise Exception("AntiDDoS already passed, but still got a 503 error")

        if intra_resp.status_code not in [204, 302]:
            student.err_scrap(f"Failed to login to Intranet API for the student: {student.student_label}")
            raise IntranetLoginError(f"Failed to login to Intranet API for the student: {student.student_label}")

        # Extract the token from the Set-Cookie header
        set_cookie = intra_resp.headers.get("Set-Cookie", "")
        if "user=" not in set_cookie:
            log_error(f"Failed to login to Intranet API for the student: {student.student_label}")
            raise IntranetLoginError(f"Failed to login to Intranet API for the student: {student.student_label}")

        token = set_cookie.split("user=")[1].split(";")[0]
        student.intra_token = token
        student.send_task_status({TaskType.AUTH: TaskStatus.SUCCESS})
        return token

    def api_request(self, url, student_obj: Student, allow_retry=True, timeout=60):
        if student_obj.intra_token is None:
            self.login(student_obj)

        res = requests.get(
            f"https://intra.epitech.eu/{url}",
            headers=DEFAULT_HEADERS,
            cookies=_build_cookies({"user": student_obj.intra_token}, student_obj),
            timeout=timeout
        )

        if res.status_code == 200:
            content_type = res.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return res.json()
            if content_type == "image/jpeg":
                # return image bytes
                return res.content
            raise Exception("Invalid content type")

        if res.status_code == 503:
            if allow_retry:
                pass_antiddos(student_obj)
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