from enum import Enum

class SummaryType(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class Client(str, Enum):
    PACKBACK = "packback"
    CHICORY = "chicory"
    GEPETO = "gepeto"