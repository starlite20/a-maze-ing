import sys
import os
import json
import time
from mazegen import MazeGenerator, Cell, Direction
from config_handler import Configuration, read_config, validate_and_cast_config
from maze_display import display_maze, Color


def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def write_output_file(maze: MazeGenerator,
                      config: Configuration,
                      solution: str) -> None:
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

    show_path = False
    color_mode = 0

    while True:
        clear_screen()
        display_maze(maze, color_mode, show_path, solution)
        print(
            "\n1. Regenerate\n2. Show/Hide Path\n3. Rotate Colors\n"
            "4. Write Output & Quit\n5. Animate Maze Generation\n"
            )

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

def run_amazing_graphics(config: Configuration) -> None:
    """Graphical MLX loop rendering PNG assets with an in-window menu."""
    from mlx import Mlx

    class RenderError(Exception):
        pass

    m = Mlx()
    p = m.mlx_init()
    if not p:
        print("Error: Failed to initialize MLX.")
        return

    def load_assets(directory: str) -> dict:
        loaded_assets = {}
        if not os.path.exists(directory):
            raise RenderError(f"Assets directory '{directory}' not found.")
        for item in os.listdir(directory):
            file_path = os.path.join(directory, item)
            if item.endswith(".png"):
                name = item.removesuffix(".png")
                try:
                    asset_key = int(name)  # numeric files: 0.png, 7.png etc
                except ValueError:
                    asset_key = name       # named files: "green.png", "path.png" etc
                image_ptr = m.mlx_png_file_to_image(p, file_path)[0]
                if not image_ptr:
                    raise RenderError(f"Failed to load image: {file_path}")
                loaded_assets[asset_key] = image_ptr
        return loaded_assets

    maze, solution = generate_and_solve(config)
    is_path_visible: bool = False
    colors = [ "yellow","red", "green", "blue"]
    color_i: int = 0
    SCALE: int = 32

    try:
        assets = load_assets("sprites")
    except RenderError as e:
        print(f"Graphics Error: {e}")
        return

    win = m.mlx_new_window(p, SCALE * maze.width, max(SCALE * maze.height, 512), "A-Maze-Ing MLX")
    if not win:
        print("Error: Failed to create window.")
        return
    m.mlx_clear_window(p, win)
    m.mlx_do_sync(p)

    def render_maze_cells() -> None:
        m.mlx_do_sync(p)
        for row_index, row in enumerate(maze.grid):
            m.mlx_do_sync(p)
            for col_index, cell in enumerate(row):
                pixel_x = col_index * SCALE
                pixel_y = row_index * SCALE
                # Draw color background first
                m.mlx_put_image_to_window(
                    p, win,
                    assets[colors[color_i]],
                    pixel_x, pixel_y)
                # Then overlay the wall tile on top
                m.mlx_put_image_to_window(
                    p, win,
                    assets[cell.walls],
                    pixel_x, pixel_y)
        m.mlx_do_sync(p)
        
    def render_path() -> None:
        m.mlx_do_sync(p)
        x, y = maze.entry
        for move in solution[:-1]:
            match move:
                case 'N': y -= 1
                case 'E': x += 1
                case 'S': y += 1
                case 'W': x -= 1
                case _: raise ValueError("path contains invalid character")
            m.mlx_put_image_to_window(
                p, win,
                assets["path"],
                x * SCALE, y * SCALE)
            m.mlx_do_sync(p)

    ESC_LINUX, ESC_MAC = 65307, 53
    KEY_MAP = {
        10: '1', 11: '2', 12: '3', 13: '4',
        18: '1', 19: '2', 20: '3', 21: '4',
    }

    def handle_key_press(keycode: int, _param) -> None:
        nonlocal maze, solution, is_path_visible

        key = KEY_MAP.get(keycode)

        if key == '1':
            maze, solution = generate_and_solve(config)
            is_path_visible = False
            m.mlx_clear_window(p, win)
            render_maze_cells()

        elif key == '2':
            is_path_visible = not is_path_visible
            render_maze_cells()
            if is_path_visible:
                render_path()

        elif key == '4' or keycode in (ESC_LINUX, ESC_MAC):
            write_output_file(maze, config, solution)
            try:
                os.remove("history.json")
            except FileNotFoundError:
                pass
            m.mlx_loop_exit(p)

    def on_close(_param) -> None:
        m.mlx_loop_exit(p)

    render_maze_cells()

    m.mlx_key_hook(win, handle_key_press, None)
    m.mlx_hook(win, 17, 0, on_close, None)
    m.mlx_loop(p)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python a_maze_ing.py <config_file>")
        sys.exit(1)

    maze_config = read_config(sys.argv[1])
    try:
        config = validate_and_cast_config(maze_config)
        if config.DISPLAY != "MLX":
            run_amazing(config)
        else:
            run_amazing_graphics(config)

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
