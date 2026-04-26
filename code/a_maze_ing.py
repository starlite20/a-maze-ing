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
        display_maze(maze, config.DISPLAY_MODE)
        # maze.print_grid()
