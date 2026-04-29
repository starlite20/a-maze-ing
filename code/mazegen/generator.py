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
    pattern: bool = False

    def get_position(self) -> tuple[int, int]:
        return (self.x, self.y)

    def remove_wall(self, direction: Direction) -> None:
        self.walls &= ~direction


class MazeGenerator:
    def __init__(
        self, width: int, height: int,
        entry_pos: tuple[int, int], exit_pos: tuple[int, int],
        perfect: bool, seed: int, pattern_42: bool = False
    ) -> None:
        self.set_width(width)
        self.set_height(height)
        self.set_entry_exit_pos(entry_pos, exit_pos)
        self.set_perfect(perfect)
        self.set_seed(seed)
        self.set_pattern_42(pattern_42)
        self.grid: list[list[Cell]] = []

    # =============================
    # custom validators
    def set_width(self, width: int):
        if not isinstance(width, int) or width < 2:
            raise ValueError(f"Width must be an integer >= 2. Got: {width}")
        self.width = width

    def set_height(self, height: int):
        if not isinstance(height, int) or height < 2:
            raise ValueError(f"Height must be an integer >= 2. Got: {height}")
        self.height = height

    def _is_valid_coord(self, coord: tuple[int, int], name: str) -> None:
        if not (isinstance(coord, tuple) and len(coord) == 2 and
                all(isinstance(i, int) for i in coord)):
            raise ValueError(
                f"{name} must be a tuple of two integers. Got: {coord}")
        x, y = coord
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(
                f"{name} coordinates out of bounds. Got: {coord}")

    def set_entry_exit_pos(self, entry_pos: tuple[int, int], exit_pos: tuple[int, int]) -> None:
        self._is_valid_coord(entry_pos, "Entry")
        self._is_valid_coord(exit_pos, "Exit")

        if entry_pos == exit_pos:
            raise ValueError("Entry and Exit coordinates must be different.")

        self.entry = entry_pos
        self.exit = exit_pos

    def set_perfect(self, perfect: bool) -> None:
        if not isinstance(perfect, bool):
            raise ValueError(
                f"Perfect must be a boolean. Got: {type(perfect)}"
            )
        self.perfect = perfect

    def set_seed(self, seed: int) -> None:
        if seed is not None and not isinstance(seed, int):
            raise ValueError(
                f"Seed must be an integer or None. Got: {type(seed)}"
            )
        self.seed = seed if seed > 0 else random.randint(0, 2**32 - 1)

    def set_pattern_42(self, embed_pattern: bool = False) -> None:
        if not isinstance(embed_pattern, bool):
            raise ValueError(
                f"Perfect must be a boolean. Got: {type(embed_pattern)}"
            )
        self.embed_pattern = embed_pattern

    # =============================
    # maze generation

    def create_grid(self) -> None:
        self.grid = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                new_cell = Cell(x, y)
                new_cell.visited = False
                new_cell.pattern = False
                row.append(new_cell)
            self.grid.append(row)

    def print_grid(self) -> None:
        for row in self.grid:
            print("".join([f"{cell.walls:X}" for cell in row]))

    def get_unvisited_neighbours(self, x, y) -> list[Cell]:
        neighbours = []

        # North (x, y-1)
        if y > 0 and not self.grid[y-1][x].visited and not self.grid[y-1][x].pattern:
            neighbours.append(self.grid[y-1][x])

        # East (x+1, y)
        if x < self.width - 1 and not self.grid[y][x+1].visited and not self.grid[y][x+1].pattern:
            neighbours.append(self.grid[y][x+1])

        # South (x, y+1)
        if y < self.height - 1 and not self.grid[y+1][x].visited and not self.grid[y+1][x].pattern:
            neighbours.append(self.grid[y+1][x])

        # West (x-1, y)
        if x > 0 and not self.grid[y][x-1].visited and not self.grid[y][x-1].pattern:
            neighbours.append(self.grid[y][x-1])

        return neighbours

    def _remove_walls(self, current: Cell, next_cell: Cell):
        # calculate the difference in position to find direction
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

        if self.embed_pattern:
            self.embed_42_pattern()

        if algorithm == "DFS":
            self._generate_maze_DFS()
        else:
            pass

        if not self.perfect:
            self._generate_imperfections()
        pass

    def _generate_maze_DFS(self) -> None:
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

    def _generate_imperfections(self) -> None:
        # consider only n-1 rows and columns. ignoring the last.
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

            if current_cell.pattern or neighbor_cell.pattern:
                continue

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

    # =============================
    # Maze Solving Algorithm One - BFS
    # suitable for finding one path only... therefore, best for perfect maze.
    def solve_maze(self):
        if not self.grid:
            raise ValueError("Maze not generated yet...")

        start_x, start_y = self.entry
        end_x, end_y = self.exit

        grid_visit_flag = [[False for _ in range(
            self.width)] for _ in range(self.height)]

        grid_visit_flag[start_y][start_x] = True

        # dictionary to keep track of path each cell was reached from.
        cell_from = {}
        cell_from[(start_x, start_y)] = None

        # to keep track of the nodes we currently traversed
        queue = [(start_x, start_y)]

        moves = [
            (Direction.NORTH, 0, -1, "N"),
            (Direction.EAST, 1, 0, "E"),
            (Direction.SOUTH, 0, 1, "S"),
            (Direction.WEST, -1, 0, "W")
        ]

        while len(queue) > 0:
            current_x, current_y = queue.pop(0)

            if current_x == end_x and current_y == end_y:
                break

            current_cell = self.grid[current_y][current_x]

            for direction, dir_x, dir_y, dir_txt in moves:
                next_x = current_x + dir_x
                next_y = current_y + dir_y

                if 0 <= next_x < self.width and 0 <= next_y < self.height:
                    if not current_cell.walls & direction:
                        if not grid_visit_flag[next_y][next_x]:
                            grid_visit_flag[next_y][next_x] = True

                            cell_from[(next_x, next_y)] = (
                                current_x, current_y, dir_txt)
                            queue.append((next_x, next_y))

        # Retracing Path
        path = []
        step = (end_x, end_y)

        while step is not None:
            data = cell_from.get(step)

            # if none, it means we reached the start point
            if data is None:
                break

            prev_x, prev_y, prev_dir_txt = data
            path.append(prev_dir_txt)
            step = (prev_x, prev_y)

        path.reverse()
        return "".join(path)

    # =============================
    # 42 Pattern Embedding

    def embed_42_pattern(self):
        pattern_map = [
            "1000111",
            "1000001",
            "1110111",
            "0010100",
            "0010111"
        ]

        pattern_width = len(pattern_map[0])
        pattern_height = len(pattern_map)

        if self.width < pattern_width or self.height < pattern_height:
            raise ValueError("Maze too small to embed '42' pattern.")

        pattern_start_x = (self.width // 2) - (pattern_width // 2)
        pattern_start_y = (self.height // 2) - (pattern_height // 2)

        blocked_coords = []

        for y_offset, row in enumerate(pattern_map):
            for x_offset, point in enumerate(row):
                if point == "1":
                    blocked_coords.append(
                        (pattern_start_x + x_offset, pattern_start_y + y_offset))

        if self.entry in blocked_coords:
            raise ValueError(
                f"Entry {self.entry} conflicts with '42' pattern.")
        if self.exit in blocked_coords:
            raise ValueError(
                f"Exit {self.exit} conflicts with '42' pattern.")

        for (x, y) in blocked_coords:
            if 0 <= y < self.height and 0 <= x < self.width:
                self.grid[y][x].visited = True
                self.grid[y][x].pattern = True
