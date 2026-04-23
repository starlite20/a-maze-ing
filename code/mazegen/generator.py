import random
from .cell import Cell


class MazeGenerator:
    def __init__(self, width: int, height: int, entry: tuple[int, int], exit_pos: tuple[int, int], perfect: bool, seed: int = None):
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self.grid: list[list[Cell]] = []

    def create_grid(self) -> None:
        # Nested list comprehension for the 2D grid
        self.grid = [
            [Cell(x, y) for x in range(self.width)]
            for y in range(self.height)
        ]

    def print_grid(self) -> None:
        for row in self.grid:
            print("".join([f"{cell.walls:X}" for cell in row]))


if __name__ == "__main__":
    mg = MazeGenerator(10, 10, (0, 0), (9, 9), True, "maze.txt")
    mg.create_grid()
    mg.print_grid()
