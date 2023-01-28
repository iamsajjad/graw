
from dataclasses import dataclass

@dataclass
class Version:

    MAJOR = 0
    MINOR = 1
    PATCH = 0

    STRING = f"{MAJOR}.{MINOR}.{PATCH}"
