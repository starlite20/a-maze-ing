
from enum import IntFlag
from dataclasses import dataclass


class Direction(IntFlag):
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8


@dataclass
class Cell:
    x: int
    y: int
    walls: int = 15
    visited: bool = False

    def remove_wall(self, direction: Direction) -> None:
        self.walls &= ~direction
