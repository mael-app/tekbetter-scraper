import re
import base64
import requests
import urllib.parse
import execjs

from app.config import USER_AGENT


def decode_js_content(encoded_str: str) -> str:
    # Équivalent Python de decodeURIComponent(escape(...))
    try:
        escaped_str = encoded_str.encode('latin1').decode('unicode_escape')
        decoded_str = urllib.parse.unquote(escaped_str)
        return decoded_str
    except Exception as e:
        return f"Erreur lors du décodage : {e}"


class IntranetAntiDDoSBypasser:
    def __init__(self):
        self.cookies = {}
        self.headers = {}
        self.saved_cookies = {}

    def extract_cookies_from_response(self, resp: requests.Response):
        for cookie in resp.cookies:
            self.cookies[cookie.name] = cookie.value

    def regenerate_cookies(self):
        for _ in range(7):
            try:
                cookies = self.try_pass()
                self.saved_cookies = cookies
                return cookies
            except Exception:
                continue  # Silencieux volontairement, on retente
        raise Exception("Failed to regenerate anti-ddos cookies")

    def try_pass(self):
        self.cookies = {}
        self.headers = {"User-Agent": USER_AGENT}

        # Get the first response, containing the javascript puzzle and the first cookie
        resp = requests.get("https://intra.epitech.eu/", headers=self.headers)
        self.extract_cookies_from_response(resp)

        js_puzzle = None

        # Check if the response contains the javascript puzzle
        if "eval(decodeURIComponent(escape(window.atob(" in resp.text:
            try:
                b64_data = resp.text.split("eval(decodeURIComponent(escape(window.atob('")[1].split("'))))")[0]
                js_puzzle = base64.b64decode(b64_data).decode("utf-8")
            except Exception:
                raise Exception("Failed to decode base64 puzzle content")
        elif "eval(decodeURIComponent(escape" in resp.text:
            try:
                encoded_data = resp.text.split("eval(decodeURIComponent(escape('")[1].split("'))")[0]
                js_puzzle = decode_js_content(encoded_data)
            except Exception:
                raise Exception("Failed to decode js content")

        if not js_puzzle:
            raise Exception("Failed to extract the javascript puzzle")

        # What is secret header ?
        # It's a header needed for the 2nd request, it's value is calculated with a random-variable-name.
        sh_variable_name, sh_value = self._extract_secretheader(js_puzzle)

        # Extract all other headers
        self._extract_all_headers(js_puzzle)

        # Extract the document.cookie from the javascript code
        self._extract_document_cookie(js_puzzle)

        # Replace the header that contains the variable_name as value, by the secret header real value
        self.headers = {
            k: v.replace(sh_variable_name, str(sh_value)) for k, v in self.headers.items()
        }

        # Make the second request
        # We don't know why the data should be "name1=Henry&name2=Ford", but it works.
        resp = requests.post(
            "https://intra.epitech.eu/",
            headers=self.headers,
            cookies=self.cookies,
            data="name1=Henry&name2=Ford"
        )

        if resp.status_code != 204:
            raise Exception("Failed to pass the anti-ddos page")

        self.extract_cookies_from_response(resp)

        # Now we can use all the cookies to make requests to the intranet
        return self.cookies

    def _extract_secretheader(self, text: str):
        # Example: var _9631010 = parseInt("20250108", 10) + parseInt("08012025", 10);
        row = next((line for line in text.split("\n") if "parseInt" in line), None)
        if not row:
            raise Exception("No parseInt row found in JS")

        executable_row = row.split("=", 1)[1].replace(";", "").strip()
        variable_name = row.split("=")[0].strip().replace("var ", "")
        row_js = f"const a = () => {executable_row}"
        result = execjs.compile(row_js).call("a")
        return variable_name, result

    def _extract_all_headers(self, text: str):
        # Extract headers from javascript code (xhttp.setRequestHeader calls)
        rows = []
        skip_next = False

        for line in text.split("\n"):
            if "xhttp.setRequestHeader" in line and not skip_next:
                rows.append(line)
            if "(v==true)" in line.replace(" ", ""):
                skip_next = True

        header_lines = "\n".join(rows)
        pattern = re.compile(r"\(([^,]+?),\s*(.+?)\)")
        matches = pattern.findall(header_lines)

        for key, value in matches:
            clean_key = key.strip("'\" ")
            clean_value = value.strip("'\" ")
            self.headers[clean_key] = clean_value

    def _extract_document_cookie(self, text: str):
        # Extract the document.cookie from the javascript code
        cookie_rows = [line for line in text.split("\n") if "document.cookie = " in line]

        for row in cookie_rows:
            try:
                cookie = row.split("document.cookie = '")[1].split("' + ")[0]
                name, value = cookie.split("=")
                self.cookies[name.strip()] = value.strip()
            except Exception:
                continue  # Ignore malformed rows silently