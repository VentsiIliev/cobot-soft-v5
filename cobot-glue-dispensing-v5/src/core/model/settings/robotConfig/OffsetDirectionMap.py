from dataclasses import dataclass

@dataclass
class OffsetDirectionMap:
    """Represents direction-following states for TCP offset correction"""
    pos_x: bool = True
    neg_x: bool = True
    pos_y: bool = True
    neg_y: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> 'OffsetDirectionMap':
        """Create an OffsetDirectionMap from a dict"""
        return cls(
            pos_x=data.get("+X", True),
            neg_x=data.get("-X", True),
            pos_y=data.get("+Y", True),
            neg_y=data.get("-Y", True)
        )

    def to_dict(self) -> dict:
        """Convert OffsetDirectionMap to dict for JSON"""
        return {
            "+X": self.pos_x,
            "-X": self.neg_x,
            "+Y": self.pos_y,
            "-Y": self.neg_y
        }