import sys
import os
from mazegen import MazeGenerator
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


def run_regular_mode(config: Configuration) -> None:
    maze, solution = generate_and_solve(config)

    show_path = False
    color_mode = 0

    while True:
        clear_screen()
        display_maze(maze, config.DISPLAY_MODE, config, 
                     color_mode, show_path, solution)
        print(
            "\n1. Regenerate\n2. Show/Hide Path\n3. Rotate Colors\n4. Write Output & Quit\n")

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
            sys.exit(0)
        else:
            print("Incorrect Option Selected.")


def run_interactive_mode(config: Configuration) -> None:
    maze = None
    solution = None
    show_path = False
    color_mode = 0
    generated_once = False

    while True:
        clear_screen()
        print(
            f"Size: {config.WIDTH}x{config.HEIGHT} | Seed: {config.SEED} | Perfect: {config.PERFECT}")

        if generated_once:
            display_maze(maze, config.DISPLAY_MODE, config,
                         color_mode, show_path, solution)
        else:
            print("\nNo maze generated yet.")

        print("\n1. Generate\n2. Path\n3. Colors\n4. Settings\n5. Write & Quit")
        choice = input("Choice? ").strip()

        if choice == '1':
            maze, solution = generate_and_solve(config)
            generated_once = True
            show_path = False
        elif choice == '2' and generated_once:
            show_path = not show_path
        elif choice == '3':
            color_mode = (color_mode + 1) % len(list(Color))
        elif choice == '4':
            open_settings_menu(config)
        elif choice == '5' and generated_once:
            write_output_file(maze, config, solution)
            sys.exit(0)
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
        print(f"7. ALGO    ({config.ALGORITHM})")
        print(f"8. DISPLAY ({config.DISPLAY_MODE})")
        print(f"9. PATTERN ({config.PATTERN_42})")
        print("0. Back to Main Menu")

        choice = input("Edit which setting? ").strip()

        if choice == '0':
            break

        # Mapping choices to keys
        key_map = {
            '1': "WIDTH", '2': "HEIGHT", '3': "ENTRY", '4': "EXIT",
            '5': "PERFECT", '6': "SEED", '7': "ALGORITHM",
            '8': "DISPLAY_MODE", '9': "PATTERN_42"
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python a_maze_ing.py <config_file>")
        sys.exit(1)

    maze_config = read_config(sys.argv[1])
    try:
        config = validate_and_cast_config(maze_config)

        if config.INTERACTIVE_MODE:
            run_interactive_mode(config)
        else:
            run_regular_mode(config)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
