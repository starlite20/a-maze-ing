import sys
import os
import json
import time
from mazegen import MazeGenerator, Cell, Direction
from config_handler import Configuration, read_config, validate_and_cast_config
from maze_display import display_maze, Color


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def write_output_file(maze: MazeGenerator, config: Configuration, solution: str) -> None:
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
    maze = MazeGenerator(
        config.WIDTH, config.HEIGHT, config.ENTRY,
        config.EXIT, config.PERFECT, config.SEED, config.PATTERN_42
    )
    maze.generate_maze(config.ALGORITHM)
    return (maze, maze.solve_maze())


def run_amazing(config: Configuration) -> None:
    maze, solution = generate_and_solve(config)
    generated_once = True

    show_path = False
    color_mode = 0

    while True:
        clear_screen()
        display_maze(maze, color_mode, show_path, solution)
        print(
            "\n1. Regenerate\n2. Show/Hide Path\n3. Rotate Colors\n4. Write Output & Quit\n5. Animate Maze Generation\n")

        choice = input("Choice? ").strip()
        if choice == '1':
            maze, solution = generate_and_solve(config)
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
            if not generated_once:
                print("Please generate a maze first (Option 1).")
                input("Press Enter to continue...")
                continue

            maze.export_history("history.json")
            play_animation(maze, "history.json")
            show_path = False
        else:
            print("Incorrect Option Selected.")


def open_settings_menu(config: Configuration):
    while True:
        clear_screen()
        print(Color.CYAN.value + "SETTINGS EDITOR" + Color.RESET.value)
        print(f"1. WIDTH  ({config.WIDTH})")
        print(f"2. HEIGHT ({config.HEIGHT})")
        print(f"3. ENTRY  ({config.ENTRY})")
        print(f"4. EXIT   ({config.EXIT})")
        print(f"5. PERFECT ({config.PERFECT})")
        print(f"6. SEED   ({config.SEED})")
        print(f"7. ALGORITHM    ({config.ALGORITHM})")
        print(f"8. PATTERN ({config.PATTERN_42})")
        print("0. Back to Main Menu")

        choice = input("Edit which setting? ").strip()

        if choice == '0':
            break

        # Mapping choices to keys
        key_map = {
            '1': "WIDTH", '2': "HEIGHT", '3': "ENTRY", '4': "EXIT",
            '5': "PERFECT", '6': "SEED", '7': "ALGORITHM",
            '8': "PATTERN_42"
        }

        if choice in key_map:
            new_val = input(f"Enter new value for {key_map[choice]}: ").strip()
            try:
                config.update_value(key_map[choice], new_val)
                print(Color.GREEN.value + "Updated!" + Color.RESET.value)
                input("Press Enter...")
            except ValueError as e:
                print(Color.RED.value + f"Error: {e}" + Color.RESET.value)
                input("Press Enter...")


def play_animation(maze: MazeGenerator, history_file: str) -> None:
    frames_per_second = 0.05

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
            fx, fy = frame["from_"]
            tx, ty = frame["to"]
            curr = preview_grid[fy][fx]
            nxt = preview_grid[ty][tx]

            nxt.visited = True
            maze._remove_walls(curr, nxt)
            active_cell = nxt

        elif action == "backtrack":
            tx, ty = frame["to"]
            active_cell = preview_grid[ty][tx]

        # rendering the frame
        clear_screen()
        real_grid = maze.grid
        maze.grid = preview_grid

        display_maze(maze, color_mode=0, show_path=False, solution="",
                     current_cell=active_cell, head_cell=None)

        maze.grid = real_grid

        # frame rate
        time.sleep(frames_per_second)


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
