from enum import IntFlag
from dataclasses import dataclass
import random
import json
from collections import deque


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
        self.history: list[dict] = []

    # =============================
    # custom validators
    def set_width(self, width: int) -> None:
        if not isinstance(width, int) or width < 2:
            raise ValueError(f"Width must be an integer >= 2. Got: {width}")
        self.width = width

    def set_height(self, height: int) -> None:
        if not isinstance(height, int) or height < 2:
            raise ValueError(f"Height must be an integer >= 2. Got: {height}")
        self.height = height

    def _is_valid_coord(self,
                        coord: tuple[int, int],
                        name: str) -> None:
        if not (isinstance(coord, tuple) and len(coord) == 2 and
                all(isinstance(i, int) for i in coord)):
            raise ValueError(
                f"{name} must be a tuple of two integers. Got: {coord}")
        x, y = coord
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(
                f"{name} coordinates out of bounds. Got: {coord}")

    def set_entry_exit_pos(self,
                           entry_pos: tuple[int, int],
                           exit_pos: tuple[int, int]
                           ) -> None:
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

    def set_seed(self, seed: int | None) -> None:
        if seed is not None and not isinstance(seed, int):
            raise ValueError(
                f"Seed must be an integer or None. Got: {type(seed)}"
            )
        self.seed = seed

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
        if (y > 0
            and not self.grid[y-1][x].visited
                and not self.grid[y-1][x].pattern):
            neighbours.append(self.grid[y-1][x])

        # East (x+1, y)
        if (x < self.width - 1
            and not self.grid[y][x+1].visited
                and not self.grid[y][x+1].pattern):
            neighbours.append(self.grid[y][x+1])

        # South (x, y+1)
        if (y < self.height - 1
            and not self.grid[y+1][x].visited
                and not self.grid[y+1][x].pattern):
            neighbours.append(self.grid[y+1][x])

        # West (x-1, y)
        if (x > 0
            and not self.grid[y][x-1].visited
                and not self.grid[y][x-1].pattern):
            neighbours.append(self.grid[y][x-1])

        return neighbours

    def _remove_walls(self, current: Cell, next_cell: Cell) -> None:
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

    def generate_maze(self, algorithm: str = "DFS") -> None:
        self.create_grid()

        if self.embed_pattern:
            self.embed_42_pattern()

        if algorithm == "DFS":
            self._generate_maze_DFS()
        elif algorithm == "ELLER":
            self._generate_maze_eller()
        else:
            pass

        if not self.perfect:
            self._generate_imperfections()
        pass

    def _generate_maze_DFS(self) -> None:
        start_cell = self.grid[self.entry[1]][self.entry[0]]
        start_cell.visited = True
        self._log_event("visit", cell=[start_cell.x, start_cell.y])

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

                self._log_event("carve", from_=[current.x, current.y], to=[
                                next_cell_to_go.x, next_cell_to_go.y])
            else:
                stack.pop()
                active = stack[-1] if stack else None
                if active:
                    self._log_event("backtrack", to=[active.x, active.y])

    def _is_3x3_open(self, col: int, row: int) -> bool:
        min_x = col - 1
        max_x = col + 1
        min_y = row - 1
        max_y = row + 1
        for current_row in range(min_y, max_y + 1):
            for current_col in range(min_x, max_x + 1):
                if (current_col < 0
                    or current_row < 0
                    or current_col + 2 >= self.width
                        or current_row + 2 >= self.height):
                    continue

                is_open = True

                for row_in_grid in range(3):
                    for column_in_grid in range(3):
                        cell = (self.grid[current_row +
                                          row_in_grid][current_col
                                                       + column_in_grid])

                        # verfying if there is a wall on the right-side
                        if (column_in_grid < 2
                                and (cell.walls & Direction.EAST)):
                            is_open = False
                            break

                        # verfying if there is a wall on the bottom-side
                        if (row_in_grid < 2
                                and (cell.walls & Direction.SOUTH)):
                            is_open = False
                            break

                    if not is_open:
                        break

                # if is_open is still flagged true
                # it means this is a 3x3 corridor.
                if is_open:
                    return True
        return False

    # Eller's part

    def _generate_maze_eller(self) -> None:
        random.seed(self.seed)
        # row_sets tracks which set each cell belongs to in the current row
        row_sets = list(range(self.width))
        next_set_id = self.width

        for y in range(self.height):
            is_last_row = (y == self.height - 1)

            # --- STEP 1: Horizontal Merging ---
            for x in range(self.width - 1):
                current_cell = self.grid[y][x]
                next_cell = self.grid[y][x + 1]

                # Merge if sets are different AND (random choice OR last row)
                if row_sets[x] != row_sets[x+1]:
                    if is_last_row or random.choice([True, False]):
                        # Avoid pattern cells to keep the "42" intact
                        if not (current_cell.pattern or next_cell.pattern):
                            self._remove_walls(current_cell, next_cell)
                            self._log_event(
                                "carve", from_=[x, y], to=[x + 1, y])

                            # unify the sets
                            # all cells in the old set join the new set
                            old_set = row_sets[x+1]
                            new_set = row_sets[x]
                            for i in range(self.width):
                                if row_sets[i] == old_set:
                                    row_sets[i] = new_set

            # --- STEP 2: Vertical Merging ---
            if not is_last_row:
                next_row_sets = [None] * self.width

                # Group cell indices by their set ID
                sets_in_row = {}
                for x in range(self.width):
                    s = row_sets[x]
                    if s not in sets_in_row:
                        sets_in_row[s] = []
                    sets_in_row[s].append(x)

                for s, indices in sets_in_row.items():
                    # filter valid cells (No pattern in current or south)
                    valid_indices = [
                        x for x in indices
                        if (not (self.grid[y][x].pattern
                                 or self.grid[y+1][x].pattern))
                    ]

                    # STEP 2: If empty, this set is pattern-blocked; skip it
                    if not valid_indices:
                        continue

                    # STEP 3: Guarantee at least one drop, then random the rest
                    random.shuffle(valid_indices)

                    # 3a: The Guarantee (First cell always drops)
                    first_x = valid_indices[0]
                    self._remove_walls(
                        self.grid[y][first_x], self.grid[y+1][first_x])
                    next_row_sets[first_x] = s
                    self._log_event(
                        "carve", from_=[first_x, y], to=[first_x, y + 1])

                    # 3b: The Random (50% chance for additional drops)
                    for i in range(1, len(valid_indices)):
                        if random.choice([True, False]):
                            rand_x = valid_indices[i]
                            self._remove_walls(
                                self.grid[y][rand_x], self.grid[y+1][rand_x])
                            next_row_sets[rand_x] = s
                            self._log_event(
                                "carve", from_=[rand_x, y], to=[rand_x, y + 1])

                # --- STEP 3: Next Row Preparation ---
                for x in range(self.width):
                    if next_row_sets[x] is None:
                        # cell didn't get a vertical drop
                        # assign a brand new Set ID
                        next_row_sets[x] = next_set_id
                        next_set_id += 1
                row_sets = next_row_sets

        # Post-generation: Mark all as visited so the Solver can work
        for row in self.grid:
            for cell in row:
                cell.visited = True

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

            # ignoring the last row and column, as we will focus
            # on eliminating walls on the right and down only.
            # creating a safe approach.
            neighbor_x = random_cell_x
            neighbor_y = random_cell_y
            direction = random.choice([Direction.EAST, Direction.SOUTH])
            if (direction == Direction.EAST
                    and random_cell_x < self.width - 1):
                neighbor_x += 1
            elif (direction == Direction.SOUTH
                  and random_cell_y < self.height - 1):
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
            # check 3x3 box centered on the CURRENT & NEIGHBOR
            if (self._is_3x3_open(random_cell_x, random_cell_y)
                    or self._is_3x3_open(neighbor_x, neighbor_y)):
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
        queue: deque[tuple[int, int]] = deque([(start_x, start_y)])

        moves = [
            (Direction.NORTH, 0, -1, "N"),
            (Direction.EAST, 1, 0, "E"),
            (Direction.SOUTH, 0, 1, "S"),
            (Direction.WEST, -1, 0, "W")
        ]

        while len(queue) > 0:
            current_x, current_y = queue.popleft()

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
            print("Warning: Maze too small to embed "
                  "'42' pattern. Omitting pattern.")
            self.embed_pattern = False
            return

        pattern_start_x = (self.width // 2) - (pattern_width // 2)
        pattern_start_y = (self.height // 2) - (pattern_height // 2)

        blocked_coords = []

        for y_offset, row in enumerate(pattern_map):
            for x_offset, point in enumerate(row):
                if point == "1":
                    blocked_coords.append(
                        (pattern_start_x + x_offset,
                         pattern_start_y + y_offset)
                    )

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

    # =============================
    # the logging concept

    def _log_event(self, action: str, **kwargs) -> None:
        """Record a single delta event."""
        self.history.append({
            "step": len(self.history),
            "action": action,
            **kwargs
        })

    def export_history(self, filepath: str = "history.json") -> None:
        """Save the recorded events to a file."""
        with open(filepath, 'w') as f:
            json.dump(self.history, f, indent=2)
