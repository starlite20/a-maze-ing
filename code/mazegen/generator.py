import random
class MazeGenerator:
    def __init__(self, width, height, entry, exit_pos, perfect, output_file):
        self.width = width
        self.height = height
        self.seed = random.randint(0, 2**32 - 1)

    def create_grid(self):
        # Create a grid with all walls
        self.grid = [[15 for _ in range(self.width)] for _ in range(self.height)]

    def print_grid(self):
        for row in self.grid:
            print("".join([cell for cell in row]))

mg = MazeGenerator(10, 10, (0, 0), (9, 9), True, "maze.txt")
mg.create_grid()
mg.print_grid()