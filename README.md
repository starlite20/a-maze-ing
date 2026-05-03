_This project has been created as part of the 42 curriculum by ssujaude, sobied._

# A-Maze-ing

## Description
__A-Maze-ing__ is a project focused on building a Maze Generator and Maze Solver. Through this project, we explore deeply through the concepts of Graphs & Trees, which leads us to several algorithms to traverse through them. These algorithms help build the maze, and solve as well. This comprehensive Maze Generation and Solving Code is developed in Python.

Throughout the project, modularity and clean readability of the code is a key aspect, thereby allowing the core generation logic to be decoupled from configuration handling and execution flow. The engine handles the creation of complex grid-based structures, ensures full connectivity across the maze, and outputs the results in a standardized hexadecimal format.

### Key Features
*   **Dual Generation Logic:** Supports **Depth-First Search (DFS) Algorithm** and **Eller's Algorithm**.
*   **Perfect & Imperfect Mazes:** Create & solve both single-path spanning trees and looped mazes.
*   **Maze Solving:** Integrated **Breadth First Search (BFS) based solver** to calculate the shortest path.
*   **42 Pattern Embedding:** Integration of the "42" pattern into the maze.
*   **Geometric Constraints:** Automatic prevention of large (3x3) open corridors.
*   **Terminal ASCII Visuals:** Explore the maze through the terminal in a Retro 8-bit styled manner.
*   **Animated Maze Generation:** View the clear generation of the maze in a detailed step manner.

---
## Instructions

### Installation and Setup

1. Clone the repository:
```
git clone <repository_url>
cd a-maze-ing
```

```
pip install -r requirements.txt
```

```
python3 -m venv venv
source venv/bin/activate
```


### Execution

The program is executed by passing a configuration text file as a command-line argument.
```
python3 a_maze_ing.py config.txt
```

## Configuration File Structure
The configuration file follows a KEY=VALUE format. All parameters must be defined.

| Key         | Description                     | Data Type     | Example              |
|-------------|---------------------------------|--------------|----------------------|
| WIDTH       | Maze width (cells)             | int          | WIDTH=20             |
| HEIGHT      | Maze height (cells)            | int          | HEIGHT=15            |
| ENTRY       | Entry coordinates (x,y)        | int, int     | ENTRY=0,0            |
| EXIT        | Exit coordinates (x,y)         | int, int     | EXIT=19,14           |
| OUTPUT_FILE | Output filename                | string       | OUTPUT_FILE=maze.txt |
| PERFECT     | Perfect maze toggle            | boolean      | PERFECT=True         |
| ALGORITHM   | Generation algorithm           | string       | ALGORITHM=DFS        |
| SEED        | Random seed for reproducibility| int          | SEED=42              |
| PATTERN_42  | Enable 42 pattern embedding    | boolean      | PATTERN_42=True      |

---

## Understanding the Project

### Maze Cell
Each direction is represented as a bit:

- North = 2^0
- East  = 2^1
- South = 2^2
- West  = 2^3

A wall is present if the corresponding bit is set.


### Perfect Maze
- When a maze has all parts of the maze accessible, while having only one path from entry point to exit point, this is a Perfect Maze
- In mathematical explanation, Perfect Mazes are a form of Spanning tree with N-1 edges, where N is the total number of nodes present in the graph.


---
## Maze Generation Algorithm

- Depth-First Search (DFS)
  A backtracking algorithm that produces long, winding paths and guarantees a perfect maze when enabled.

- Eller’s Algorithm
  A row-by-row algorithm optimized for memory usage, capable of generating large mazes efficiently.

### Depth-First Search (DFS)
- DFS is a very popular backtracking algorithm that explores the maze by going as deep as possible before backtracking.
- It is typically implemented using a **STACK**, which naturally supports this behavior.
- One of its defining characteristics is the creation of long, winding corridors with very few branches. When used for maze generation, it produces a *perfect maze*, meaning there is exactly one unique path between any two points.

#### Implementation
- Implemented using an **explicit stack (iterative approach)** instead of recursion.
- This avoids Python recursion limits and potential `RecursionError` on large mazes.
- Starts from the entry point and randomly explores unvisited neighbours.
- Walls are removed between the current cell and the chosen neighbour.
- When no unvisited neighbours are available, the algorithm backtracks using the stack.

#### Benefits
- Simple and intuitive logic
- Stack-based traversal makes control flow predictable
- Easy to implement and debug
- Produces complex and visually interesting maze structures
- Guarantees a single-solution path (perfect maze), making solver validation straightforward


### Eller’s Algorithm
- Eller’s Algorithm generates the maze **ROW BY ROW**, instead of exploring the full grid.
- It does not use recursion or a stack. Instead, it relies on **set management / grouping concept**.
- Each row is processed in two phases:
  - Horizontal merging of adjacent cells
  - Vertical connections to the next row
- Ensures that every set has at least one downward connection, preventing isolated sections.

#### Implementation
- Implemented using a **set-based approach** where each cell belongs to a group (set ID).
- Adjacent cells are randomly merged if they belong to different sets.
- On the final row, all remaining disjoint sets are forcefully merged to ensure full connectivity.
- Vertical connections are guaranteed such that each set propagates at least one connection downward.
- Integrated handling for:
  - **Pattern cells ("42")**, treated as blocked cells during generation
  - **Post-processing connectivity check**, where BFS is used to connect any isolated components
  - **3x3 open space prevention**, ensuring maze structure integrity

#### Benefits
- Memory efficient as only current and next row state is needed
- Does not rely on recursion or stack
- Scales well for large mazes
- Deterministic row-by-row processing makes it easier to control structure
- Works well with constraints like pattern embedding and controlled openings



### Imperfect Maze Generation

Imperfect maze generation is built on top of the perfect maze produced by either DFS or Eller’s Algorithm.

The process begins by generating a fully connected *perfect maze* (a spanning tree), where there is exactly one unique path between any two cells. Once this structure is established, additional walls are selectively removed to introduce loops and multiple possible paths.

Our approach:
- We iteratively remove walls between adjacent cells to create alternative routes.
- Each removal is validated before being applied to ensure it does not violate structural constraints.
- A key constraint enforced is the prevention of large open areas (such as 3x3 corridors), which would reduce maze complexity.
- Bitwise wall checks are used to verify whether a wall can be safely removed without breaking constraints.

This ensures the maze contains multiple valid paths while preserving structural complexity.

---

### Why These Algorithms
DFS was selected for its simplicity and ability to generate complex mazes with a single valid path. It is well-suited for validating solver correctness and provides a strong baseline implementation.

Eller’s Algorithm was chosen to complement DFS with a more scalable and memory-efficient approach. Its row-based design avoids storing the entire maze state, making it suitable for large-scale maze generation.

Together, these algorithms provide a balance between structural complexity and performance, covering both exploratory and optimized generation strategies.

---

## Maze Solving through Breadth First Search Algorithm (BFS)

Maze solving is implemented using the Breadth-First Search (BFS) algorithm to guarantee the shortest path from entry to exit.

BFS works by exploring the maze level by level:
- Starting from the entry cell, all reachable neighboring cells are explored first
- A queue is used to maintain traversal order
- Each visited cell is marked to prevent revisiting
- Parent tracking is maintained to reconstruct the final path

Our implementation:
- Uses a queue-based approach for traversal
- Ensures that only valid, non-blocked, and connected cells are explored
- Stops as soon as the exit cell is reached
- Reconstructs the shortest path by backtracking using stored parent references

Why BFS:
- Guarantees the shortest path in an unweighted grid
- Simple and reliable for grid-based traversal
- Works seamlessly with both perfect and imperfect mazes

This makes BFS an ideal choice for validating maze correctness and providing optimal path solutions.

---

## Technical Choices and Reusability

The project was designed with a strong focus on modularity and separation of concerns. Core logic is isolated from configuration handling and execution, making the system easier to extend, test, and reuse.

The central component of the project is the `MazeGenerator` class, which encapsulates both generation and solving logic. This class is independent of input/output handling and can be reused in other Python-based applications.

Reusable components include:
- **Maze generation engine**  
  Supports multiple algorithms (DFS and Eller’s) through a unified interface.

- **Maze solving logic (BFS)**  
  Can be reused independently to compute shortest paths on any grid-based structure.

- **Configuration-driven execution**  
  The system is fully controlled via an external configuration file, allowing behavior changes without modifying code.

- **Grid and cell abstraction**  
  The internal representation of the maze is generalized and can be extended to other grid-based problems.

- **Decoupled architecture**  
  Clear separation between generation logic, constraints, and output formatting improves maintainability and scalability.

- **Standardized hexadecimal output**  
  The maze is exported in a compact hexadecimal format, ensuring compatibility with external tools and visualizers.

---

## Advanced Features

- ### Pattern embedding with connectivity preservation
  The “42” pattern is embedded into the maze without breaking overall solvability.

  The approach is implemented by defining the pattern as a 2D reference map. During grid initialization, the corresponding cells are marked as blocked before any generation algorithm is applied. Both DFS and Eller’s algorithms respect these blocked cells by checking their status before carving paths.

  To ensure the maze remains fully connected, a post-processing step is applied. This step validates connectivity and resolves any isolated sections introduced by the pattern constraints.

---

- ### Geometric constraint system
  Prevents the formation of large open areas (specifically 3x3 empty regions), preserving the structural integrity of the maze.

  The system iterates through the grid (excluding boundary cells) and checks for potential 3x3 open configurations. For each candidate region:
  - Boundary conditions are validated to avoid out-of-bounds checks
  - Bitwise operations are used to inspect wall presence (RIGHT and BOTTOM walls)
  - If all required walls are absent, the region qualifies as a potential 3x3 open space

  If such a condition is detected, wall carving is restricted to prevent the formation of large open corridors. This ensures the maze retains its intended complexity.

---

- ### Multiple generation strategies
  Supports both DFS and Eller’s Algorithm, allowing flexibility between exploratory generation (DFS) and memory-efficient structured generation (Eller’s).

---

- ### Deterministic generation support
  A configurable seed value enables reproducible maze generation, which is useful for testing, debugging, and validation.

---

- ### Visual representation
  Provides a terminal-based ASCII visualization of the maze, displaying:
  - Walls and open paths
  - Entry and exit points
  - Rotating color variations for improved readability

---

- ### Animated maze generation
  Inspired by concepts from game development, this feature visualizes the step-by-step construction of the maze.

  - Each generation step is logged into a `history.json` file
  - The animation system replays these steps on a temporary grid
  - The terminal is continuously refreshed to simulate real-time maze construction

  This approach separates generation from visualization, allowing the animation to be replayed without recomputing the maze.

---

## Package Documentation

### Overview

- `mazegen` is a standalone Python package that procedurally generates mazes using either a **Depth-First Search (DFS)** or **Eller's** algorithm.
- It supports perfect mazes (single unique path), imperfect mazes (with loops), optional pattern embedding, seed-based reproducibility, and BFS-based solving.

---

### Installation

From the root of the repository, inside a virtual environment:

```bash
pip install mazegen-*.whl
## or
pip install mazegen-*.tar.gz
```

To build the package yourself from source:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install build
python3 -m build
```

This produces both `.whl` and `.tar.gz` files in the `dist/` directory.

---

### Quick Start

```python
from mazegen import MazeGenerator

maze = MazeGenerator(
    width=15,
    height=15,
    entry_pos=(0, 0),
    exit_pos=(14, 14),
    perfect=True,
    seed=42
)

maze.generate_maze()       # uses DFS by default
solution = maze.solve_maze()

print(solution)            # e.g. "SSSSEENNSS"
```

---

### Class Reference

#### `MazeGenerator`

```python
MazeGenerator(
    width: int,
    height: int,
    entry_pos: tuple[int, int],
    exit_pos: tuple[int, int],
    perfect: bool,
    seed: int | None,
    pattern_42: bool = False
)
```

| Parameter | Type | Description |
|---|---|---|
| `width` | `int` | Number of columns. Must be >= 2. |
| `height` | `int` | Number of rows. Must be >= 2. |
| `entry_pos` | `tuple[int, int]` | Start cell as `(x, y)`. Must be within bounds. |
| `exit_pos` | `tuple[int, int]` | End cell as `(x, y)`. Must differ from entry. |
| `perfect` | `bool` | If `True`, generates a perfect maze (no loops). |
| `seed` | `int \| None` | Fixed seed for reproducibility. Pass `None` for random. |
| `pattern_42` | `bool` | If `True`, embeds a visible `42` pattern in the center. |

---

### Generating a Maze

```python
maze.generate_maze(algorithm="DFS")    ## default
maze.generate_maze(algorithm="ELLER")  ## row-by-row algorithm
```

Supported algorithms:

| Value | Description |
|---|---|
| `"DFS"` | Recursive backtracker. Produces long winding corridors. |
| `"ELLER"` | Row-by-row set merging. Faster on tall mazes. |

After calling `generate_maze()`, the grid is fully populated and ready to
use. If `seed=None` was passed, the actual seed used is captured and stored
in `maze.seed` for later reference.

---

### Custom Parameters — Examples

#### Fixed seed for reproducibility

```python
maze = MazeGenerator(
    width=20, height=20,
    entry_pos=(0, 0), exit_pos=(19, 19),
    perfect=True,
    seed=1234
)
maze.generate_maze()
print(f"Seed used: {maze.seed}")
```

#### Random seed — capture after generation

```python
maze = MazeGenerator(
    width=20, height=20,
    entry_pos=(0, 0), exit_pos=(19, 19),
    perfect=False,
    seed=None
)
maze.generate_maze()
print(f"Seed used: {maze.seed}")
## Pass this value back as seed= to reproduce the same maze
```

#### Imperfect maze with loops

```python
maze = MazeGenerator(
    width=15, height=15,
    entry_pos=(0, 0), exit_pos=(14, 14),
    perfect=False,   ## removes ~5% of internal walls after generation
    seed=99
)
maze.generate_maze()
```

#### With 42 pattern

```python
## Maze must be at least 11 wide and 9 tall for the pattern to fit
maze = MazeGenerator(
    width=20, height=15,
    entry_pos=(0, 0), exit_pos=(19, 14),
    perfect=True,
    seed=7,
    pattern_42=True
)
maze.generate_maze()
```

---

### Accessing the Grid Structure

After `generate_maze()`, the maze is accessible via `maze.grid` —
a 2D list indexed as `maze.grid[row][col]`, i.e. `maze.grid[y][x]`.

```python
## Iterate all cells
for row in maze.grid:
    for cell in row:
        print(cell.x, cell.y, bin(cell.walls))
```

#### `Cell` attributes

| Attribute | Type | Description |
|---|---|---|
| `cell.x` | `int` | Column index of the cell. |
| `cell.y` | `int` | Row index of the cell. |
| `cell.walls` | `int` | Bitmask of closed walls (see below). |
| `cell.visited` | `bool` | Whether the cell was reached during generation. |
| `cell.pattern` | `bool` | Whether the cell is part of the 42 pattern. |

#### Wall bitmask

Each cell's `walls` integer encodes which walls are **closed** (present):

| Bit | Value | Direction |
|---|---|---|
| 0 | 1 | North |
| 1 | 2 | East |
| 2 | 4 | South |
| 3 | 8 | West |

```python
from mazegen import Direction

cell = maze.grid[5][3]          ## row 5, column 3

## Check individual walls
if cell.walls & Direction.NORTH:
    print("North wall is closed")

if cell.walls & Direction.EAST:
    print("East wall is closed")

## 15 = all walls closed (0b1111)
## 0  = all walls open
```

---

### Solving the Maze

```python
solution = maze.solve_maze()
print(solution)   ## e.g. "SSSEENWWSS"
```

Returns a string of cardinal direction characters representing the
**shortest path** from `entry_pos` to `exit_pos` using BFS.

| Character | Meaning |
|---|---|
| `N` | Move north (y - 1) |
| `E` | Move east  (x + 1) |
| `S` | Move south (y + 1) |
| `W` | Move west  (x - 1) |

Returns an empty string `""` if no path exists.

#### Replaying the solution manually

```python
x, y = maze.entry
for move in solution:
    if move == 'N': y -= 1
    elif move == 'S': y += 1
    elif move == 'E': x += 1
    elif move == 'W': x -= 1

assert (x, y) == maze.exit   ## always True for a valid maze
```

---

### Generation History & Animation

Every carve and visit step is recorded during generation and accessible
via `maze.history` — a list of event dictionaries.

```python
maze.generate_maze()

## Each entry looks like:
## {"step": 0, "action": "visit", "cell": [x, y]}
## {"step": 1, "action": "carve", "from_": [x, y], "to": [x, y]}
## {"step": 2, "action": "backtrack", "to": [x, y]}

for event in maze.history[:5]:
    print(event)
```

#### Exporting history to JSON

```python
maze.export_history("history.json")
```

Writes all events to a JSON file, which can be replayed frame-by-frame
for animation.

---

### Printing the Grid (debug)

```python
maze.print_grid()
## Outputs one hex digit per cell, one row per line:
## 9511F...
## A3C0B...
```

Each hex digit matches the wall bitmask for that cell, identical to the
output file format used by the main program.

---

### Complete Example

```python
from mazegen import MazeGenerator, Direction

## Create a 20x15 perfect maze with a fixed seed
maze = MazeGenerator(
    width=20,
    height=15,
    entry_pos=(0, 0),
    exit_pos=(19, 14),
    perfect=True,
    seed=2025,
    pattern_42=True
)

## Generate using Eller's algorithm
maze.generate_maze(algorithm="ELLER")

## Print the seed actually used
print(f"Seed: {maze.seed}")

## Solve and print the path
solution = maze.solve_maze()
print(f"Solution ({len(solution)} steps): {solution}")

## Inspect a specific cell
cell = maze.grid[0][0]   ## top-left corner
print(f"Cell (0,0) walls: {cell.walls:04b}")

## Check if north wall of entry is closed (should be — it's a border)
if cell.walls & Direction.NORTH:
    print("Border wall intact ✓")

## Export generation history
maze.export_history("history.json")
```

---


## Team and Project Management

### Team Roles
- **Shared Responsibilities**
  - Core architecture and `MazeGenerator` class design  
  - Configuration file parsing and validation  
  - Geometric constraint system (3x3 open space prevention)  
  - Imperfect maze generation logic  
  - ASCII visualization and terminal rendering  
  - Code refactoring and modularization  
  - Documentation and packaging  

- **ssujaude**  
  - Depth-First Search (DFS) implementation  
  - Breadth-First Search (BFS) solver  
  - Pattern embedding
  - Maze generation animation system and history tracking  

- **sobied**
  - Eller’s Algorithm implementation
  - Connectivity validation logic
  - Makefile setup and execution flow 
  - Unit testing and validation  


### Planning and Evolution

The project was developed through iterative sprints. Initial efforts focused on designing and implementing the core `MazeGenerator` class collaboratively.

Following this, responsibilities were divided, with each team member implementing one of the core maze generation algorithms in parallel. Once the algorithms were completed, the remaining components were distributed and developed independently, including:
- Edge case handling
- Configuration file parsing
- Makefile setup
- Interactive menu design
- Object-oriented structuring
- Documentation and packaging

Throughout development, the design evolved to ensure compatibility between different generation strategies while maintaining a consistent and reusable architecture.

**What worked well?**
  Modular design enabled parallel development with minimal conflicts.

**What could be improved?**
  An attempt was made to integrate MinilibX for graphical rendering, but it was not completed due to time constraints.
  


### Tools Used
- Git and GitHub for version control
- Python virtual environments for dependency management
- Unit testing for validation
- Collaborative planning through iterative development

---

## Resources
- Eller’s Algorithm by Jamis Buck  (https://weblog.jamisbuck.org/2010/12/29/maze-generation-eller-s-algorithm)
- Computerphile Maze Generation Video (https://www.youtube.com/watch?v=uctN47p_KVk)
- BFS and DFS Traversals (https://www.youtube.com/watch?v=vf-cxgUXcMk)
- Graph Theory concepts: spanning trees and traversal algorithms
- Maze Generation Algorithms (https://www.youtube.com/watch?v=ioUl1M77hww)
- Programming Mazes (https://www.youtube.com/watch?v=Y37-gB83HKE)
- What School Didn't Tell You About Mazes (https://www.youtube.com/watch?v=uctN47p_KVk)

---

## AI Usage Disclosure
- Assistance in refining documentation structure and clarity
- Minor support in reviewing explanations for correctness and readability

---
