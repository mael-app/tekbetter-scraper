from datetime import datetime

from app.logger import log_info
from app.model.Student import Student
from app.myepitech.myepitech_api import MyEpitechApi


class LatestTest:
    last_id: int
    project_slug: str
    project_module: str
    year: int

class MyEpitechManager:
    def __init__(self):
        self.api = MyEpitechApi()


    def fetch_student(self, student: Student, known_tests: [int]):
        current_year = datetime.now().year
        years = [current_year - 2, current_year -1, current_year]
        new_tests = {}
        for year in years:
            all_projects = self.get_latest_from_year(student, year)
            new_projects = [p for p in all_projects if int(p.last_id) not in known_tests]
            for nproj in new_projects:
                history = self.get_project_history(student, nproj.year, nproj.project_slug, nproj.project_module)
                data = self.get_data_from_list(student=student, tests_obs=history, known_tests=known_tests)
                for key, value in data.items():
                    new_tests[key] = value
        return new_tests

    def _is_valid_project(self, project):
        if "project" not in project:
            return False
        if "slug" not in project["project"]:
            return False
        if "module" not in project["project"]:
            return False
        if "code" not in project["project"]["module"]:
            return False
        if "results" not in project:
            return False
        if "testRunId" not in project["results"]:
            return False
        return True

    def get_data_from_list(self, student: Student, tests_obs: [LatestTest], known_tests: [int], force_fetch=False):
        """
        Fetch data from a list of tests
        :param student:  Student object
        :param tests_obs:  List of LatestTest objects
        :param known_tests:  List of known tests
        :param force_fetch:
        :return:  Dict of test data (test_id: data)
        """
        tests_data = {}
        for test in tests_obs:
            if str(test.last_id) in known_tests and not force_fetch:
                continue
            data = self.get_test_data(student, test)
            tests_data[test.last_id] = data
        return tests_data

    def get_latest_from_year(self, student_obj, year: int):
        obj_tests = []
        projects_json = self.api.api_request(f"me/{year}", student_obj)

        for project in projects_json:
            if not self._is_valid_project(project):
                continue
            test = LatestTest()
            test.last_id = project["results"]["testRunId"]
            test.project_slug = project["project"]["slug"]
            test.project_module = project["project"]["module"]["code"]
            test.year = year
            obj_tests.append(test)
        return obj_tests

    def get_project_history(self, student, year: int, project_slug: str, project_module: str):
        obj_tests = []
        latest_projects_json = self.api.api_request(f"me/{year}/{project_module}/{project_slug}", student)
        for project in latest_projects_json:
            if not self._is_valid_project(project):
                continue
            test = LatestTest()
            test.last_id = project["results"]["testRunId"]
            test.project_slug = project["project"]["slug"]
            test.project_module = project["project"]["module"]["code"]
            test.year = year
            obj_tests.append(test)
        return obj_tests


    def get_test_data(self, student, test: LatestTest):
        log_info(f"Fetching data for test n°{test.last_id} ({test.project_slug}/{test.project_module}/{test.year})")
        test_data = self.api.api_request(f"me/details/{test.last_id}", student)
        return test_data
