import sys
import mazegen


class Configuration():
    def __init__(self, width, height, entry, exit_pos, output_file, perfect):
        self.set_width(width)
        self.set_height(height)
        self.set_entry(entry)
        self.set_exit(exit_pos)
        self.set_output_file(output_file)
        self.set_perfect(perfect)

    def __str__(self):
        return f"Configuration(WIDTH={self.WIDTH}, HEIGHT={self.HEIGHT}, ENTRY={self.ENTRY}, EXIT={self.EXIT}, OUTPUT_FILE='{self.OUTPUT_FILE}', PERFECT={self.PERFECT})"

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

    def split_coords(self, coord_str: str, field_name: str, width: int, height: int) -> tuple[int, int]:
        try:
            coord_x = int(coord_str.split(",")[0].strip())
            coord_y = int(coord_str.split(",")[1].strip())
            if coord_x < 0 or coord_y < 0 or coord_x >= width or coord_y >= height:
                raise ValueError(
                    f"Coordinates for {field_name} must be within maze dimensions (0 <= x < {width}, 0 <= y < {height}): {coord_str}")
            return (coord_x, coord_y)
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid coordinate format used for {field_name}: {coord_str}")

    def set_perfect(self, perfect):
        if perfect not in ["True", "False"]:
            raise ValueError(f"Invalid value for PERFECT: {perfect}")
        self.PERFECT = True if perfect == "True" else False

    def set_output_file(self, output_file):
        self.OUTPUT_FILE = output_file


def validate_and_cast_config(config) -> Configuration:
    # Ensure all required keys are present in Configuration File
    required_keys = ["WIDTH", "HEIGHT", "ENTRY",
                     "EXIT", "PERFECT", "OUTPUT_FILE"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(
            f"Missing required config keys: {', '.join(missing_keys)}")

    # Casting and Storing each Configuration Value
    configuration = Configuration(
        width=config["WIDTH"],
        height=config["HEIGHT"],
        entry=config["ENTRY"],
        exit_pos=config["EXIT"],
        output_file=config["OUTPUT_FILE"],
        perfect=config["PERFECT"]
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


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Usage: python a_maze_ing.py <config_file>")
        sys.exit(1)

    maze_config = read_config(sys.argv[1])
    try:
        config = validate_and_cast_config(maze_config)
        print(config)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
