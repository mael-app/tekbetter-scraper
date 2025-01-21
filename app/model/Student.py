from app.intranet.intranet_antiddos_bypass import IntranetAntiDDoSBypasser


class Student:
    microsoft_session: str
    tekbetter_token: str = None
    myepitech_token: str = None
    intra_token: str = None
    last_sync: int = 0
    student_label: str = None
    antiddos: IntranetAntiDDoSBypasser = None