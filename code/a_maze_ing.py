import sys
from mazegen import MazeGenerator
from config_handler import Configuration, read_config, validate_and_cast_config
from maze_display import display_maze


def create_maze(maze_config: dict) -> tuple[MazeGenerator, Configuration]:
    validated_config = validate_and_cast_config(maze_config)

    created_maze = MazeGenerator(
        validated_config.WIDTH,
        validated_config.HEIGHT,
        validated_config.ENTRY,
        validated_config.EXIT,
        validated_config.PERFECT,
        validated_config.SEED,
    )

    created_maze.generate_maze(validated_config.ALGORITHM)

    return (created_maze, validated_config)


def write_output_file(maze: MazeGenerator, config: Configuration, solution: str) -> None:
    maze_txt = ""
    for row in maze.grid:
        for cell in row:
            maze_txt += f"{cell.walls:X}"
        maze_txt += "\n"
    # print(maze_txt)
    # print()
    # print(solution)

    entry_str = f"{maze.entry[0]},{maze.entry[1]}\n"
    exit_str = f"{maze.exit[0]},{maze.exit[1]}\n"
    solution_str = f"{solution}\n"

    try:
        with open(config.OUTPUT_FILE, 'w') as output_file:
            output_file.write(
                maze_txt + "\n" + entry_str + exit_str + solution_str
                )
    except Exception as e:
        print(f"Error while writing to file : {e}")


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Usage: python a_maze_ing.py <config_file>")
        sys.exit(1)

    maze_config = read_config(sys.argv[1])

    maze = None
    try:
        maze, config = create_maze(maze_config)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # generate maze
    if maze is not None:
        # maze.print_grid()
        # print()
        # display_maze(maze, config.DISPLAY_MODE)
        # maze.print_grid()
        write_output_file(maze, config, maze.solve_maze())
