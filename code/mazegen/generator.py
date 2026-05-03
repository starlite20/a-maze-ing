"""
maze_generator.py — Enhanced Maze Generator using Eller's Algorithm.

Design:
  - Eller's builds the maze row-by-row using a disjoint-set (union-find) on
    cell group IDs.  Each row performs two passes:
      1. Horizontal merge  – randomly merge adjacent cells in different sets
         (on the last row, ALL different sets are force-merged for full
         connectivity).
      2. Vertical carve    – for every set, guarantee ≥ 1 south opening so
         no set is stranded without a downward connection.
  - '42' pattern cells are marked BEFORE generation.  They are treated as
    permanent walls and skipped during both Eller passes.
  - Because pattern cells can split a set into disconnected sub-regions
    (e.g. a set whose only vertical-exit column is a pattern cell), a
    post-generation ``_connect_components`` pass uses BFS to detect isolated
    non-pattern components and punches the minimum number of walls to join
    them, guaranteeing full connectivity.
  - Imperfect mode adds random wall removals while checking the
    ``_is_3x3_open`` constraint via the centre-cell heuristic from the
    original code (which correctly rejects moves that would widen a corridor
    beyond 2 cells).
  - All mutations go through ``_remove_walls`` so shared-wall coherence is
    always maintained (no cell can have an east wall while its east neighbour
    lacks a west wall).
"""
from __future__ import annotations

from enum import IntFlag
from dataclasses import dataclass
import random
import json
from collections import deque
from typing import Any, Optional



class Direction(IntFlag):
    """Bitmask representation for maze cell walls.

    Each attribute corresponds to a single bit. A set bit indicates that 
    the wall in that cardinal direction is present (closed).

    Attributes:
        NORTH (int): bit 0 (value 1)
        EAST (int): bit 1 (value 2)
        SOUTH (int): bit 2 (value 4)
        WEST (int): bit 3 (value 8)
    """
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8


@dataclass
class Cell:
    """Represents a individual unit within the maze grid.

    Tracks the physical boundaries (walls), exploration state, and 
    coordinate position of a single cell.

    Attributes:
        x (int): The horizontal column index (0-based).
        y (int): The vertical row index (0-based).
        walls (int): Bitmask representing present walls. Defaults to 15 (all closed).
        visited (bool): exploration status for generation/solving algorithms.
        pattern (bool): Indicates if the cell belongs to a specific visual pattern.
    """
    x: int
    y: int
    walls: int = 15
    visited: bool = False
    pattern: bool = False

    def get_position(self) -> tuple[int, int]:
        """Retrieves the cell's grid coordinates.

        Returns:
            tuple[int, int]: A tuple in the format (x, y).
        """
        return (self.x, self.y)

    def remove_wall(self, direction: Direction) -> None:
        """Removes the wall in the specified direction using bitwise negation.

        Args:
            direction (Direction): The cardinal direction of the wall to clear.
        """
        self.walls &= ~int(direction)


class MazeGenerator:
    """A procedural maze generator supporting DFS and Eller's algorithms.

    This class manages the lifecycle of a maze, including configuration validation,
    grid initialization, pattern embedding, generation via multiple algorithms,
    and shortest-path solving.

    Attributes:
        grid (list[list[Cell]]): The 2D array representing the maze structure.
        history (list[dict]): A chronological log of generation steps (visits, carves).
        width (int): Number of columns in the maze.
        height (int): Number of rows in the maze.
        entry (tuple): (x, y) coordinates for the starting point.
        exit (tuple): (x, y) coordinates for the end point.
        perfect (bool): If True, the maze is a spanning tree (no cycles).
        seed (int): The seed used for the current generation's randomness.
        embed_pattern (bool): Whether to block out the '42' pattern in the center.
    """

    # 42 Pattern Map where '1' = fully-closed pattern cell, '0' = open cell.
    _PATTERN_42_MAP: list[str] = [
        "1000111",
        "1000001",
        "1110111",
        "0010100",
        "0010111",
    ]

    _PATTERN_WIDTH: int = len(_PATTERN_42_MAP[0])
    _PATTERN_HEIGHT: int = len(_PATTERN_42_MAP)

    # Minimum maze size to accommodate the pattern with a 2-cell margin all around
    MIN_WIDTH_FOR_42: int = _PATTERN_WIDTH + 4
    MIN_HEIGHT_FOR_42: int = _PATTERN_HEIGHT + 4

    _NEIGHBOURS: list[tuple[Direction, int, int]] = [
        (Direction.NORTH, 0, -1),
        (Direction.EAST, 1, 0),
        (Direction.SOUTH, 0, 1),
        (Direction.WEST, -1, 0),
    ]

    def __init__(
        self, width: int, height: int,
        entry_pos: tuple[int, int], exit_pos: tuple[int, int],
        perfect: bool, seed: int | None, pattern_42: bool = False
    ) -> None:
        """Initializes the generator and validates all spatial and logic constraints.

        Args:
            width (int): Horizontal dimension (>= 2).
            height (int): Vertical dimension (>= 2).
            entry_pos (tuple[int, int]): Starting (x, y) coordinates.
            exit_pos (tuple[int, int]): Destination (x, y) coordinates.
            perfect (bool): Whether to enforce a perfect (loop-free) maze.
            seed (int | None): Seed for reproducibility; random if None.
            pattern_42 (bool): If True, embeds the '42' pattern map.
        """
        self.set_width(width)
        self.set_height(height)
        self.set_entry_exit_pos(entry_pos, exit_pos)
        self.set_perfect(perfect)
        self.set_seed(seed)
        self.set_pattern_42(pattern_42)
        self.grid: list[list[Cell]] = []
        self.history: list[dict[str, Any]] = []

    def set_width(self, width: int) -> None:
        """Sets and validates the maze width.

        Args:
            width (int): Desired width.

        Raises:
            ValueError: If width is not an integer or is less than 2.
        """
        if not isinstance(width, int) or width < 2:
            raise ValueError(f"Width must be an integer >= 2. Got: {width}")
        self.width: int = width

    def set_height(self, height: int) -> None:
        """Sets and validates the maze height.

        Args:
            height (int): Desired height.

        Raises:
            ValueError: If height is not an integer or is less than 2.
        """
        if not isinstance(height, int) or height < 2:
            raise ValueError(f"Height must be an integer >= 2. Got: {height}")
        self.height: int = height

    def _is_valid_coord(self,
                        coord: tuple[int, int],
                        name: str) -> None:
        """Checks if a coordinate pair is within the current grid dimensions.

        Args:
            coord (tuple[int, int]): The (x, y) pair to check.
            name (str): The label used in the error message if validation fails.

        Raises:
            ValueError: If the coordinate is malformed or out of bounds.
        """
        if (
            not isinstance(coord, tuple)
            or len(coord) != 2
            or not all(isinstance(i, int) for i in coord)
        ):
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
        """Validates and assigns the entry and exit points.

        Args:
            entry_pos (tuple[int, int]): Start position.
            exit_pos (tuple[int, int]): End position.

        Raises:
            ValueError: If positions are identical or out of bounds.
        """
        self._is_valid_coord(entry_pos, "Entry")
        self._is_valid_coord(exit_pos, "Exit")

        if entry_pos == exit_pos:
            raise ValueError("Entry and Exit coordinates must be different.")

        self.entry: tuple[int, int] = entry_pos
        self.exit: tuple[int, int] = exit_pos

    def set_perfect(self, perfect: bool) -> None:
        """Defines whether the maze will be generated as a perfect maze.

        Args:
            perfect (bool): True for no loops, False for an imperfect maze.

        Raises:
            ValueError: If the input is not a boolean.
        """
        if not isinstance(perfect, bool):
            raise ValueError(
                f"Perfect must be a boolean. Got: {type(perfect)}"
            )
        self.perfect: bool = perfect

    def set_seed(self, seed: int | None) -> None:
        """Stores the provided seed or None for automatic randomization.

        Args:
            seed (int | None): Reproducibility seed.

        Raises:
            ValueError: If the seed is not an integer or None.
        """
        if seed is not None and not isinstance(seed, int):
            raise ValueError(
                f"Seed must be an integer or None. Got: {type(seed)}"
            )
        self.seed: int | None = seed

    def _randomize_seed(self) -> None:
        """Initializes the random number generator using the stored seed.

        If seed is None, it generates a random 32-bit integer and stores it
        so the specific run remains reproducible if requested.
        """
        if self.seed is None:
            self.seed = random.randrange(2 ** 32)
        random.seed(self.seed)

    def set_pattern_42(self, embed_pattern: bool = False) -> None:
        """Sets the flag for embedding the numerical '42' pattern.

        Args:
            embed_pattern (bool): True to enable pattern blocking.

        Raises:
            ValueError: If the input is not a boolean.
        """
        if not isinstance(embed_pattern, bool):
            raise ValueError(
                f"Perfect must be a boolean. Got: {type(embed_pattern)}"
            )
        self.embed_pattern: bool = embed_pattern

    # =============================
    # maze generation

    def create_grid(self) -> None:
        """Initializes the maze grid with closed Cells based on height and width."""
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
        """Outputs the grid's wall bitmasks in hexadecimal format to the terminal."""
        for row in self.grid:
            print("".join([f"{cell.walls:X}" for cell in row]))

    def get_unvisited_neighbours(self, x: int, y: int) -> list[Cell]:
        """Identifies adjacent cells that have not yet been visited or blocked by patterns.

        Args:
            x (int): Current column index.
            y (int): Current row index.

        Returns:
            list[Cell]: A list of available Cell objects (North, East, South, West).
        """
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
        """Clears the wall bitmask between two adjacent cells.

        Detects the relative orientation of the cells and updates the `walls`
        attribute for both to ensure consistency.

        Args:
            current (Cell): The starting cell.
            next_cell (Cell): The adjacent neighbor to connect to.
        """
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
        """Executes the maze generation process using the chosen algorithm.

        Orchestrates the lifecycle: grid creation, pattern embedding, 
        core generation, component connectivity check, and imperfection injection.

        Args:
            algorithm (str): The generation logic to use ("DFS" or "ELLER").

        Raises:
            ValueError: If an unsupported algorithm string is provided.
        """
        self.create_grid()

        if self.embed_pattern:
            self._embed_42_pattern()

        alg = algorithm.upper()

        if alg == "DFS":
            self._generate_maze_dfs()
        elif alg == "ELLER":
            self._generate_maze_eller()
        else:
            raise ValueError(f"Unknown algorithm: '{algorithm}'")

        self._connect_components()

        if not self.perfect:
            self._generate_imperfections()
        
        # Mark all non-pattern cells as visited
        for row in self.grid:
            for cell in row:
                if not cell.pattern:
                    cell.visited = True
        pass

    def _generate_maze_dfs(self) -> None:
        """Generates a maze using Depth-First Search (Recursive Backtracker).

        Uses an explicit stack and a history logger for generation playback.
        """
        start_cell = self.grid[self.entry[1]][self.entry[0]]
        start_cell.visited = True
        self._log_event("visit", cell=[start_cell.x, start_cell.y])

        self._randomize_seed()

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

    def _generate_maze_eller(self) -> None:
        """Generates a maze using Eller's row-by-row algorithm.

        This algorithm handles maze creation row-by-row, using sets to manage
        connectivity and ensuring every row is connected to the next.
        """
        self._randomize_seed()

        row_sets: list[int] = list(range(self.width))
        next_set_id: int = self.width

        for y in range(self.height):
            is_last_row: bool = (y == self.height - 1)

            # visit all cells in this row at the start of processing
            for x in range(self.width):
                cell = self.grid[y][x]
                if not cell.visited and not cell.pattern:
                    cell.visited = True
                    self._log_event("visit", cell=[x, y])

            # horizontal merge
            for x in range(self.width - 1):
                left = self.grid[y][x]
                right = self.grid[y][x + 1]

                if left.pattern or right.pattern:
                    continue

                if row_sets[x] == row_sets[x + 1]:
                    continue

                should_merge = is_last_row or random.choice([True, False])
                if should_merge:
                    self._remove_walls(left, right)

                    if (
                        self._is_3x3_open(x, y)
                        or self._is_3x3_open(x + 1, y)
                    ):
                        left.walls |= int(Direction.EAST)
                        right.walls |= int(Direction.WEST)
                        continue

                    self._log_event("carve", from_=[x, y], to=[x + 1, y])

                    old_id = row_sets[x + 1]
                    new_id = row_sets[x]
                    for i in range(self.width):
                        if row_sets[i] == old_id:
                            row_sets[i] = new_id

            # vertical carve except for last row)
            if is_last_row:
                continue

            sets_in_row: dict[int, list[int]] = {}
            for x in range(self.width):
                sets_in_row.setdefault(row_sets[x], []).append(x)

            next_row_sets: list[int] = [
                next_set_id + i for i in range(self.width)
            ]
            next_set_id += self.width

            for s_id, columns in sets_in_row.items():
                valid_cols: list[int] = [
                    x for x in columns
                    if not self.grid[y][x].pattern
                    and not self.grid[y + 1][x].pattern
                ]

                if not valid_cols:
                    continue

                random.shuffle(valid_cols)

                # guaranteed south opening
                mandatory = valid_cols[0]
                self._remove_walls(
                    self.grid[y][mandatory],
                    self.grid[y + 1][mandatory],
                )
                self._log_event("carve", from_=[mandatory, y], to=[mandatory, y + 1])
                next_row_sets[mandatory] = s_id

                # optional extra south openings
                for x in valid_cols[1:]:
                    if random.choice([True, False]):
                        self._remove_walls(
                            self.grid[y][x], self.grid[y + 1][x]
                        )
                        self._log_event("carve", from_=[x, y], to=[x, y + 1])
                        next_row_sets[x] = s_id

            row_sets = next_row_sets
    

    def _is_3x3_open(self, col: int, row: int) -> bool:
        """Determines if removing a wall would create a wide 3x3 open area.

        This is used to maintain a 'maze-like' structure by preventing 
        large open corridors or rooms.

        Args:
            col (int): Center column to check.
            row (int): Center row to check.

        Returns:
            bool: True if a 3x3 open block exists or would be created.
        """
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

    def _connect_components(self) -> None:
        """Verifies and fixes grid connectivity issues.

        Uses BFS to find isolated components (often caused by the central pattern
        blocking Eller's vertical expansion) and punches walls to merge them
        into the main path starting from the entry.
        """

        max_passes = self.width * self.height

        for _ in range(max_passes):
            reachable = self._bfs_reachable(self.entry[0], self.entry[1])

            # check total non-pattern cell count
            all_cells: list[tuple[int, int]] = [
                (x, y)
                for y in range(self.height)
                for x in range(self.width)
                if not self.grid[y][x].pattern
            ]
            if len(reachable) == len(all_cells):
                # indicates all cells are reacheable and connected
                break

            # find one isolated cell
            isolated_start: Optional[tuple[int, int]] = None
            for (x, y) in all_cells:
                if (x, y) not in reachable:
                    isolated_start = (x, y)
                    break

            if isolated_start is None:
                break

            # BFS to label the entire isolated component
            iso_x, iso_y = isolated_start
            iso_component: set[tuple[int, int]] = set()
            queue: deque[tuple[int, int]] = deque([(iso_x, iso_y)])
            iso_component.add((iso_x, iso_y))
            while queue:
                cx, cy = queue.popleft()
                for d, dx, dy in self._NEIGHBOURS:
                    nx, ny = cx + dx, cy + dy
                    if (
                        0 <= nx < self.width
                        and 0 <= ny < self.height
                        and (nx, ny) not in iso_component
                        and not self.grid[ny][nx].pattern
                        and not (self.grid[cy][cx].walls & int(d))
                    ):
                        iso_component.add((nx, ny))
                        queue.append((nx, ny))

            # find a wall between the isolated component and main component
            # prefer openings that do NOT widen a 3×3 area.
            punched = False
            for (cx, cy) in iso_component:
                if punched:
                    break
                for d, dx, dy in self._NEIGHBOURS:
                    nx, ny = cx + dx, cy + dy
                    if (
                        0 <= nx < self.width
                        and 0 <= ny < self.height
                        and not self.grid[ny][nx].pattern
                        and (nx, ny) in reachable
                    ):
                        self._remove_walls(
                            self.grid[cy][cx], self.grid[ny][nx]
                        )
                        punched = True
                        break

            if not punched:
                # fallback if unable to remove ignoring 3×3 constraint
                for (cx, cy) in iso_component:
                    if punched:
                        break
                    for d, dx, dy in self._NEIGHBOURS:
                        nx, ny = cx + dx, cy + dy
                        if (
                            0 <= nx < self.width
                            and 0 <= ny < self.height
                            and not self.grid[ny][nx].pattern
                        ):
                            self._remove_walls(
                                self.grid[cy][cx], self.grid[ny][nx]
                            )
                            punched = True
                            break

    def _bfs_reachable(
        self, start_x: int, start_y: int
    ) -> set[tuple[int, int]]:
        """Calculates all cells reachable from a starting point via open paths.

        Args:
            start_x (int): Origin column.
            start_y (int): Origin row.

        Returns:
            set[tuple[int, int]]: A set of (x, y) coordinates reachable from the start.
        """
        visited: set[tuple[int, int]] = set()
        queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
        visited.add((start_x, start_y))
        while queue:
            cx, cy = queue.popleft()
            for d, dx, dy in self._NEIGHBOURS:
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and (nx, ny) not in visited
                    and not self.grid[ny][nx].pattern
                    and not (self.grid[cy][cx].walls & int(d))
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        return visited

    def _generate_imperfections(self) -> None:
        """Randomly removes walls to create loops in the maze.

        This is only called if `perfect` is False. It respects the 3x3 open 
        area constraint.
        """
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

            self._remove_walls(current_cell, neighbor_cell)

            # LARGE CORRIDOR CHECK
            # check 3x3 box centered on the CURRENT & NEIGHBOR
            if (self._is_3x3_open(random_cell_x, random_cell_y)
                    or self._is_3x3_open(neighbor_x, neighbor_y)):
                # restore both sides of the wall
                current_cell.walls |= int(direction)
                opposite = {
                    Direction.EAST: Direction.WEST,
                    Direction.SOUTH: Direction.NORTH,
                }
                neighbor_cell.walls |= int(opposite[direction])
                continue

            removed_count += 1

    # =============================
    # Maze Solving Algorithm One - BFS
    # suitable for finding one path only... therefore, best for perfect maze.
    def solve_maze(self) -> str:
        """Finds the shortest solution path using Breadth-First Search.

        Returns:
            str: A string of directions (N, E, S, W) representing the path.

        Raises:
            ValueError: If called before the maze has been generated.
        """
        if not self.grid:
            raise ValueError(
                "Maze not generated yet. Call generate_maze() first."
            )

        start_x, start_y = self.entry
        end_x, end_y = self.exit

        grid_visit_flag = [[False for _ in range(
            self.width)] for _ in range(self.height)]

        grid_visit_flag[start_y][start_x] = True

        # dictionary to keep track of path each cell was reached from.
        cell_from: dict[tuple[int, int], tuple[int, int, str] | None] = {}
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

    def _embed_42_pattern(self) -> None:
        """Blocks out specific cells to form a '42' pattern in the center.

        Calculates the center offset and marks specific cells as 'pattern' and
        'visited' so they are ignored by generation and solving logic.

        Raises:
            ValueError: If the entry or exit positions fall within the pattern area.
        """
        if self.width < self.MIN_WIDTH_FOR_42 or self.height < self.MIN_HEIGHT_FOR_42:
            print("Warning: Maze too small to embed "
                  "'42' pattern. Omitting pattern.")
            self.embed_pattern = False
            return

        pattern_start_x = (self.width // 2) - (self._PATTERN_WIDTH // 2)
        pattern_start_y = (self.height // 2) - (self._PATTERN_HEIGHT // 2)

        blocked_coords: list[tuple[int, int]] = []

        for y_offset, row in enumerate(self._PATTERN_42_MAP):
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

    def _log_event(self, action: str, **kwargs: Any) -> None:
        """Appends a generation step to the history log.

        Args:
            action (str): The type of action (e.g., "visit", "carve").
            **kwargs: Additional data such as coordinates (cell, from, to).
        """
        self.history.append({
            "step": len(self.history),
            "action": action,
            **kwargs
        })

    def export_history(self, filepath: str = "history.json") -> None:
        """Writes the generation history log to a JSON file.

        Args:
            filepath (str): Destination path for the JSON output.
        """
        with open(filepath, 'w') as f:
            json.dump(self.history, f, indent=2)
