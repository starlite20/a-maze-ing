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


class MazeGenerator:
    def __init__(
        self, width: int, height: int,
        entry: tuple[int, int], exit_pos: tuple[int, int],
        perfect: bool, seed: int
    ) -> None:

        if not isinstance(width, int) or width < 2:
            raise ValueError(f"Width must be an integer >= 2. Got: {width}")
        self.width = width

        if not isinstance(height, int) or height < 2:
            raise ValueError(f"Height must be an integer >= 2. Got: {height}")
        self.height = height

        def is_valid_coord(coord: tuple[int, int], name: str) -> None:
            if not (isinstance(coord, tuple) and len(coord) == 2 and
                    all(isinstance(i, int) for i in coord)):
                raise ValueError(
                    f"{name} must be a tuple of two integers. Got: {coord}")
            x, y = coord
            if not (0 <= x < self.width and 0 <= y < self.height):
                raise ValueError(
                    f"{name} coordinates out of bounds. Got: {coord}")

        is_valid_coord(entry, "Entry")
        is_valid_coord(exit_pos, "Exit")

        if entry == exit_pos:
            raise ValueError("Entry and Exit coordinates must be different.")

        self.entry = entry
        self.exit = exit_pos

        if not isinstance(perfect, bool):
            raise ValueError(
                f"Perfect must be a boolean. Got: {type(perfect)}"
                )
        self.perfect = perfect

        if seed is not None and not isinstance(seed, int):
            raise ValueError(
                f"Seed must be an integer or None. Got: {type(seed)}"
                )
        self.seed = seed if seed > 0 else random.randint(0, 2**32 - 1)

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

    def generate_maze(self, algorithm: str = "DFS"):
        self.create_grid()

        if algorithm == "DFS":
            self._generate_maze_DFS()
        else:
            pass

        if not self.perfect:
            self._generate_imperfections()
        pass

    def _generate_maze_DFS(self) -> None:
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

    def _is_3x3_open(self, center_cell_col: int, center_cell_row: int) -> bool:
        # if the surrounding neighbour has the chance of crossing border, it means its not a 3x3 open space
        if (center_cell_col - 1 < 0 or center_cell_col + 1 >= self.width or
                center_cell_row - 1 < 0 or center_cell_row + 1 >= self.height):
            return False

        # checking all 6 internal EAST - rightside - walls
        # checking top mid and bottom rows
        for row_offset in range(-1, 2):
            # checking left and mid cols
            for col_offset in range(-1, 1):
                col = center_cell_col + col_offset
                row = center_cell_row + row_offset

                # we're doing bitwise operator check here
                # walls sum value   AND   east value
                if self.grid[row][col].walls & Direction.EAST:
                    return False

        # similarly checking 6 internal SOUTH - bottomside - walls.
        # checking top mid
        for row_offset in range(-1, 1):
            # checking left and mid and right cols
            for col_offset in range(-1, 2):
                col = center_cell_col + col_offset
                row = center_cell_row + row_offset

                # walls sum value   AND   south value
                if self.grid[row][col].walls & Direction.SOUTH:
                    return False

        # if no internal East or South walls were found, it's a 3x3 open area
        return True

    # working on this imperfection creator by making the algorithm consider only n-1 rows and columns. ignoring the last.
    def _generate_imperfections(self) -> None:
        imperfectness_factor = 5

        internal_walls = ((self.width - 1) * self.height) + \
            (self.width * (self.height - 1))
        walls_to_remove = int(internal_walls * imperfectness_factor * 0.01)

        removed_count = 0

        while removed_count < walls_to_remove:
            random_cell_x = random.randint(0, self.width - 1)
            random_cell_y = random.randint(0, self.height - 1)

            # as we are ignoring the last row and column, we will focus on eliminating walls on the right and down only.
            # creating a safe approach.
            neighbor_x = random_cell_x
            neighbor_y = random_cell_y
            direction = random.choice([Direction.EAST, Direction.SOUTH])
            if direction == Direction.EAST and random_cell_x < self.width - 1:
                neighbor_x += 1
            elif direction == Direction.SOUTH and random_cell_y < self.height - 1:
                neighbor_y += 1
            else:
                continue
                # direction chosen will hit a border, ignore iteration.

            current_cell = self.grid[random_cell_y][random_cell_x]
            neighbor_cell = self.grid[neighbor_y][neighbor_x]

            if not (current_cell.walls & direction):
                # if wall doesnt exist, skip this iteration
                continue

            # LARGE CORRIDOR CHECK
            # We check the 3x3 box centered on the CURRENT cell, AND the NEIGHBOR cell.
            if self._is_3x3_open(random_cell_x, random_cell_y) or self._is_3x3_open(neighbor_x, neighbor_y):
                continue
                # skip this iteration as this is a large corridor.

            # all safe... remove walls
            self._remove_walls(current_cell, neighbor_cell)
            removed_count += 1


# if __name__ == "__main__":
#     # print("Welcome to the Maze Generator!")
#     # print("Enter the following values in a comma separted manner")
#     # print("height_size, width_size, entry_x, entry_y, end_x, end_y, perfect_maze_bool")
#     # inputs = input()
#     # height, width, entry_x, entry_y, end_x, end_y, perfect_maze_bool = inputs.split(',').strip()
#     # mg = MazeGenerator(height, width, (entry_x, entry_y), (end_x, end_y), perfect_maze_bool, seed=3)

#     mg = MazeGenerator(10, 10, (0, 0), (9, 9), False, seed=3)
#     mg.generate_maze("DFS")
#     mg.print_grid()
#     print()
#     mg.display_maze("ASCII")
#     mg.print_grid()
#     print()
