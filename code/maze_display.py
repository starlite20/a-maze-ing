from mazegen import MazeGenerator, Direction
from enum import Enum
from config_handler import Configuration

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
        maze: MazeGenerator, display_mode: str | None,
        config: Configuration, color_mode: int = 0,
        show_path: bool = False, solution: str = ""
) -> None:
    if display_mode == "ASCII":
        show_ascii_maze(maze, color_mode, show_path, solution)
    elif display_mode == "MLX":
        show_mlx_maze(maze, config, color_mode, show_path, solution)
    else:
        raise ValueError (f"Invalid Display Mode : {display_mode}")


def show_ascii_maze(maze, color_mode: int, show_path: bool, solution: str):

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
    def render_cell(row, col):
        if (row, col) == maze.entry:
            return paint("███", entry_color + Color.BOLD.value)

        if (row, col) == maze.exit:
            return paint("███", exit_color + Color.BOLD.value)

        if (row, col) in path_coords:
            return paint("███", path_color + Color.BOLD.value)

        if maze.grid[row][col].pattern:
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
            if (maze.height - 1, col) in path_coords and (maze.height, col) in path_coords:
                line += paint("███", path_color + Color.BOLD.value)
            else:
                line += SPACE * 3
        line += wall_color + WALL
    print(line + Color.RESET.value)





from mazegen import MazeGenerator, Direction
# You will need to import your config type if using strict mypy
from config_handler import Configuration 

def show_mlx_maze(
    maze: MazeGenerator,
    config: Configuration,  # Added config to allow regeneration
    color_mode: int,
    show_path: bool,
    solution: str
) -> None:
    """Display the maze and handle interactions entirely inside MLX."""
    
    # --- Configuration ---
    WALL_W: int = 3
    TILE: int = 20
    CELL_SIZE: int = TILE + WALL_W
    MENU_H: int = 40  # Added height for the bottom menu

    win_w: int = maze.width * CELL_SIZE + WALL_W
    win_h: int = maze.height * CELL_SIZE + WALL_W + MENU_H

    COLORS: list[int] = [0x00FFFF, 0xFF0000, 0x00FF00, 0xFF00FF, 0xFFFF00, 0x808080]
    wall_hex: int = COLORS[color_mode % len(COLORS)]
    path_hex: int = COLORS[(color_mode + 1) % len(COLORS)]
    entry_hex: int = COLORS[(color_mode + 2) % len(COLORS)]
    exit_hex: int = COLORS[(color_mode + 3) % len(COLORS)]
    bg_color: int = 0x121212
    text_color: int = 0xFFFFFF

    from mlx import Mlx

    m: Mlx = Mlx()
    mlx_ptr = m.mlx_init()
    if not mlx_ptr:
        raise RuntimeError("Failed to initialize MLX connection.")

    win_ptr = m.mlx_new_window(mlx_ptr, win_w, win_h, "A-Maze-Ing MLX")
    img_ptr = m.mlx_new_image(mlx_ptr, win_w, win_h)

    buf, bpp_val, sl_val, endian_val = m.mlx_get_data_addr(img_ptr)

    # ==========================================
    # INTERACTIVE STATE MANAGEMENT
    # ==========================================
    # We use nonlocal to allow the key_hook to mutate these variables
    current_maze: MazeGenerator = maze
    current_solution: str = solution
    current_show_path: bool = show_path
    current_color_mode: int = color_mode

    def has_wall(r: int, c: int, direction: Direction) -> bool:
        return bool(current_maze.grid[r][c].walls & direction)

    # --- Fast C-Memory Drawing ---
    def draw_rect(rx: int, ry: int, rw: int, rh: int, color: int) -> None:
        b: int = bpp_val // 8
        if endian_val == 0: 
            pixel = bytes([color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF, 255])
        else:                
            pixel = bytes([255, (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF])
        row_bytes = pixel * rw
        for y in range(ry, min(ry + rh, win_h)):
            start: int = y * sl_val + rx * b
            end: int = start + rw * b
            buf[start:end] = row_bytes

    # --- Complete Render Pipeline ---
    def render() -> None:
        nonlocal wall_hex, path_hex, entry_hex, exit_hex

        # Recalculate active colors
        wall_hex = COLORS[current_color_mode % len(COLORS)]
        path_hex = COLORS[(current_color_mode + 1) % len(COLORS)]
        entry_hex = COLORS[(current_color_mode + 2) % len(COLORS)]
        exit_hex = COLORS[(current_color_mode + 3) % len(COLORS)]

        # 1. Clear background (including menu area)
        draw_rect(0, 0, win_w, win_h, bg_color)

        # 2. Calculate Path
        path_coords: set[tuple[int, int]] = set()
        if current_show_path and current_solution:
            curr_x, curr_y = current_maze.entry
            path_coords.add((curr_y, curr_x))
            for move in current_solution:
                if move == 'N': curr_y -= 1
                elif move == 'S': curr_y += 1
                elif move == 'E': curr_x += 1
                elif move == 'W': curr_x -= 1
                path_coords.add((curr_y, curr_x))

        # 3. Draw Cells & Paths
        for r in range(current_maze.height):
            for c in range(current_maze.width):
                x0, y0 = c * CELL_SIZE, r * CELL_SIZE
                cx, cy = x0 + WALL_W, y0 + WALL_W

                cell_color: int = bg_color
                if (r, c) == current_maze.entry: cell_color = entry_hex
                elif (r, c) == current_maze.exit: cell_color = exit_hex
                elif (r, c) in path_coords: cell_color = path_hex

                draw_rect(cx, cy, TILE, TILE, cell_color)

                if (r, c) in path_coords:
                    if r > 0 and (r - 1, c) in path_coords and not has_wall(r, c, Direction.NORTH):
                        draw_rect(cx, cy - WALL_W, TILE, WALL_W, path_hex)
                    if c > 0 and (r, c - 1) in path_coords and not has_wall(r, c, Direction.WEST):
                        draw_rect(cx - WALL_W, cy, WALL_W, TILE, path_hex)

        # 4. Draw Walls
        for r in range(current_maze.height):
            for c in range(current_maze.width):
                x0, y0 = c * CELL_SIZE, r * CELL_SIZE
                if has_wall(r, c, Direction.NORTH):
                    draw_rect(x0, y0, CELL_SIZE + WALL_W, WALL_W, wall_hex)
                if has_wall(r, c, Direction.WEST):
                    draw_rect(x0, y0, WALL_W, CELL_SIZE + WALL_W, wall_hex)
                if c == current_maze.width - 1 and has_wall(r, c, Direction.EAST):
                    draw_rect(x0 + CELL_SIZE, y0, WALL_W, CELL_SIZE + WALL_W, wall_hex)
                if r == current_maze.height - 1 and has_wall(r, c, Direction.SOUTH):
                    draw_rect(x0, y0 + CELL_SIZE, CELL_SIZE + WALL_W, WALL_W, wall_hex)

        # 5. Push Image to Window
        m.mlx_put_image_to_window(mlx_ptr, win_ptr, img_ptr, 0, 0)

        # 6. Draw Menu Text (Drawn directly to window over the image)
        menu_y = current_maze.height * CELL_SIZE + WALL_W + 10
        m.mlx_string_put(mlx_ptr, win_ptr, 10, menu_y, text_color, "[1] Regen  [2] Path  [3] Color  [4] Save & Quit")

    # --- Input Handling ---
    # X11 Linux keycodes. (macOS: 1=18, 2=19, 3=20, 4=21)
    KEY_1, KEY_2, KEY_3, KEY_4 = 10, 11, 12, 13 
    ESC_LINUX, ESC_MAC = 65307, 53

    def handle_key(keycode: int, param: dict) -> int:
        nonlocal current_maze, current_solution, current_show_path, current_color_mode

        if keycode == KEY_1:
            # Regenerate
            current_maze = MazeGenerator(
                config.WIDTH, config.HEIGHT, config.ENTRY,
                config.EXIT, config.PERFECT, config.SEED, config.PATTERN_42
            )
            current_maze.generate_maze(config.ALGORITHM)
            current_solution = current_maze.solve_maze()
            current_show_path = False
            render()
            
        elif keycode == KEY_2:
            # Toggle Path
            current_show_path = not current_show_path
            render()
            
        elif keycode == KEY_3:
            # Rotate Colors
            current_color_mode = (current_color_mode + 1) % len(COLORS)
            render()
            
        elif keycode == KEY_4 or keycode == ESC_LINUX or keycode == ESC_MAC:
            # Exit MLX loop cleanly
            param["m"].mlx_loop_exit(param["mlx_ptr"])
            
        return 0

    # --- Execution Flow ---
    m.mlx_key_hook(win_ptr, handle_key, {"mlx_ptr": mlx_ptr, "m": m})
    
    # Initial draw
    render()
    
    m.mlx_loop(mlx_ptr)