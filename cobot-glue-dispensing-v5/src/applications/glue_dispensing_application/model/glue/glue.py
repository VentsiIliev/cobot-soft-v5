from dataclasses import dataclass


@dataclass
class Glue:
    def __init__(self, name: str, description:str):
        self.name = name
        self.description = description

