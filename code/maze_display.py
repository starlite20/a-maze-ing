from mazegen import MazeGenerator, Direction, Cell
from enum import Enum


class Color(Enum):
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
    show_ascii_maze(maze, color_mode, show_path, solution, current_cell)


def show_ascii_maze(
        maze: MazeGenerator, color_mode: int,
        show_path: bool, solution: str, current_cell: Cell | None
) -> None:
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

    # cell rendering
    def render_cell(row: int, col: int) -> str:
        cell = maze.grid[row][col]

        # as we are animating the cells for generation
        # we fill all unvisited cells with grey
        if not cell.visited and not cell.pattern:
            return paint("███", Color.GREY.value)

        # current cell active will be marked with yellow
        if current_cell is not None and cell is current_cell:
            return paint("███", Color.YELLOW.value + Color.BOLD.value)

        # fixed cells such as start & end point, path way, pattern
        if (row, col) == maze.entry:
            return paint("███", entry_color + Color.BOLD.value)
        if (row, col) == maze.exit:
            return paint("███", exit_color + Color.BOLD.value)
        if (row, col) in path_coords:
            return paint("███", path_color + Color.BOLD.value)
        if cell.pattern:
            return paint("███", pattern_color + Color.BOLD.value)

        return "   "

    def has_wall(r, c, direction):
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
                    and (maze.height, col) in path_coords):
                line += paint("███", path_color + Color.BOLD.value)
            else:
                line += SPACE * 3
        line += wall_color + WALL
    print(line + Color.RESET.value)
