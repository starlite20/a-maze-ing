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

import json
import random
import sys
from collections import deque
from dataclasses import dataclass
from enum import IntFlag
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Direction enum & wall bitmask helpers
# ---------------------------------------------------------------------------

class Direction(IntFlag):
    """Cardinal-direction wall bitmask.

    Each bit encodes one wall of a cell:
      bit 0 (1)  = North
      bit 1 (2)  = East
      bit 2 (4)  = South
      bit 3 (8)  = West
    A set bit means the wall is *closed* (present).
    """

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8


# (dx, dy) → Direction
_DELTA_TO_DIR: dict[tuple[int, int], Direction] = {
    (0, -1): Direction.NORTH,
    (1, 0): Direction.EAST,
    (0, 1): Direction.SOUTH,
    (-1, 0): Direction.WEST,
}

# Direction → single letter for path strings
_DIR_LETTER: dict[Direction, str] = {
    Direction.NORTH: "N",
    Direction.EAST: "E",
    Direction.SOUTH: "S",
    Direction.WEST: "W",
}

# 4-neighbour iterator (direction, dx, dy)
_NEIGHBOURS: list[tuple[Direction, int, int]] = [
    (Direction.NORTH, 0, -1),
    (Direction.EAST, 1, 0),
    (Direction.SOUTH, 0, 1),
    (Direction.WEST, -1, 0),
]


# ---------------------------------------------------------------------------
# Cell dataclass
# ---------------------------------------------------------------------------

@dataclass
class Cell:
    """A single maze cell.

    Attributes:
        x: Column index (0-based).
        y: Row index (0-based).
        walls: Bitmask of *closed* walls (all 4 closed = 15).
        visited: Bookkeeping flag (used by solvers / renderers).
        pattern: True if this cell is part of the embedded '42' pattern.
                 Pattern cells keep all 4 walls closed permanently.
    """

    x: int
    y: int
    walls: int = 15          # 0b1111 — all walls closed by default
    visited: bool = False
    pattern: bool = False

    def get_position(self) -> tuple[int, int]:
        """Return ``(x, y)`` tuple."""
        return (self.x, self.y)

    def remove_wall(self, direction: Direction) -> None:
        """Open (remove) a wall in the given direction.

        Args:
            direction: The wall to remove.
        """
        self.walls &= ~int(direction)


# ---------------------------------------------------------------------------
# 42 pattern definition
# ---------------------------------------------------------------------------

# 5 rows × 7 columns.  '1' = fully-closed (pattern) cell, '0' = open cell.
_PATTERN_42_MAP: list[str] = [
    "1000111",
    "1000001",
    "1110111",
    "0010100",
    "0010111",
]
_PATTERN_WIDTH: int = len(_PATTERN_42_MAP[0])   # 7
_PATTERN_HEIGHT: int = len(_PATTERN_42_MAP)      # 5
# Minimum maze size to accommodate the pattern with a 2-cell margin all around
MIN_WIDTH_FOR_42: int = _PATTERN_WIDTH + 4       # 11
MIN_HEIGHT_FOR_42: int = _PATTERN_HEIGHT + 4     # 9


# ---------------------------------------------------------------------------
# MazeGenerator
# ---------------------------------------------------------------------------

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
        path = gen.solve_maze()   # e.g. "NNEESSWW..."
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

    def __init__(
        self,
        width: int,
        height: int,
        entry_pos: tuple[int, int],
        exit_pos: tuple[int, int],
        perfect: bool,
        seed: int | None,
        pattern_42: bool = False,
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

    # ------------------------------------------------------------------
    # Validated setters
    # ------------------------------------------------------------------

    def set_width(self, width: int) -> None:
        """Set and validate maze width.

        Args:
            width: Must be an integer ≥ 2.

        Raises:
            ValueError: If validation fails.
        """
        if not isinstance(width, int) or width < 2:
            raise ValueError(f"Width must be an integer >= 2. Got: {width!r}")
        self.width: int = width

    def set_height(self, height: int) -> None:
        """Set and validate maze height.

        Args:
            height: Must be an integer ≥ 2.

        Raises:
            ValueError: If validation fails.
        """
        if not isinstance(height, int) or height < 2:
            raise ValueError(
                f"Height must be an integer >= 2. Got: {height!r}"
            )
        self.height: int = height

    def set_entry_exit_pos(
        self,
        entry_pos: tuple[int, int],
        exit_pos: tuple[int, int],
    ) -> None:
        """Set and validate entry and exit positions.

        Args:
            entry_pos: ``(x, y)`` of the entrance — must be inside bounds.
            exit_pos: ``(x, y)`` of the exit — must differ from entry.

        Raises:
            ValueError: If any constraint is violated.
        """
        self._assert_valid_coord(entry_pos, "Entry")
        self._assert_valid_coord(exit_pos, "Exit")
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
                f"Perfect must be a boolean. Got: {type(perfect)!r}"
            )
        self.perfect: bool = perfect

    def set_seed(self, seed: int | None) -> None:
        """Set the RNG seed.

        Args:
            seed: Integer seed for reproducibility.  Pass ``None`` to have
                  the seed chosen automatically at generation time.

        Raises:
            ValueError: If not an int or None.
        """
        if seed is not None and not isinstance(seed, int):
            raise ValueError(
                f"Seed must be an integer or None. Got: {type(seed)!r}"
            )
        self.seed: int | None = seed

    def _randomize_seed(self) -> None:
        """Assign a random seed if none was provided, then seed the RNG.

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
                f"pattern_42 must be a boolean. Got: {type(embed_pattern)!r}"
            )
        self.embed_pattern: bool = embed_pattern

    # ------------------------------------------------------------------
    # Grid initialisation
    # ------------------------------------------------------------------

    def create_grid(self) -> None:
        """Allocate the grid as a 2-D list of fresh ``Cell`` objects.

        All cells start with ``walls = 15`` (all four walls closed) and
        ``pattern = False``.
        """
        self.grid = [
            [Cell(x=x, y=y) for x in range(self.width)]
            for y in range(self.height)
        ]

    def print_grid(self) -> None:
        """Print grid to stdout in hex format (one row per line)."""
        for row in self.grid:
            print("".join(f"{cell.walls:X}" for cell in row))

    # ------------------------------------------------------------------
    # Wall mutation (coherence-safe)
    # ------------------------------------------------------------------

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
        if dx == 1:    # next is West
            current.remove_wall(Direction.WEST)
            next_cell.remove_wall(Direction.EAST)
        elif dx == -1:  # next is East
            current.remove_wall(Direction.EAST)
            next_cell.remove_wall(Direction.WEST)
        if dy == 1:    # next is North
            current.remove_wall(Direction.NORTH)
            next_cell.remove_wall(Direction.SOUTH)
        elif dy == -1:  # next is South
            current.remove_wall(Direction.SOUTH)
            next_cell.remove_wall(Direction.NORTH)

    # ------------------------------------------------------------------
    # Public generate entry-point
    # ------------------------------------------------------------------

    def generate_maze(self, algorithm: str = "ELLER") -> None:
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
        if alg == "ELLER":
            self._generate_maze_eller()
        elif alg == "DFS":
            self._generate_maze_dfs()
        else:
            raise ValueError(
                f"Unknown algorithm: {algorithm!r}. Use 'ELLER' or 'DFS'."
            )

        # Guarantee every non-pattern cell is reachable
        self._connect_components()

        if not self.perfect:
            self._generate_imperfections()

        # Mark all non-pattern cells as visited
        for row in self.grid:
            for cell in row:
                if not cell.pattern:
                    cell.visited = True

    # ------------------------------------------------------------------
    # Pattern embedding
    # ------------------------------------------------------------------

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
        if self.width < MIN_WIDTH_FOR_42 or self.height < MIN_HEIGHT_FOR_42:
            print(
                f"[WARNING] Maze is too small to embed the '42' pattern "
                f"(need ≥ {MIN_WIDTH_FOR_42}×{MIN_HEIGHT_FOR_42}). "
                "Pattern skipped.",
                file=sys.stderr,
            )
            self.embed_pattern = False
            return

        start_x = (self.width // 2) - (_PATTERN_WIDTH // 2)
        start_y = (self.height // 2) - (_PATTERN_HEIGHT // 2)

        blocked: list[tuple[int, int]] = []
        for y_off, row_str in enumerate(_PATTERN_42_MAP):
            for x_off, ch in enumerate(row_str):
                if ch == "1":
                    blocked.append((start_x + x_off, start_y + y_off))

        # Guard: entry/exit must not overlap the pattern
        for coord, name in [(self.entry, "Entry"), (self.exit, "Exit")]:
            if coord in blocked:
                raise ValueError(
                    f"{name} {coord} conflicts with the '42' pattern."
                )

        for (px, py) in blocked:
            if 0 <= py < self.height and 0 <= px < self.width:
                self.grid[py][px].pattern = True
                self.grid[py][px].visited = True
                # walls remain 15 (all closed)

    # ------------------------------------------------------------------
    # Eller's Algorithm — core implementation
    # ------------------------------------------------------------------

    def _generate_maze_eller(self) -> None:
        """Run Eller's row-by-row maze generation algorithm.

        Algorithm outline
        -----------------
        Maintain ``row_sets[x]`` — the set-ID for each column in the current
        row.  Unique IDs start at ``[0, 1, 2, …, width-1]``.

        For every row ``y``:

        **Pass 1 — Horizontal merge**
            For each adjacent pair ``(x, x+1)`` in different sets:
            - On the last row: *always* merge (force full connectivity).
            - Otherwise: merge with 50 % probability.
            - Pattern cells are never merged through (their walls stay closed).
            - Merging = open the east/west shared wall + unify set IDs.

        **Pass 2 — Vertical carve** (skipped on the last row)
            For every unique set in ``row_sets``:
            - Collect all non-pattern cells in this set **whose south
              neighbour is also not a pattern cell** (valid candidates).
            - If there are valid candidates, guarantee at least one south
              opening (picked randomly); open additional ones at 50 %.
            - Cells that get a south opening carry their set ID into the next
              row.  All others receive a fresh unique set ID.

        After the full loop ``_connect_components`` fixes any residual
        isolated regions caused by pattern cells blocking entire set columns.
        """
        self._randomize_seed()

        row_sets: list[int] = list(range(self.width))
        next_set_id: int = self.width

        for y in range(self.height):
            is_last_row: bool = (y == self.height - 1)

            # ── Pass 1: Horizontal merge ──────────────────────────────────
            for x in range(self.width - 1):
                left = self.grid[y][x]
                right = self.grid[y][x + 1]

                # Never carve through a pattern cell
                if left.pattern or right.pattern:
                    continue

                # Already in the same set → wall stays closed
                if row_sets[x] == row_sets[x + 1]:
                    continue

                # Merge decision
                should_merge = is_last_row or random.choice([True, False])
                if should_merge:
                    self._remove_walls(left, right)
                    # Revert if the merge creates a 3×3 open corridor
                    if (
                        self._is_3x3_open(x, y)
                        or self._is_3x3_open(x + 1, y)
                    ):
                        left.walls |= int(Direction.EAST)
                        right.walls |= int(Direction.WEST)
                        continue
                    old_id = row_sets[x + 1]
                    new_id = row_sets[x]
                    for i in range(self.width):
                        if row_sets[i] == old_id:
                            row_sets[i] = new_id

            # ── Pass 2: Vertical carve (skip last row) ────────────────────
            if is_last_row:
                continue

            # Group columns by set ID
            sets_in_row: dict[int, list[int]] = {}
            for x in range(self.width):
                sets_in_row.setdefault(row_sets[x], []).append(x)

            next_row_sets: list[int] = [
                next_set_id + i for i in range(self.width)
            ]
            # Pre-assign fresh IDs; valid south-openings will overwrite below.
            next_set_id += self.width

            for s_id, columns in sets_in_row.items():
                # Only columns where neither cell is a pattern cell
                valid_cols: list[int] = [
                    x for x in columns
                    if not self.grid[y][x].pattern
                    and not self.grid[y + 1][x].pattern
                ]

                if not valid_cols:
                    # Entire set is blocked by pattern in this row or the next.
                    # The post-generation _connect_components will fix this.
                    continue

                random.shuffle(valid_cols)

                # Guarantee at least one south opening per set
                mandatory = valid_cols[0]
                self._remove_walls(
                    self.grid[y][mandatory],
                    self.grid[y + 1][mandatory],
                )
                next_row_sets[mandatory] = s_id

                # Optional extra south openings
                for x in valid_cols[1:]:
                    if random.choice([True, False]):
                        self._remove_walls(
                            self.grid[y][x], self.grid[y + 1][x]
                        )
                        next_row_sets[x] = s_id

            row_sets = next_row_sets

    # ------------------------------------------------------------------
    # DFS algorithm (bonus / alternative)
    # ------------------------------------------------------------------

    def _generate_maze_dfs(self) -> None:
        """Generate a perfect maze using recursive-backtracker (DFS).

        Uses an explicit stack to avoid Python recursion limits.

        Args:
            None — uses ``self.entry`` as the start cell.
        """
        self._randomize_seed()
        start = self.grid[self.entry[1]][self.entry[0]]
        start.visited = True
        stack: list[Cell] = [start]

        while stack:
            current = stack[-1]
            neighbours = self._get_unvisited_neighbours(current.x, current.y)
            if neighbours:
                chosen = random.choice(neighbours)
                self._remove_walls(current, chosen)
                chosen.visited = True
                stack.append(chosen)
            else:
                stack.pop()

    def _get_unvisited_neighbours(self, x: int, y: int) -> list[Cell]:
        """Return unvisited, non-pattern neighbours of ``(x, y)``.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            List of adjacent ``Cell`` objects that have not been visited.
        """
        neighbours: list[Cell] = []
        for _, dx, dy in _NEIGHBOURS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                n = self.grid[ny][nx]
                if not n.visited and not n.pattern:
                    neighbours.append(n)
        return neighbours

    # ------------------------------------------------------------------
    # Connectivity repair (post-generation)
    # ------------------------------------------------------------------

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
        max_passes = self.width * self.height  # safety limit

        for _ in range(max_passes):
            reachable = self._bfs_reachable(self.entry[0], self.entry[1])

            # Check total non-pattern cell count
            all_cells: list[tuple[int, int]] = [
                (x, y)
                for y in range(self.height)
                for x in range(self.width)
                if not self.grid[y][x].pattern
            ]
            if len(reachable) == len(all_cells):
                break  # Fully connected

            # Find one isolated cell
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
                for d, dx, dy in _NEIGHBOURS:
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

            # Find a wall between the isolated component and main component
            # Prefer openings that do NOT widen a 3×3 area.
            punched = False
            for (cx, cy) in iso_component:
                if punched:
                    break
                for d, dx, dy in _NEIGHBOURS:
                    nx, ny = cx + dx, cy + dy
                    if (
                        0 <= nx < self.width
                        and 0 <= ny < self.height
                        and not self.grid[ny][nx].pattern
                        and (nx, ny) in reachable
                    ):
                        # Punch the wall
                        self._remove_walls(
                            self.grid[cy][cx], self.grid[ny][nx]
                        )
                        punched = True
                        break

            if not punched:
                # Fallback: force-punch ignoring 3×3 constraint
                # (should not happen with correct pattern placement)
                for (cx, cy) in iso_component:
                    if punched:
                        break
                    for d, dx, dy in _NEIGHBOURS:
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
            for d, dx, dy in _NEIGHBOURS:
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

    # ------------------------------------------------------------------
    # Imperfect mode — add controlled cycles
    # ------------------------------------------------------------------

    def _generate_imperfections(self) -> None:
        """Add random extra openings to create a non-perfect (cyclic) maze.

        Removes approximately 5 % of internal walls while enforcing:
        - No 3×3 fully-open corridor area (checked on both cells).
        - Pattern cells are never touched.
        - Only east or south walls are candidates (avoids double-counting).
        """
        # Use a separate, deterministic RNG stream so imperfections are
        # reproducible independently of the generation pass.
        saved_seed = self.seed
        self.seed = (self.seed ^ 0xDEADBEEF) if self.seed is not None else None
        self._randomize_seed()
        self.seed = saved_seed

        internal_walls = (
            (self.width - 1) * self.height
            + self.width * (self.height - 1)
        )
        target = max(1, int(internal_walls * 0.05))
        removed = 0
        attempts = 0
        max_attempts = target * 200  # prevent infinite loop on tiny mazes

        while removed < target and attempts < max_attempts:
            attempts += 1
            rx = random.randint(0, self.width - 1)
            ry = random.randint(0, self.height - 1)
            direction = random.choice([Direction.EAST, Direction.SOUTH])

            nx, ny = rx, ry
            if direction == Direction.EAST:
                if rx >= self.width - 1:
                    continue
                nx += 1
            else:
                if ry >= self.height - 1:
                    continue
                ny += 1

            cc = self.grid[ry][rx]
            nc = self.grid[ny][nx]

            if cc.pattern or nc.pattern:
                continue
            if not (cc.walls & int(direction)):
                continue  # wall already open
            if self._is_3x3_open(rx, ry) or self._is_3x3_open(nx, ny):
                continue

            self._remove_walls(cc, nc)
            removed += 1

    def _is_3x3_open(self, cx: int, cy: int) -> bool:
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
        if cx - 1 < 0 or cx + 1 >= self.width:
            return False
        if cy - 1 < 0 or cy + 1 >= self.height:
            return False

        # Check the 6 internal east walls (left two columns of each row)
        for ro in range(-1, 2):
            for co in range(-1, 1):
                if self.grid[cy + ro][cx + co].walls & Direction.EAST:
                    return False

        # Check the 6 internal south walls (top two rows of each column)
        for ro in range(-1, 1):
            for co in range(-1, 2):
                if self.grid[cy + ro][cx + co].walls & Direction.SOUTH:
                    return False

        return True

    # ------------------------------------------------------------------
    # Solver — BFS shortest path
    # ------------------------------------------------------------------

    def solve_maze(self) -> str:
        """Find the shortest path from entry to exit using BFS.

        Returns:
            A string of direction characters ``N``, ``E``, ``S``, ``W``
            encoding each step of the shortest path.

        Raises:
            ValueError: If the grid has not been generated yet.
            ValueError: If no path exists (should not occur for a valid maze).
        """
        if not self.grid:
            raise ValueError(
                "Maze not generated yet. Call generate_maze() first."
            )

        sx, sy = self.entry
        ex, ey = self.exit

        visited: list[list[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        visited[sy][sx] = True

        # parent[(nx, ny)] = (cx, cy, direction_letter)
        parent: dict[tuple[int, int], tuple[int, int, str]] = {}
        queue: deque[tuple[int, int]] = deque([(sx, sy)])

        while queue:
            cx, cy = queue.popleft()
            if cx == ex and cy == ey:
                break
            cell = self.grid[cy][cx]
            for d, dx, dy in _NEIGHBOURS:
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                    and not visited[ny][nx]
                    and not (cell.walls & int(d))
                ):
                    visited[ny][nx] = True
                    parent[(nx, ny)] = (cx, cy, _DIR_LETTER[d])
                    queue.append((nx, ny))

        if (ex, ey) not in parent and (sx, sy) != (ex, ey):
            raise ValueError(
                f"No path found from {self.entry} to {self.exit}. "
                "The maze may not be fully connected."
            )

        # Reconstruct path
        path: list[str] = []
        step: tuple[int, int] = (ex, ey)
        while step != (sx, sy):
            prev_x, prev_y, letter = parent[step]
            path.append(letter)
            step = (prev_x, prev_y)
        path.reverse()
        return "".join(path)

    # ------------------------------------------------------------------
    # History / logging
    # ------------------------------------------------------------------

    def _log_event(self, action: str, **kwargs: Any) -> None:
        """Record a single generation delta event.

        Args:
            action: Event type label (e.g. ``"carve"``, ``"visit"``).
            **kwargs: Arbitrary key-value pairs attached to the event.
        """
        self.history.append(
            {"step": len(self.history), "action": action, **kwargs}
        )

    def export_history(self, filepath: str = "history.json") -> None:
        """Serialise the recorded event history to a JSON file.

        Args:
            filepath: Destination path (default ``"history.json"``).
        """
        with open(filepath, "w") as fh:
            json.dump(self.history, fh, indent=2)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assert_valid_coord(self, coord: tuple[int, int], name: str) -> None:
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
                f"{name} must be a tuple of two integers. Got: {coord!r}"
            )
        x, y = coord
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(
                f"{name} coordinates {coord} are out of bounds "
                f"(0..{self.width - 1}, 0..{self.height - 1})."
            )

    def is_fully_blocked(self, cell: Cell) -> bool:
        """Return ``True`` if *cell* is non-pattern and has all 4 walls closed.

        Args:
            cell: The cell to inspect.

        Returns:
            ``True`` when the cell is a fully-walled non-pattern cell.
        """
        _all = int(
            Direction.NORTH | Direction.EAST | Direction.SOUTH | Direction.WEST
        )
        return not cell.pattern and cell.walls == _all
