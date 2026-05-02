_This project has been created as part of the 42 curriculum by ssujaude, sobied._

# A-Maze-ing

## 📖 Description
__A-Maze-ing__ is a project focused on building a Maze Generator and Maze Solver. Through this project, we explore deeply through the concepts of Graphs & Trees, which leads us to several algorithms to traverse through them. These algorithms help build the maze, and solve as well. This comprehensive Maze Generation and Solving Code is developed in Python.

Throughout the project, modularity and clean readability of the code is a key aspect, thereby allowing the core generation logic to be decoupled from the user interface and configuration management. The engine handles the creation of complex grid-based structures, ensures mathematical connectivity, and outputs the results in a standardized hexadecimal format.

### ✨ Key Features
*   **Dual Generation Logic:** Supports **Depth-First Search (DFS) Algorithm** and **Eller's Algorithm**.
*   **Perfect & Imperfect Mazes:** Toggle between single-path spanning trees or looped mazes.
*   **42 Pattern Embedding:** Integration of the "42" pattern into the maze.
*   **Maze Solving:** Integrated **Breadth First Search (BFS) based solver** to calculate the shortest path.
*   **Geometric Constraints:** Automatic prevention of large (3x3) open corridors.
*   **Animated Maze Generation:** View the clear generation of the maze in a detailed step manner.

---

## 🛠 Instructions

### Installation
1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd a-maze-ing
(Optional) Setup virtual environment:

Bash
python3 -m venv venv
source venv/bin/activate
Install dependencies:

Bash
pip install -r requirements.txt
Usage
Run the program by passing a configuration file:

Bash
python3 a_maze_ing.py config.txt
⚙️ Configuration File (config.txt)
The configuration file uses a KEY=VALUE format.

Key	Description	Example
WIDTH	Maze width (number of cells)	WIDTH=20
HEIGHT	Maze height	HEIGHT=15
ENTRY	Entry coordinates (x,y)	ENTRY=0,0
EXIT	Exit coordinates (x,y)	EXIT=19,14
OUTPUT_FILE	Output filename for hex data	OUTPUT_FILE=maze.txt
PERFECT	Generate perfect maze (True/False)	PERFECT=True
Additional Options:

SEED: Set a specific random seed for reproducibility.

ALGORITHM: Choose DFS or ELLER.

PATTERN_42: Embed the “42” pattern (True/False).

🧠 Algorithms & Logic
Maze Generation
DFS (Depth-First Search): A stack-based backtracking approach. It explores as far as possible before backtracking, creating long, winding corridors.

Eller’s Algorithm: A row-by-row generation method using set-merging logic. Highly memory-efficient (O(N) space) for extremely large mazes.

Pathfinding
BFS Solver: Finds the shortest path from the entry to the exit by exploring the grid in layers, ensuring mathematical optimality in path length.

📦 Reusable Module
The logic is encapsulated in the MazeGenerator class, designed to be imported into other Python projects.

Python
from mazegen import MazeGenerator

# 1. Instantiation
maze = MazeGenerator(width=20, height=15, entry_pos=(0, 0), 
                     exit_pos=(19, 14), perfect=True, seed=42)

# 2. Generation
maze.generate_maze(algorithm="DFS")

# 3. Solving
solution_path = maze.solve_maze()
print(f"Path taken: {solution_path}") # e.g., "EENNSWW"


## Project Management
As a team, we handled the project by splitting up core functionalities and approached the design in a collaborative manner.

Roles: Collaborative design on algorithm logic, memory management optimization, and unit testing.
Planning: Iterative sprints starting with DFS foundation, followed by row-based Eller's logic and pattern embedding.


Graph Theory: Spanning trees, Spanning Tree algorithms, and BFS traversal.

AI Disclosure: AI was utilized for code validation suggestions, bitmasking optimization, and edge-case testing logic.


## Bonus Features
[x] Multiple generation algorithms (DFS vs Eller's).

[x] Intelligent "42" pattern connectivity fixer.

[x] Reusable package format (.whl / .tar.gz).





## Instructions

### Installation / Setup
1. Clone the repository:
   ```bash
   git clone <repository_url>-ing

## Run Calls

Run from code folder directly.
Update your requirements on config.txt
and then execute in the following manner
```
python3 a_maze_ing.py config.txt 
```




## Resources
https://www.youtube.com/watch?v=uctN47p_KVk
Eller's Algorithm (https://weblog.jamisbuck.org/2010/12/29/maze-generation-eller-s-algorithm)
