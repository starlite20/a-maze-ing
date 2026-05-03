from mazegen import MazeGenerator, Direction, Cell
from enum import Enum


class Color(Enum):
    """ANSI escape sequences for terminal text coloring and formatting.
    
    Attributes:
        CYAN, RED, GREEN, PURPLE, YELLOW, GREY: Standard foreground colors.
        RESET: Resets terminal formatting to default.
        BOLD: Applies bold weight to the text.
    """
    CYAN = '\033[96m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    PURPLE = '\033[95m'
    YELLOW = '\033[33m'
    GREY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def display_maze(
        maze: MazeGenerator, color_mode: int = 0,
        show_path: bool = False, solution: str = "",
        current_cell: Cell | None = None
) -> None:
    """Interface function to render the maze to the terminal.

    Args:
        maze (MazeGenerator): The maze object containing grid and coordinate data.
        color_mode (int): Integer offset to cycle through available color themes.
        show_path (bool): Whether to highlight the solution path.
        solution (str): String of directions (N, S, E, W) representing the path.
        current_cell (Cell, optional): The cell to highlight as 'active' (e.g., during animation).
    """
    show_ascii_maze(maze, color_mode, show_path, solution, current_cell)


def show_ascii_maze(
        maze: MazeGenerator, color_mode: int,
        show_path: bool, solution: str, current_cell: Cell | None
) -> None:
    """Executes the complex ASCII rendering logic for the maze.

    Iterates through the maze grid to print wall characters, spaces, and 
    colored path segments based on the cell state and the selected color mode.

    Args:
        maze (MazeGenerator): The maze instance to be printed.
        color_mode (int): Selection index for the color palette.
        show_path (bool): If True, calculates and renders the path overlay.
        solution (str): The sequence of moves to solve the maze.
        current_cell (Cell | None): A specific cell to highlight with a unique style.
    """
    WALL = "█"
    SPACE = " "

    colors = list(Color)
    len_colors = len(colors) - 2
    wall_color = colors[color_mode % len_colors].value
    path_color = colors[(color_mode + 1) % len_colors].value
    entry_color = colors[(color_mode + 2) % len_colors].value
    exit_color = colors[(color_mode + 3) % len_colors].value
    pattern_color = colors[(color_mode + 5) % len_colors].value

    def paint(text: str, color: str) -> str:
        """Wraps text in ANSI color codes.

        Args:
            text (str): The string to be colored.
            color (str): The ANSI escape sequence to apply.

        Returns:
            str: The colored string followed by a reset code.
        """
        return f"{color}{text}{Color.RESET.value}"

    # path tracing
    path_coords = set()
    if show_path and solution:
        x, y = maze.entry
        path_coords.add((y, x))
        for move in solution:
            if move == 'N':
                y -= 1
            elif move == 'S':
                y += 1
            elif move == 'E':
                x += 1
            elif move == 'W':
                x -= 1
            path_coords.add((y, x))

    def render_cell(row: int, col: int) -> str:
        """Determines the visual representation of a single cell's interior.

        Checks for visitation status, entry/exit points, solution path membership, 
        and special pattern flags to return the correct colored block or space.

        Args:
            row (int): The vertical index of the cell.
            col (int): The horizontal index of the cell.

        Returns:
            str: A 3-character wide string representing the cell's center.
        """
        cell = maze.grid[row][col]

        if not cell.visited and not cell.pattern:
            return paint("███", Color.GREY.value)

        if current_cell is not None and cell is current_cell:
            return paint("███", Color.YELLOW.value + Color.BOLD.value)

        entry_y, entry_x = maze.entry[1], maze.entry[0]
        exit_y, exit_x = maze.exit[1], maze.exit[0]

        if (row, col) == (entry_y, entry_x):
            return paint("███", entry_color + Color.BOLD.value)
        if (row, col) == (exit_y, exit_x):
            return paint("███", exit_color + Color.BOLD.value)
        if (row, col) in path_coords:
            return paint("███", path_color + Color.BOLD.value)
        if cell.pattern:
            return paint("███", pattern_color + Color.BOLD.value)

        return "   "

    def has_wall(r: int, c: int, direction: Direction) -> int:
        """Checks if a specific wall exists for a cell in a given direction.

        Args:
            r (int): Row index.
            c (int): Column index.
            direction (Direction): The direction to check (NORTH, SOUTH, etc.).

        Returns:
            int: A non-zero value if the wall exists, 0 otherwise.
        """
        return maze.grid[r][c].walls & direction

    # drawing the maze
    for row in range(maze.height):

        # top line
        line = wall_color + WALL
        for col in range(maze.width):
            if has_wall(row, col, Direction.NORTH):
                line += WALL * 3
            else:
                # check if this passage is part of the solution path
                if (row, col) in path_coords and (row - 1, col) in path_coords:
                    line += paint("███", path_color + Color.BOLD.value)
                else:
                    line += SPACE * 3
            line += wall_color + WALL
        print(line + Color.RESET.value)

        # middle line
        line = wall_color
        for col in range(maze.width):
            if has_wall(row, col, Direction.WEST):
                line += wall_color + WALL
            else:
                # check if the path moves west/left through this gap
                if (row, col) in path_coords and (row, col - 1) in path_coords:
                    line += paint(WALL, path_color + Color.BOLD.value)
                else:
                    line += SPACE

            line += render_cell(row, col)

        # then we check east/right wall check for the end of the row
        if has_wall(row, maze.width - 1, Direction.EAST):
            line += wall_color + WALL
        else:
            line += SPACE

        print(line + Color.RESET.value)

    # bottom line
    line = wall_color + WALL
    for col in range(maze.width):
        if has_wall(maze.height - 1, col, Direction.SOUTH):
            line += WALL * 3
        else:
            # check if the path through the bottom
            if ((maze.height - 1, col) in path_coords
                    and (maze.height - 1, col) in path_coords):
                line += paint("███", path_color + Color.BOLD.value)
            else:
                line += SPACE * 3
        line += wall_color + WALL
    print(line + Color.RESET.value)
