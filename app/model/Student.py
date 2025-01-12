
class Student:
    microsoft_session: str
    tekbetter_token: str = None
    myepitech_token: str = None
    intra_token: str = None
    last_sync: int = 0
    student_label: str = None
    locked: bool = False # If the student is locked, it won't be synced