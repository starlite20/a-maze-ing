import sys
import os
import json
import time
from mazegen import MazeGenerator, Cell, Direction
from config_handler import Configuration, read_config, validate_and_cast_config
from maze_display import display_maze, Color


def clear_screen() -> None:
    """Clears the terminal screen based on the operating system."""
    os.system('cls' if os.name == 'nt' else 'clear')


def write_output_file(maze: MazeGenerator,
                      config: Configuration,
                      solution: str) -> None:
    """Formats the maze data and saves it to the configured output file.

    The file includes the hexadecimal wall representation of the grid, 
    entry/exit coordinates, and the solution path string.

    Args:
        maze (MazeGenerator): The generated maze object containing the grid.
        config (Configuration): The configuration object containing the output path.
        solution (str): A string representation of the solution path.
    """
    maze_txt = ""
    for row in maze.grid:
        for cell in row:
            maze_txt += f"{cell.walls:X}"
        maze_txt += "\n"

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


def generate_and_solve(config: Configuration) -> tuple[MazeGenerator, str]:
    """Initializes a maze generator, creates the maze, and finds the solution.

    Args:
        config (Configuration): Settings for width, height, seed, and algorithm.

    Returns:
        tuple[MazeGenerator, str]: A tuple containing the populated MazeGenerator 
            instance and the solution string.
    """
    maze = MazeGenerator(
        config.WIDTH, config.HEIGHT, config.ENTRY,
        config.EXIT, config.PERFECT, config.SEED, config.PATTERN_42
    )
    maze.generate_maze(config.ALGORITHM)
    return (maze, maze.solve_maze())


def run_amazing(config: Configuration) -> None:
    """Main application loop for the interactive maze interface.

    Handles user input for regenerating mazes, toggling path visibility, 
    cycling colors, and triggering animations.

    Args:
        config (Configuration): The initial configuration used to build the maze.
    """
    maze, solution = generate_and_solve(config)

    active_seed: int | str = "random (no seed set)"
    if maze.seed is not None:
        active_seed = maze.seed

    show_path = False
    color_mode = 0

    while True:
        clear_screen()
        display_maze(maze, color_mode, show_path, solution)
        print(f"=> Randomness Seed : {active_seed}")
        print(
            "\n\n1. Regenerate\n2. Show/Hide Path\n3. Rotate Colors\n"
            "4. Write Output & Quit\n5. Animate Maze Generation\n"
        )

        choice = input("Choice? ").strip()
        if choice == '1':
            maze, solution = generate_and_solve(config)
            if maze.seed is not None:
                active_seed = maze.seed
            show_path = False
        elif choice == '2':
            show_path = not show_path
        elif choice == '3':
            color_mode = (color_mode + 1) % len(Color)
        elif choice == '4':
            write_output_file(maze, config, solution)

            try:
                os.remove("history.json")
            except FileNotFoundError:
                pass

            sys.exit(0)
        elif choice == '5':
            if not maze.history:
                print("No generation history available to animate.")
                input("Press Enter to continue...")
                continue

            maze.export_history("history.json")
            play_animation(maze, "history.json")
            show_path = False
        else:
            print("Incorrect Option Selected.")
            input("Press Enter to continue...")
            continue


def play_animation(maze: MazeGenerator, history_file: str) -> None:
    """Plays a frame-by-frame terminal animation of the maze generation process.

    Reads from a JSON history file to simulate the 'visit', 'carve', and 
    'backtrack' steps of the algorithm visually.

    Args:
        maze (MazeGenerator): The maze object used for dimensions and rendering context.
        history_file (str): Path to the JSON file containing generation steps.
    """
    frames_delay_rate = 0.05

    with open(history_file, 'r') as f:
        script = json.load(f)

    # creating a preview grid matching the maze dimensions and configuration
    preview_grid = [[Cell(x, y, walls=15, visited=False)
                     for x in range(maze.width)]
                    for y in range(maze.height)]

    # copying 42 pattern state
    if maze.embed_pattern:
        for r in range(maze.height):
            for c in range(maze.width):
                preview_grid[r][c].pattern = maze.grid[r][c].pattern

    active_cell = None

    for frame in script:
        action = frame["action"]

        if action == "visit":
            x, y = frame["cell"]
            preview_grid[y][x].visited = True
            active_cell = preview_grid[y][x]

        elif action == "carve":
            from_x, from_y = frame["from_"]
            to_x, to_y = frame["to"]
            curr = preview_grid[from_y][from_x]
            nxt = preview_grid[to_y][to_x]

            nxt.visited = True

            dx = curr.x - nxt.x
            dy = curr.y - nxt.y

            if dx == 1:
                curr.remove_wall(Direction.WEST)
                nxt.remove_wall(Direction.EAST)

            elif dx == -1:
                curr.remove_wall(Direction.EAST)
                nxt.remove_wall(Direction.WEST)

            if dy == 1:
                curr.remove_wall(Direction.NORTH)
                nxt.remove_wall(Direction.SOUTH)

            elif dy == -1:
                curr.remove_wall(Direction.SOUTH)
                nxt.remove_wall(Direction.NORTH)

            active_cell = nxt

        elif action == "backtrack":
            to_x, to_y = frame["to"]
            active_cell = preview_grid[to_y][to_x]

        # rendering the frame
        clear_screen()
        real_grid = maze.grid
        maze.grid = preview_grid

        display_maze(maze, color_mode=0, show_path=False, solution="",
                     current_cell=active_cell)

        maze.grid = real_grid

        # frame rate
        time.sleep(frames_delay_rate)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python a_maze_ing.py <config_file>")
        sys.exit(1)

    maze_config = read_config(sys.argv[1])
    try:
        config = validate_and_cast_config(maze_config)
        run_amazing(config)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
