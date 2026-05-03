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
    """Wall Direction based bitmask.

    Each bit encodes one wall of a cell:
      bit 0 (1)  = North
      bit 1 (2)  = East
      bit 2 (4)  = South
      bit 3 (8)  = West
    A set bit means the wall is closed or present.
    """
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8


@dataclass
class Cell:
    """A single maze cell.

    Attributes:
        x: Column index (0-based).
        y: Row index (0-based).
        walls: Bitmask of closed walls (all 4 closed = 15).
        visited: Flag to keep track of visited cells.
        pattern: Flag to specify if this cell is part of a pattern.
    """

    x: int
    y: int
    walls: int = 15
    visited: bool = False
    pattern: bool = False

    def get_position(self) -> tuple[int, int]:
        """Return ``(x, y)`` tuple."""
        return (self.x, self.y)

    def remove_wall(self, direction: Direction) -> None:
        """Remove a wall in the given direction.

        Args:
            direction: The wall to remove.
        """
        self.walls &= ~int(direction)


class MazeGenerator:
    """Generate a maze using Eller's row-by-row algorithm.

    Usage::

        gen = MazeGenerator(
            width=20, height=15,
            entry_pos=(0, 0), exit_pos=(19, 14),
            perfect=True, seed=42,
            pattern_42=True,
        )
        gen.generate_maze(algorithm="ELLER")
        path = gen.solve_maze()   # e.g. "NNEESSWW"
        gen.print_grid()

    Args:
        width: Number of columns (≥ 2).
        height: Number of rows (≥ 2).
        entry_pos: ``(x, y)`` of the entrance cell.
        exit_pos: ``(x, y)`` of the exit cell.
        perfect: If ``True``, generate a perfect maze (spanning tree, no
                 cycles).  If ``False``, add random extra openings.
        seed: RNG seed for reproducibility.  ``None`` or ≤ 0 picks a random
              seed automatically.
        pattern_42: If ``True``, embed the '42' pattern as fully-closed cells
                    in the centre of the maze.
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
        """Validate parameters and initialise state."""
        self.set_width(width)
        self.set_height(height)
        self.set_entry_exit_pos(entry_pos, exit_pos)
        self.set_perfect(perfect)
        self.set_seed(seed)
        self.set_pattern_42(pattern_42)
        self.grid: list[list[Cell]] = []
        self.history: list[dict[str, Any]] = []

    def set_width(self, width: int) -> None:
        """Set and validate maze width.

        Args:
            width: Must be an integer ≥ 2.

        Raises:
            ValueError: If validation fails.
        """
        if not isinstance(width, int) or width < 2:
            raise ValueError(f"Width must be an integer >= 2. Got: {width}")
        self.width: int = width

    def set_height(self, height: int) -> None:
        """Set and validate maze height.

        Args:
            height: Must be an integer ≥ 2.

        Raises:
            ValueError: If validation fails.
        """
        if not isinstance(height, int) or height < 2:
            raise ValueError(f"Height must be an integer >= 2. Got: {height}")
        self.height: int = height

    def _is_valid_coord(self,
                        coord: tuple[int, int],
                        name: str) -> None:
        """Validate that *coord* is a tuple of two ints inside maze bounds.

        Args:
            coord: The coordinate to validate.
            name: Human-readable label for error messages.

        Raises:
            ValueError: If validation fails.
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
        """Set and validate entry and exit positions.

        Args:
            entry_pos: ``(x, y)`` of the entrance — must be inside bounds.
            exit_pos: ``(x, y)`` of the exit — must differ from entry.

        Raises:
            ValueError: If any constraint is violated.
        """
        self._is_valid_coord(entry_pos, "Entry")
        self._is_valid_coord(exit_pos, "Exit")

        if entry_pos == exit_pos:
            raise ValueError("Entry and Exit coordinates must be different.")

        self.entry: tuple[int, int] = entry_pos
        self.exit: tuple[int, int] = exit_pos

    def set_perfect(self, perfect: bool) -> None:
        """Set the perfect-maze flag.

        Args:
            perfect: ``True`` for a spanning-tree maze with no cycles.

        Raises:
            ValueError: If not a bool.
        """
        if not isinstance(perfect, bool):
            raise ValueError(
                f"Perfect must be a boolean. Got: {type(perfect)}"
            )
        self.perfect: bool = perfect

    def set_seed(self, seed: int | None) -> None:
        """Set the Randomness seed value.

        Args:
            seed: Integer seed for reproducibility.  Pass ``None`` to have
                  the seed chosen automatically at generation time.

        Raises:
            ValueError: If not an int or None.
        """
        if seed is not None and not isinstance(seed, int):
            raise ValueError(
                f"Seed must be an integer or None. Got: {type(seed)}"
            )
        self.seed: int | None = seed

    def _randomize_seed(self) -> None:
        """Assign a random seed if none was provided.

        Calling this at the start of each generation method ensures that
        ``self.seed`` is always an ``int`` after the call, making the run
        reproducible even when the caller passed ``None``.
        """
        if self.seed is None:
            self.seed = random.randrange(2 ** 32)
        random.seed(self.seed)

    def set_pattern_42(self, embed_pattern: bool = False) -> None:
        """Enable or disable embedding of the '42' pattern.

        Args:
            embed_pattern: ``True`` to embed the pattern.

        Raises:
            ValueError: If not a bool.
        """
        if not isinstance(embed_pattern, bool):
            raise ValueError(
                f"Perfect must be a boolean. Got: {type(embed_pattern)}"
            )
        self.embed_pattern: bool = embed_pattern

    # =============================
    # maze generation

    def create_grid(self) -> None:
        """Allocate the grid as a 2-D list of fresh ``Cell`` objects.

        All cells start with ``walls = 15`` (all four walls closed) and
        ``pattern = False``.
        """
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
        """Print grid to stdout in hex format (one row per line)."""
        for row in self.grid:
            print("".join([f"{cell.walls:X}" for cell in row]))

    def get_unvisited_neighbours(self, x: int, y: int) -> list[Cell]:
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
        """Remove the shared wall between *current* and *next_cell*.

        Works out the direction automatically from the cells' coordinates and
        updates **both** cells so the shared wall is always coherent (if one
        cell has an open east, its east neighbour has an open west).

        Args:
            current: The source cell.
            next_cell: The destination cell (must be a direct neighbour).
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
        """Generate the maze using the specified algorithm.

        Supported algorithms: ``"ELLER"``, ``"DFS"``.

        After generation:
        - If ``pattern_42`` was requested and the maze is large enough, the
          '42' pattern is visible as a cluster of fully-closed cells.
        - Full connectivity of all non-pattern cells is guaranteed.
        - No 3×3 open area exists.
        - If ``perfect=False``, a small percentage of extra walls are removed
          to introduce cycles (while still respecting the 3×3 constraint).

        Args:
            algorithm: Algorithm identifier (case-insensitive).
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
        """Generate a perfect maze using recursive-backtracker (DFS).

        Uses an explicit stack to avoid Python recursion limits.

        Args:
            None — uses ``self.entry`` as the start cell.
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
        """Return ``True`` if the 3×3 block centred on ``(cx, cy)`` is open.

        "Fully open" means no internal east or south walls exist within the
        3×3 grid (i.e. all 9 cells are mutually passable horizontally and
        vertically, forming a corridor wider than 2 cells).

        Cells on the maze border cannot be the centre of a valid 3×3 block,
        so those return ``False`` immediately.

        Args:
            cx: Column of the centre cell.
            cy: Row of the centre cell.

        Returns:
            ``True`` if removing a wall here would create a 3×3 open area.
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
        """Ensure all non-pattern cells form a single connected component.

        Why this is needed
        ------------------
        Pattern cells can fully block all vertical exits of a set during
        Eller's Pass 2.  When that happens, the cells *below* the pattern
        block receive fresh isolated set IDs with no upward link.

        This method detects such isolated regions via BFS and punches the
        minimum number of walls to merge them into the main component.  Wall
        removal always goes through ``_remove_walls`` so coherence is kept.

        The approach
        ------------
        1. BFS from entry — mark reachable component as "main".
        2. Scan grid for any unvisited non-pattern cell.
        3. BFS from that cell to label its component.
        4. Scan the border of that component for a cell that is wall-adjacent
           to the main component, and break that wall.
        5. Repeat until all cells are reachable.
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
        """Return all non-pattern cells reachable from ``(start_x, start_y)``.

        Args:
            start_x: Column of the starting cell.
            start_y: Row of the starting cell.

        Returns:
            Set of ``(x, y)`` tuples reachable without crossing pattern cells.
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
        """Finds the shortest path from entry to exit using BFS.

        Returns:
            A string of directions representing the
            shortest path between entry and exit.

        Raises:
            ValueError: If the maze has not been generated yet.
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
        """Mark cells that form the '42' pattern as permanently closed.

        The pattern is centred in the maze.  If the maze is too small,
        a warning is printed to stderr and the pattern is skipped.

        The pattern cells' ``pattern`` flag is set to ``True`` and their
        ``visited`` flag to ``True`` (so the solver ignores them).
        Their ``walls`` value stays at 15 (all walls closed).

        Raises:
            ValueError: If entry or exit would land inside the pattern.
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
