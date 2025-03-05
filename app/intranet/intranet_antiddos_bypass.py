import re
import traceback

import execjs
import base64
import requests
import urllib.parse
from app.config import USER_AGENT

def decode_js_content(encoded_str):
    # Équivalent Python de decodeURIComponent(escape(...))
    try:
        # Escape avec .encode('latin1') pour simuler le comportement de escape
        # Puis décodage avec urllib.parse.unquote
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

    def extract_cookies_from_response(self, resp):
        for cookie in resp.cookies:
            self.cookies[cookie.name] = cookie.value

    def regenerate_cookies(self):
        for _ in range(7):
            try:
                cookies = self.try_pass()
                self.saved_cookies = cookies
                return cookies
            except Exception as e:
                pass
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
            # Extract the JS code from the HTML page (decode the base64 string)
            js_puzzle = base64.b64decode(resp.text.split("eval(decodeURIComponent(escape(window.atob('")[1].split("'))))")[0]).decode("utf-8")
        elif "eval(decodeURIComponent(escape" in resp.text:
            # Extract the JS code from the HTML page
            js_puzzle = decode_js_content(resp.text.split("eval(decodeURIComponent(escape('")[1].split("'))")[0])

        if js_puzzle is None:
            raise Exception("Failed to extract the javascript puzzle")


        # What is secret header ?
        # It's a header needed for the 2nd request, it's value is calculated with a random-variable-name.
        sh_variable_name, sh_value = self._extract_secretheader(js_puzzle)

        # Extract all others headers
        self._extract_all_headers(js_puzzle)

        # Extract the document.cookie from the javascript code
        self._extact_document_cookie(js_puzzle)

        # Replace the header who containns the varibale_name as value, by the secret header real value
        self.headers = {k: v.replace(sh_variable_name, str(sh_value)) for k, v in self.headers.items()}

        # Make the second request
        # We don't know why the data should be "name1=Henry&name2=Ford", but it works.
        resp = requests.post("https://intra.epitech.eu/", headers=self.headers, cookies=self.cookies, data="name1=Henry&name2=Ford")
        if resp.status_code != 204:
            raise Exception("Failed to pass the anti-ddos page")

        self.extract_cookies_from_response(resp)

        # Now ws can use all the cookies to make requests to the intranet
        return self.cookies

    def _extract_secretheader(self, text):
        # row example: var _9631010=parseInt("20250108", 10) + parseInt("08012025", 10);
        # Find the row that contains the parseInt function
        row = [a for a in text.split("\n") if "parseInt" in a][0]
        # Keep only the executable part of the row
        executable_row = row.split("=")[1].replace(";", "")
        # Extract the variable name
        variable_name = row.split("=")[0].strip().replace("var ", "")
        row = f"const a = () => {executable_row}"
        # Execute the javascript code
        result = execjs.compile(row).call("a")
        return variable_name, result

    def _extract_all_headers(self, text):
        # Extract headers from javascript code (using the xhttp.setRequestHeader function)
        rows = []
        #rows = "\n".join([a for a in text.split("\n") if "xhttp.setRequestHeader" in a])
        skip_next = False
        for a in text.split("\n"):
            if "xhttp.setRequestHeader" in a and not skip_next:
                rows.append(a)
            # Don't extract the trapped header, located at the row after "if (v == true) {"
            if "(v==true)" in a.replace(" ", ""):
                skip_next = True
        rows = "\n".join(rows)

        pattern = re.compile(r"\(([^,]+?),\s*(.+?)\)")
        matches = pattern.findall(rows)
        result = []
        for match in matches:
            cleaned_tuple = tuple(item.strip("'\" ") for item in match)
            result.append(cleaned_tuple)
        for t in result:
            self.headers[t[0]] = t[1]

    def _extact_document_cookie(self, text):
        # Extract the document.cookie from the javascript code
        # Get rows who contains the document.cookie
        rows = [a for a in text.split("\n") if "document.cookie = " in a]
        # Extract the cookie name and value
        for row in rows:
            cookie = row.split("document.cookie = '")[1].split("' + ")[0]
            name, value = cookie.split("=")
            self.cookies[name] = value