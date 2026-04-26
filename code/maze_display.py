from mazegen import MazeGenerator, Direction


class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    GREY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def display_maze(maze: MazeGenerator, display_mode: str | None) -> None:
    if display_mode == "ASCII":
        show_ascii_maze(maze)
    elif display_mode == "MLX":
        pass


def show_ascii_maze(maze: MazeGenerator) -> None:
    WALL = "█"
    SPACE = " "

    def colored(content: str, color: str) -> str:
        return color + content + Color.RESET

    def cell_content(row: int, column: int) -> str:
        # Must be exactly 3 visible characters wide
        if (row, column) == maze.entry:
            content = "[] "
            if maze.color_mode == 1:
                return colored(content, Color.GREY)
            return colored(content, Color.PURPLE + Color.BOLD)

        if (row, column) == maze.exit:
            content = "[] "
            if maze.color_mode == 1:
                return colored(content, Color.GREY)
            return colored(content, Color.RED + Color.BOLD)

        return "   "

    row_num = 0
    for row in range(maze.height):
        top_line = WALL

        for column in range(maze.width):
            if maze.grid[row][column].walls & Direction.NORTH:
                top_line += WALL * 3
            else:
                top_line += SPACE * 3

            # Corner / separator
            top_line += WALL

        print(top_line)
        # print(str(row_num) + "   " + top_line)
        row_num += 1

        # Draw the west/east walls and cell contents
        mid_line = ""

        for column in range(maze.width):
            if maze.grid[row][column].walls & Direction.WEST:
                mid_line += WALL
            else:
                mid_line += SPACE

            mid_line += cell_content(row, column)

        # Add the far-right east wall of the last cell
        if maze.grid[row][maze.width - 1].walls & Direction.EAST:
            mid_line += WALL
        else:
            mid_line += SPACE

        print(mid_line)

    # Draw the bottom south walls
    bottom_line = WALL

    for column in range(maze.width):
        if maze.grid[maze.height - 1][column].walls & Direction.SOUTH:
            bottom_line += WALL * 3
        else:
            bottom_line += SPACE * 3

        bottom_line += WALL

    print(bottom_line)
