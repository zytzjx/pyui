from PyQt5.QtCore import Qt,QPoint
from dataclasses import dataclass

@dataclass
class profile:
    profilename: str
    filename:str

    def __init__(self, profilename: str, filename: str):
        self.profilename = profilename
        self.filename = filename

@dataclass
class screw:
    profilename: str
    filename: str
    Centerpoint: QPoint
    lefttop: QPoint
    rightbottom: QPoint

    def __init__(self, profilename: str, filename: str, cp: QPoint, lt: QPoint, rb: QPoint):
        self.profilename = profilename
        self.filename = filename    
        self.Centerpoint = cp
        self.lefttop = lt
        self.rightbottom = rb


