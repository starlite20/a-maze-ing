"""
mazegen - A perfect maze generator using Eller's Algorithm.

This module provides the MazeGenerator class, which generates perfect mazes
(spanning trees with no loops and unique paths between any two cells) using
Eller's row-by-row algorithm.

Example usage::

    from mazegen.maze_generator import MazeGenerator

    gen = MazeGenerator(width=20, height=15, seed=42, perfect=True)
    gen.generate()

    # Access the grid: list[list[int]], each int is a bitmask
    # Bit 0=North, 1=East, 2=South, 3=West  (1 = wall closed)
    grid = gen.grid

    # Access the solution path as a list of (x, y) tuples
    solution = gen.solve(entry=(0, 0), exit_pos=(19, 14))

    # Access path as direction string
    path_str = gen.path_string(entry=(0, 0), exit_pos=(19, 14))
"""

from __future__ import annotations

import random
from collections import deque
from typing import Optional


# Wall bitmask constants (bit index → direction)
NORTH: int = 1 << 0   # bit 0
EAST: int = 1 << 1    # bit 1
SOUTH: int = 1 << 2   # bit 2
WEST: int = 1 << 3    # bit 3

OPPOSITE: dict[int, int] = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST: WEST,
    WEST: EAST,
}

DIR_CHAR: dict[tuple[int, int], str] = {
    (0, -1): "N",
    (1, 0): "E",
    (0, 1): "S",
    (-1, 0): "W",
}

DIR_DELTA: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}

DIR_WALL: dict[str, int] = {
    "N": NORTH,
    "E": EAST,
    "S": SOUTH,
    "W": WEST,
}


class MazeGenerator:
    """Generate a maze using Eller's Algorithm.

    Eller's Algorithm builds the maze row by row, maintaining a disjoint-set
    (union-find) structure to track connectivity.  This guarantees a perfect
    maze when ``perfect=True``: exactly one path exists between any two cells.

    When ``perfect=False`` the east-wall removal step is relaxed so that some
    cycles may appear (imperfect maze).

    Args:
        width: Number of columns (cells).
        height: Number of rows (cells).
        seed: Optional integer seed for reproducibility.
        perfect: If True, generate a perfect (spanning-tree) maze.

    Attributes:
        grid: 2-D list ``grid[y][x]`` of wall bitmasks after ``generate()``.
    """

    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None,
        perfect: bool = True,
    ) -> None:
        """Initialise the generator with dimensions and options."""
        if width < 2 or height < 2:
            raise ValueError("Maze dimensions must be at least 2×2.")
        self.width: int = width
        self.height: int = height
        self.seed: Optional[int] = seed
        self.perfect: bool = perfect
        self.rng: random.Random = random.Random(seed)
        # grid[y][x] — bitmask of *closed* walls
        self.grid: list[list[int]] = [
            [0] * width for _ in range(height)
        ]
        self._generated: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> None:
        """Run Eller's Algorithm and populate ``self.grid``.

        After calling this method ``self.grid[y][x]`` contains a bitmask
        where a set bit means that wall is *closed* (present).
        """
        self.rng = random.Random(self.seed)  # reset for reproducibility
        self.grid = [[0] * self.width for _ in range(self.height)]

        # Each cell in the current row belongs to a set (group id).
        # We start by assigning unique set IDs to every cell.
        next_set_id: int = 0
        row_sets: list[int] = list(range(self.width))
        next_set_id = self.width

        for y in range(self.height):
            is_last_row: bool = y == self.height - 1

            # ── Step 1: Randomly merge adjacent cells in this row ──────────
            # On the last row we MUST merge all cells that are in different
            # sets (to guarantee full connectivity / perfect maze).
            for x in range(self.width - 1):
                if row_sets[x] == row_sets[x + 1]:
                    # Already in the same set → keep wall (no merge needed)
                    self._close_east(x, y, row_sets)
                    continue

                if is_last_row or (self.perfect and self.rng.random() < 0.5):
                    # Merge: remove east wall between x and x+1
                    old_set = row_sets[x + 1]
                    new_set = row_sets[x]
                    for i in range(self.width):
                        if row_sets[i] == old_set:
                            row_sets[i] = new_set
                else:
                    # Keep wall closed
                    self._close_east(x, y, row_sets)

            # ── Step 2: Create south openings (not on last row) ────────────
            if not is_last_row:
                # For each set, at least one cell must have a south opening.
                set_to_cells: dict[int, list[int]] = {}
                for x, s in enumerate(row_sets):
                    set_to_cells.setdefault(s, []).append(x)

                # Decide which cells get south openings
                south_open: list[bool] = [False] * self.width
                for s, cells in set_to_cells.items():
                    # Guarantee at least one opening per set
                    mandatory = self.rng.choice(cells)
                    south_open[mandatory] = True
                    for c in cells:
                        if c != mandatory and self.rng.random() < 0.5:
                            south_open[c] = True

                # Apply south openings and build the next row's set IDs
                next_row_sets: list[int] = []
                for x in range(self.width):
                    if south_open[x]:
                        # Remove south wall of current cell and north wall of
                        # the cell below
                        self.grid[y][x] &= ~SOUTH
                        # (will also clear north of y+1 when we initialise it)
                        next_row_sets.append(row_sets[x])
                    else:
                        # Close south wall
                        self.grid[y][x] |= SOUTH
                        # Cell below starts as isolated → new set
                        next_row_sets.append(next_set_id)
                        next_set_id += 1

                # Set north walls for next row based on south openings
                for x in range(self.width):
                    if not south_open[x]:
                        self.grid[y + 1][x] |= NORTH
                    # If south_open, north wall of y+1 stays open (0)

                row_sets = next_row_sets

        # ── Step 3: Apply all external border walls ────────────────────────
        self._apply_borders()
        self._generated = True

    def solve(
        self,
        entry: tuple[int, int],
        exit_pos: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """Return the shortest path from *entry* to *exit_pos* as cell coords.

        Uses BFS on the maze grid.

        Args:
            entry: ``(x, y)`` of the starting cell.
            exit_pos: ``(x, y)`` of the target cell.

        Returns:
            Ordered list of ``(x, y)`` tuples from entry to exit (inclusive).

        Raises:
            RuntimeError: If the maze has not been generated yet.
            ValueError: If no path exists (should not happen for a perfect maze).
        """
        if not self._generated:
            raise RuntimeError("Call generate() before solve().")
        ex, ey = entry
        fx, fy = exit_pos
        if (ex, ey) == (fx, fy):
            return [(ex, ey)]

        visited: set[tuple[int, int]] = {(ex, ey)}
        parent: dict[tuple[int, int], tuple[int, int]] = {}
        queue: deque[tuple[int, int]] = deque([(ex, ey)])

        while queue:
            cx, cy = queue.popleft()
            for direction, (dx, dy) in [
                ("N", (0, -1)), ("E", (1, 0)),
                ("S", (0, 1)), ("W", (-1, 0)),
            ]:
                wall = DIR_WALL[direction]
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and (nx, ny) not in visited
                    and not (self.grid[cy][cx] & wall)
                ):
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (cx, cy)
                    if (nx, ny) == (fx, fy):
                        return self._reconstruct(parent, entry, exit_pos)
                    queue.append((nx, ny))

        raise ValueError(f"No path found from {entry} to {exit_pos}.")

    def path_string(
        self,
        entry: tuple[int, int],
        exit_pos: tuple[int, int],
    ) -> str:
        """Return the shortest path as a direction string (e.g. ``"NESSWW"``).

        Args:
            entry: Starting cell ``(x, y)``.
            exit_pos: Target cell ``(x, y)``.

        Returns:
            String of direction characters N, E, S, W.
        """
        path = self.solve(entry, exit_pos)
        chars: list[str] = []
        for i in range(len(path) - 1):
            x0, y0 = path[i]
            x1, y1 = path[i + 1]
            chars.append(DIR_CHAR[(x1 - x0, y1 - y0)])
        return "".join(chars)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _close_east(self, x: int, y: int, row_sets: list[int]) -> None:
        """Close east wall of cell (x,y) and west wall of (x+1,y)."""
        self.grid[y][x] |= EAST
        self.grid[y][x + 1] |= WEST

    def _apply_borders(self) -> None:
        """Close all external border walls of the maze."""
        for x in range(self.width):
            self.grid[0][x] |= NORTH
            self.grid[self.height - 1][x] |= SOUTH
        for y in range(self.height):
            self.grid[y][0] |= WEST
            self.grid[y][self.width - 1] |= EAST

    @staticmethod
    def _reconstruct(
        parent: dict[tuple[int, int], tuple[int, int]],
        entry: tuple[int, int],
        exit_pos: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """Reconstruct BFS path from parent map."""
        path: list[tuple[int, int]] = []
        node: tuple[int, int] = exit_pos
        while node != entry:
            path.append(node)
            node = parent[node]
        path.append(entry)
        path.reverse()
        return path