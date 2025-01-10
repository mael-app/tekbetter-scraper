import requests

from app.config import INTRANET_LOGIN_URL, USER_AGENT
from app.intranet.intranet_antiddos_bypass import IntranetAntiDDoSBypasser
from app.model.Student import Student


class IntranetLoginError(Exception):
    pass


class IntranetNotFoundError(Exception):
    pass


HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0"
}


class IntranetApi:
    def __init__(self):
        self.antiddos_bypasser = IntranetAntiDDoSBypasser()

    def _build_cookies(self, cookies: dict = {}):
        """
        Build the cookies dict for the antiddos page
        :param cookies: List of cookies tuples
        :return: dict
        """
        cookies_dict = self.antiddos_bypasser.saved_cookies
        for key, value in cookies.items():
            cookies_dict[key] = value
        return cookies_dict

    def pass_antiddos(self):
        """
        Pass the anti-ddos page
        """
        self.antiddos_bypasser.regenerate_cookies()

        # Test if the anti-ddos page is passed
        cookies = self._build_cookies({})
        test_resp = requests.get("https://intra.epitech.eu", headers=HEADERS, cookies=self._build_cookies())
        if test_resp.status_code != 403 and "Epitech" not in test_resp.text:
            raise Exception("Failed to pass the anti-ddos, post test not passed")
        print("Anti-DDoS passed")

    def login(self, student, allow_retry=True):
        """
        Create a intra.epitech.eu session using the given Microsoft cookies
        :param allow_retry:
        :param student: Student object
        :return: string token if the session is created
        """

        # Microsoft request
        msoft_resp = requests.get(INTRANET_LOGIN_URL, cookies=self._build_cookies({
            "ESTSAUTHPERSISTENT": student.microsoft_session
        }), headers=HEADERS, allow_redirects=False)
        # if msoft_resp.status_code == 503:
        #     if not allow_retry:
        #         raise Exception("Failed to pass the anti-ddos page")
        #     self.pass_antiddos()
        if msoft_resp.status_code != 302:
            raise Exception("Failed to create intranet session")
        # Get the "Location" response header
        location = msoft_resp.headers["Location"]
        intra_resp = requests.get(location, headers=HEADERS, cookies=self._build_cookies({}), allow_redirects=False)

        if intra_resp.status_code == 503: # Anti-ddos page
            if allow_retry:
                self.pass_antiddos()
                return self.login(student, allow_retry=False)
            raise Exception("Failed to pass the anti-ddos page")
        # Extract the token from the Set-Cookie header
        token = intra_resp.headers["Set-Cookie"].split("user=")[1].split(";")[0]
        student.intra_token = token
        return token

    def api_request(self, url, student_obj: Student, allow_retry=True):
        if student_obj.intra_token is None:
            self.login(student_obj)
        res = requests.get(f"https://intra.epitech.eu/{url}", headers=HEADERS, cookies=self._build_cookies({
            "user": student_obj.intra_token
        }))
        if res.status_code == 200:
            return res.json()
        if res.status_code == 503:
            if allow_retry:
                self.pass_antiddos()
                return self.api_request(url, student_obj, allow_retry=False)
            raise Exception("Failed to pass the anti-ddos page")

        if res.status_code == 403:
            if allow_retry:
                self.login(student_obj)
                return self.api_request(url, student_obj, allow_retry=False)
            raise IntranetLoginError("Failed to login to Intranet API")

        if res.status_code == 404:
            raise IntranetNotFoundError("Resource not found")

        raise Exception(f"Failed to fetch data from Intranet API: {res.status_code}")
