import sys


class Configuration():
    def __init__(
            self, width, height, entry, exit_pos,
            output_file, perfect, seed, algorithm,
            display_mode, pattern_42, interactive_mode) -> None:
        self.set_width(width)
        self.set_height(height)
        self.set_entry(entry)
        self.set_exit(exit_pos)
        self.set_output_file(output_file)
        self.set_perfect(perfect)
        self.set_seed(seed)
        self.set_algorithm(algorithm)
        self.set_display_mode(display_mode)
        self.set_embed_pattern(pattern_42)
        self.set_interactive_mode(interactive_mode)

    def __str__(self):
        return (
            f"WIDTH={self.WIDTH}"
            f"HEIGHT={self.HEIGHT}"
            f"ENTRY={self.ENTRY[0]}, {self.ENTRY[1]}"
            f"EXIT={self.EXIT[0]}, {self.EXIT[1]}"
            f"OUTPUT_FILE={self.OUTPUT_FILE}"
            f"PERFECT={'True' if self.PERFECT else 'False'}"
            f"SEED={self.SEED}"
            f"ALGORITHM={self.ALGORITHM}"
            f"DISPLAY_MODE={self.DISPLAY_MODE}"
            f"PATTERN_42={'True' if self.PATTERN_42 else 'False'}"
            f"INTERACTIVE_MODE={'True' if self.INTERACTIVE_MODE else 'False'}"
        )

    def set_width(self, width):
        try:
            self.WIDTH = int(width)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for WIDTH: {width}")

    def set_height(self, height):
        try:
            self.HEIGHT = int(height)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for HEIGHT: {height}")

    def set_entry(self, entry):
        self.ENTRY = self.split_coords(entry, "ENTRY", self.WIDTH, self.HEIGHT)

    def set_exit(self, exit_pos):
        self.EXIT = self.split_coords(
            exit_pos, "EXIT", self.WIDTH, self.HEIGHT)

    def split_coords(self, coord_str: str,
                     field_name: str, width: int,
                     height: int) -> tuple[int, int]:
        try:
            coord_x = int(coord_str.split(",")[0].strip())
            coord_y = int(coord_str.split(",")[1].strip())
            if (coord_x < 0 or coord_y < 0
                    or coord_x >= width or coord_y >= height):
                raise ValueError(
                    f"Coordinates for {field_name} must be within "
                    f"maze dimensions (0 <= x < {width}, "
                    f"0 <= y < {height}): {coord_str}"
                )
            return (coord_x, coord_y)
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid coordinate format used "
                f"for {field_name}: {coord_str}"
            )

    def set_perfect(self, perfect):
        if perfect not in ["True", "False"]:
            raise ValueError(f"Invalid value for PERFECT: {perfect}")
        self.PERFECT = True if perfect == "True" else False

    def set_embed_pattern(self, embed_pattern):
        if embed_pattern not in ["True", "False"]:
            raise ValueError(f"Invalid value for PATTERN_42: {embed_pattern}")
        self.PATTERN_42 = True if embed_pattern == "True" else False

    def set_interactive_mode(self, interactive_mode):
        if interactive_mode not in ["True", "False"]:
            raise ValueError(
                f"Invalid value for INTERACTIVE_MODE: {interactive_mode}")
        self.INTERACTIVE_MODE = True if interactive_mode == "True" else False

    def set_seed(self, seed):
        try:
            if seed != "":
                self.SEED = int(seed)
            else:
                self.SEED = 0
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for seed: {seed}")

    def set_algorithm(self, algorithm):
        if algorithm not in ["", "DFS"]:
            raise ValueError(
                f"Specified algorithm '{algorithm}' not supported."
            )
        self.ALGORITHM = algorithm

    def set_display_mode(self, display_mode):
        if display_mode not in ["", "ASCII", "MLX"]:
            raise ValueError(
                f"Specified display mode '{display_mode}' not supported."
            )
        self.DISPLAY_MODE = display_mode

    def set_output_file(self, output_file):
        self.OUTPUT_FILE = output_file

    def update_value(self, key: str, value: str) -> None:
        if not isinstance(key, str):
            raise TypeError("Key must be a string.")

        key = key.upper()
        if key == "WIDTH":
            self.set_width(value)
        elif key == "HEIGHT":
            self.set_height(value)
        elif key == "ENTRY":
            self.set_entry(value)
        elif key == "EXIT":
            self.set_exit(value)
        elif key == "PERFECT":
            self.set_perfect(value)
        elif key == "SEED":
            self.set_seed(value)
        elif key == "ALGORITHM":
            self.set_algorithm(value)
        elif key == "DISPLAY_MODE":
            self.set_display_mode(value)
        elif key == "PATTERN_42":
            self.set_embed_pattern(value)
        elif key == "OUTPUT_FILE":
            self.OUTPUT_FILE = value
        else:
            raise ValueError(f"Unknown configuration key: {key}")


def validate_and_cast_config(config) -> Configuration:
    # Ensure all required keys are present in Configuration File
    required_keys = ["WIDTH", "HEIGHT", "ENTRY",
                     "EXIT", "PERFECT", "OUTPUT_FILE"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(
            f"Missing required mandatory config keys: "
            f"{', '.join(missing_keys)}"
        )

    # Casting and Storing each Configuration Value
    configuration = Configuration(
        width=config["WIDTH"],
        height=config["HEIGHT"],
        entry=config["ENTRY"],
        exit_pos=config["EXIT"],
        output_file=config["OUTPUT_FILE"],
        perfect=config["PERFECT"],
        seed=config["SEED"] if "SEED" in config else "",
        algorithm=config["ALGORITHM"] if "ALGORITHM" in config else "",
        display_mode=config["DISPLAY_MODE"] if "DISPLAY_MODE" in config else "",
        pattern_42=config["PATTERN_42"] if "PATTERN_42" in config else "False",
        interactive_mode=config["INTERACTIVE_MODE"] if "INTERACTIVE_MODE" in config else "False"
    )

    return configuration


def get_val(text):
    if not text or text.startswith('#'):
        return None, None
    parts = text.split('=')
    if len(parts) != 2:
        raise ValueError(f"Invalid config line: '{text}'")
    LHS = parts[0].strip()
    RHS = parts[1].strip()
    return LHS, RHS


def read_config(filename):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            configuration = {}
            for line in lines:
                key, value = get_val(line.strip())
                if key is not None:
                    configuration[key] = value
            return configuration

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading config file '{filename}': {e}")
        sys.exit(1)
