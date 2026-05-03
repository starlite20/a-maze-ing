class Configuration():
    """Manages and validates maze generation settings.

    This class handles the parsing, casting, and validation of raw configuration
    strings into appropriate Python types (int, tuple, bool, etc.).
    """
    def __init__(
            self, width: str, height: str, entry: str, exit_pos: str,
            output_file: str, perfect: str, seed: str, algorithm: str,
            pattern_42: str) -> None:
        """Initializes Configuration by validating and setting all parameters.

        Args:
            width (str): The grid width.
            height (str): The grid height.
            entry (str): Comma-separated entry coordinates (x,y).
            exit_pos (str): Comma-separated exit coordinates (x,y).
            output_file (str): Path to save the generated maze.
            perfect (str): "True" or "False" indicating if loops are forbidden.
            seed (str): Randomness seed for reproducibility.
            algorithm (str): The maze generation algorithm to use.
            pattern_42 (str): "True" or "False" to embed a specific pattern.
        """
        self.set_width(width)
        self.set_height(height)
        self.set_entry(entry)
        self.set_exit(exit_pos)
        self.set_output_file(output_file)
        self.set_perfect(perfect)
        self.set_seed(seed)
        self.set_algorithm(algorithm)
        self.set_embed_pattern(pattern_42)

    def __str__(self) -> str:
        """Returns a string representation of the current configuration.

        Returns:
            str: A formatted string of all key-value configuration pairs.
        """
        return (
            f"WIDTH={self.WIDTH}"
            f"HEIGHT={self.HEIGHT}"
            f"ENTRY={self.ENTRY[0]}, {self.ENTRY[1]}"
            f"EXIT={self.EXIT[0]}, {self.EXIT[1]}"
            f"OUTPUT_FILE={self.OUTPUT_FILE}"
            f"PERFECT={'True' if self.PERFECT else 'False'}"
            f"SEED={self.SEED}"
            f"ALGORITHM={self.ALGORITHM}"
            f"PATTERN_42={'True' if self.PATTERN_42 else 'False'}"
        )

    def set_width(self, width: str) -> None:
        """Casts and sets the maze width.

        Args:
            width (str): The width value to set.

        Raises:
            ValueError: If width is not a valid integer.
        """
        try:
            self.WIDTH = int(width)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for WIDTH: {width}")

    def set_height(self, height: str) -> None:
        """Casts and sets the maze height.

        Args:
            height (str): The height value to set.

        Raises:
            ValueError: If height is not a valid integer.
        """
        try:
            self.HEIGHT = int(height)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for HEIGHT: {height}")

    def set_entry(self, entry: str) -> None:
        """Parses and sets the entry point coordinates.

        Args:
            entry (str): String format "x,y".
        """
        self.ENTRY = self.split_coords(
            entry, "ENTRY", self.WIDTH, self.HEIGHT)

    def set_exit(self, exit_pos: str) -> None:
        """Parses and sets the exit point coordinates.

        Args:
            exit_pos (str): String format "x,y".
        """
        self.EXIT = self.split_coords(
            exit_pos, "EXIT", self.WIDTH, self.HEIGHT)

    def split_coords(self, coord_str: str, field_name: str,
                     width: int, height: int) -> tuple[int, int]:
        """Splits a coordinate string and validates bounds against grid dimensions.

        Args:
            coord_str (str): The "x,y" string to parse.
            field_name (str): Label for error reporting (e.g., "ENTRY").
            width (int): Current grid width for boundary check.
            height (int): Current grid height for boundary check.

        Returns:
            tuple[int, int]: Validated (x, y) integer tuple.

        Raises:
            ValueError: If format is invalid or coordinates are out of bounds.
        """
        try:
            parts = coord_str.split(",")
            coord_x = int(parts[0].strip())
            coord_y = int(parts[1].strip())
        except (ValueError, TypeError, IndexError):
            raise ValueError(
                f"Invalid coordinate format for {field_name}: '{coord_str}'"
            )
        if coord_x < 0 or coord_y < 0 or coord_x >= width or coord_y >= height:
            raise ValueError(
                f"{field_name} coordinates out of bounds "
                f"(0 <= x < {width}, 0 <= y < {height}): '{coord_str}'"
            )
        return (coord_x, coord_y)

    def set_perfect(self, perfect: str) -> None:
        """Sets the 'perfect' maze flag.

        Args:
            perfect (str): Must be literal "True" or "False".

        Raises:
            ValueError: If the string is not a valid boolean representation.
        """
        if perfect not in ["True", "False"]:
            raise ValueError(f"Invalid value for PERFECT: {perfect}")
        self.PERFECT = True if perfect == "True" else False

    def set_embed_pattern(self, embed_pattern: str) -> None:
        """Sets the PATTERN_42 flag.

        Args:
            embed_pattern (str): Must be literal "True" or "False".

        Raises:
            ValueError: If the string is not a valid boolean representation.
        """
        if embed_pattern not in ["True", "False"]:
            raise ValueError(f"Invalid value for PATTERN_42: {embed_pattern}")
        self.PATTERN_42 = True if embed_pattern == "True" else False

    def set_seed(self, seed: str) -> None:
        """Casts and sets the randomness seed.

        Args:
            seed (str): The seed value. Can be empty for random generation.

        Raises:
            ValueError: If seed is provided but is not an integer.
        """
        self.SEED: int | None = None
        try:
            if seed != "":
                self.SEED = int(seed)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value for seed: {seed}")

    def set_algorithm(self, algorithm: str) -> None:
        """Validates and sets the maze generation algorithm.

        Args:
            algorithm (str): Algorithm name (e.g., "DFS", "ELLER").

        Raises:
            ValueError: If the algorithm is not supported.
        """
        if algorithm not in ["", "DFS", "ELLER"]:
            raise ValueError(
                f"Specified algorithm '{algorithm}' not supported.")
        self.ALGORITHM = algorithm

    def set_output_file(self, output_file: str) -> None:
        """Sets the output destination path.

        Args:
            output_file (str): The file path string.
        """
        self.OUTPUT_FILE = output_file

    def update_value(self, key: str, value: str) -> None:
        """Updates a specific configuration setting by key name.

        Args:
            key (str): The configuration field name (case-insensitive).
            value (str): The new value to set.

        Raises:
            TypeError: If key is not a string.
            ValueError: If the key is unknown.
        """
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
        elif key == "PATTERN_42":
            self.set_embed_pattern(value)
        elif key == "OUTPUT_FILE":
            self.OUTPUT_FILE = value
        else:
            raise ValueError(f"Unknown configuration key: {key}")


def validate_and_cast_config(config: dict[str, str]) -> Configuration:
    """Validates a dictionary of raw config data and returns a Configuration object.

    Args:
        config (dict[str, str]): Key-value pairs extracted from a config file.

    Returns:
        Configuration: A fully initialized and validated configuration instance.

    Raises:
        ValueError: If mandatory keys are missing from the dictionary.
    """
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
        pattern_42=config["PATTERN_42"] if "PATTERN_42" in config else "False",
    )

    return configuration


def get_val(text: str) -> tuple[str | None, str | None]:
    """Parses a single line from a configuration file.

    Args:
        text (str): A line of text from the file.

    Returns:
        tuple[str | None, str | None]: A tuple containing (Key, Value). 
            Returns (None, None) for empty lines or comments.

    Raises:
        ValueError: If the line contains an invalid assignment format.
    """
    if not text or text.startswith('#'):
        return None, None
    parts = text.split('=')
    if len(parts) != 2:
        raise ValueError(f"Invalid config line: '{text}'")
    LHS = parts[0].strip()
    RHS = parts[1].strip()
    return LHS, RHS


def read_config(filename: str) -> dict[str, str]:
    """Reads a configuration file and parses it into a dictionary.

    Args:
        filename (str): Path to the configuration file.

    Returns:
        dict[str, str]: Dictionary of raw configuration keys and values.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If an error occurs during file reading or parsing.
    """
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            configuration = {}
            for line in lines:
                key, value = get_val(line.strip())
                if key is not None and value is not None:
                    configuration[key] = value
            return configuration

    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File '{filename}' not found.")
    except Exception as e:
        raise ValueError(f"Error reading config file '{filename}': {e}")
