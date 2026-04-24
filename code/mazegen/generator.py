from enum import IntFlag
from dataclasses import dataclass
import random


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


class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GREY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class MazeGenerator:
    def __init__(self, width: int, height: int, entry: tuple[int, int], exit_pos: tuple[int, int], perfect: bool, seed: int = None):
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit_pos
        self.perfect = perfect
        self.seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self.color_mode = 0
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

    def display_maze(self) -> None:
        self.show_ascii_maze()

    def show_ascii_maze(self) -> None:
        WALL = "█"
        SPACE = " "

        def colored(content: str, color: str) -> str:
            return color + content + Color.RESET

        def cell_content(row: int, column: int) -> str:
            # Must be exactly 3 visible characters wide
            if (row, column) == self.entry:
                content = "[] "
                if self.color_mode == 1:
                    return colored(content, Color.GREY)
                return colored(content, Color.PURPLE + Color.BOLD)

            if (row, column) == self.exit:
                content = "[] "
                if self.color_mode == 1:
                    return colored(content, Color.GREY)
                return colored(content, Color.RED + Color.BOLD)

            return "   "

        for row in range(self.height):
            top_line = WALL

            for column in range(self.width):
                if self.grid[row][column].walls & Direction.NORTH:
                    top_line += WALL * 3
                else:
                    top_line += SPACE * 3

                # Corner / separator
                top_line += WALL

            print(top_line)

            # Draw the west/east walls and cell contents
            mid_line = ""

            for column in range(self.width):
                if self.grid[row][column].walls & Direction.WEST:
                    mid_line += WALL
                else:
                    mid_line += SPACE

                mid_line += cell_content(row, column)

            # Add the far-right east wall of the last cell
            if self.grid[row][self.width - 1].walls & Direction.EAST:
                mid_line += WALL
            else:
                mid_line += SPACE

            print(mid_line)

        # Draw the bottom south walls
        bottom_line = WALL

        for column in range(self.width):
            if self.grid[self.height - 1][column].walls & Direction.SOUTH:
                bottom_line += WALL * 3
            else:
                bottom_line += SPACE * 3

            bottom_line += WALL

        print(bottom_line)

    def get_unvisited_neighbours(self, x, y) -> list[Cell]:
        neighbours = []

        # North (x, y-1)
        if y > 0 and not self.grid[y-1][x].visited:
            neighbours.append(self.grid[y-1][x])

        # East (x+1, y)
        if x < self.width - 1 and not self.grid[y][x+1].visited:
            neighbours.append(self.grid[y][x+1])

        # South (x, y+1)
        if y < self.height - 1 and not self.grid[y+1][x].visited:
            neighbours.append(self.grid[y+1][x])

        # West (x-1, y)
        if x > 0 and not self.grid[y][x-1].visited:
            neighbours.append(self.grid[y][x-1])

        return neighbours

    def _remove_walls(self, current: Cell, next_cell: Cell):
        # Calculate the difference in position to find direction
        dx = current.x - next_cell.x
        dy = current.y - next_cell.y

        # Next is to the West
        if dx == 1:
            current.remove_wall(Direction.WEST)
            next_cell.remove_wall(Direction.EAST)

        # Next is to the East
        elif dx == -1:
            current.remove_wall(Direction.EAST)
            next_cell.remove_wall(Direction.WEST)

        # Next is to the North
        if dy == 1:
            current.remove_wall(Direction.NORTH)
            next_cell.remove_wall(Direction.SOUTH)

        # Next is to the South
        elif dy == -1:
            current.remove_wall(Direction.SOUTH)
            next_cell.remove_wall(Direction.NORTH)

    def generate_maze_DFS(self) -> None:
        for row in self.grid:
            for cell in row:
                cell.visited = False

        start_cell = self.grid[self.entry[1]][self.entry[0]]
        start_cell.visited = True

        random.seed(self.seed)

        stack = [start_cell]
        while (len(stack) > 0):
            current = stack[-1]

            neighbours = self.get_unvisited_neighbours(current.x, current.y)
            if neighbours:
                next_cell_to_go = random.choice(neighbours)
                self._remove_walls(current, next_cell_to_go)

                next_cell_to_go.visited = True
                stack.append(next_cell_to_go)

            else:
                stack.pop()


if __name__ == "__main__":
    mg = MazeGenerator(20, 20, (0, 0), (9, 9), True, seed=42)
    mg.create_grid()
    mg.generate_maze_DFS()
    mg.print_grid()
    print()
    mg.display_maze()
