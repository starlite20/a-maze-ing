from mazegen import MazeGenerator, Direction
from enum import Enum

class Color(Enum):
    RED = '\033[91m'
    GREEN = '\033[92m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GREY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def display_maze(
        maze: MazeGenerator, display_mode: str | None,
        color_mode: int = 0, show_path: bool = False, solution: str = ""
) -> None:
    if display_mode == "ASCII":
        show_ascii_maze(maze, color_mode, show_path, solution)
    elif display_mode == "MLX":
        pass


def show_ascii_maze(maze: MazeGenerator, color_mode: int, show_path, solution) -> None:
    if color_mode == 1:
        WALL_COLOR = Color.GREY.value
    else:
        WALL_COLOR = Color.CYAN.value

    WALL = "█"
    SPACE = " "

    path_coords = set()
    if show_path and solution:
        curr_x, curr_y = maze.entry
        path_coords.add((curr_y, curr_x))
        for char in solution:
            if char == 'N':
                curr_y -= 1
            elif char == 'S':
                curr_y += 1
            elif char == 'E':
                curr_x += 1
            elif char == 'W':
                curr_x -= 1
            path_coords.add((curr_y, curr_x))

    def colored(content: str, color: str) -> str:
        return color + content + Color.RESET.value

    def cell_content(row: int, column: int) -> str:
        # check path and fill path with colored block
        if (row, column) in path_coords:
            content = ".. "
            if color_mode == 1:
                return colored(content, Color.GREY.value)
            return colored(content, Color.CYAN.value + Color.BOLD.value)

        # check if entry
        if (row, column) == maze.entry:
            content = "[] "
            if color_mode == 1:
                return colored(content, Color.GREY.value)
            return colored(content, Color.PURPLE.value + Color.BOLD.value)

        # check if exit
        if (row, column) == maze.exit:
            content = "[] "
            if color_mode == 1:
                return colored(content, Color.GREY.value)
            return colored(content, Color.RED.value + Color.BOLD.value)

        return "   "

    for row in range(maze.height):
        top_line = WALL
        for column in range(maze.width):
            if maze.grid[row][column].walls & Direction.NORTH:
                top_line += WALL * 3
            else:
                top_line += SPACE * 3
            top_line += WALL
        print(top_line)

        mid_line = ""
        for column in range(maze.width):
            if maze.grid[row][column].walls & Direction.WEST:
                mid_line += WALL
            else:
                mid_line += SPACE

            mid_line += cell_content(row, column)

        if maze.grid[row][maze.width - 1].walls & Direction.EAST:
            mid_line += WALL
        else:
            mid_line += SPACE
        print(mid_line)

    bottom_line = WALL
    for column in range(maze.width):
        if maze.grid[maze.height - 1][column].walls & Direction.SOUTH:
            bottom_line += WALL * 3
        else:
            bottom_line += SPACE * 3
        bottom_line += WALL
    print(bottom_line)
