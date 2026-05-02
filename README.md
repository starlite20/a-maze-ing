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
## Instructions

### Installation and Setup
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd a-maze-ing

    (Optional) Setup a virtual environment:
    Bash

    python3 -m venv venv
    source venv/bin/activate

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```


### Execution

The program is executed by passing a configuration file as a command-line argument. Run the following from the code folder:
Bash
```
python3 a_maze_ing.py config.txt
```

## Configuration File Structure
The configuration file follows a KEY=VALUE format. All parameters must be defined.

| Key          | Description                              | Example              |
|--------------|------------------------------------------|----------------------|
| WIDTH        | Maze width (cells)                       | WIDTH=20             |
| HEIGHT       | Maze height (cells)                      | HEIGHT=15            |
| ENTRY        | Entry coordinates (x,y)                  | ENTRY=0,0            |
| EXIT         | Exit coordinates (x,y)                   | EXIT=19,14           |
| OUTPUT_FILE  | Output filename                          | OUTPUT_FILE=maze.txt |
| PERFECT      | Perfect maze toggle (True/False)         | PERFECT=True         |
| ALGORITHM    | Generation algorithm (DFS / ELLER)       | ALGORITHM=DFS        |
| SEED         | Random seed for reproducibility          | SEED=42              |
| PATTERN_42   | Enable “42” pattern embedding            | PATTERN_42=True      |

---

## Maze Generation Algorithm

### Implemented Algorithms

- Depth-First Search (DFS)  
  A backtracking algorithm that produces long, winding paths and guarantees a perfect maze when enabled.

- Eller’s Algorithm  
  A row-by-row algorithm optimized for memory usage, capable of generating large mazes efficiently.

### Why These Algorithms

DFS was selected for its simplicity and ability to generate complex mazes with a single valid path. It is well-suited for validating solver correctness.

Eller’s Algorithm was chosen for its memory efficiency. Since it only maintains state for the current and previous rows, it allows scalable maze generation with O(N) space complexity, making it suitable for large inputs.

---

## Technical Choices and Reusability

The core logic is encapsulated in the `MazeGenerator` class within `mazegen.py`. This module is independent and reusable in other Python projects.

Example usage:
```
python
from mazegen import MazeGenerator

maze = MazeGenerator(width=20, height=15, entry_pos=(0, 0), exit_pos=(19, 14))
maze.generate_maze(algorithm="DFS")
path = maze.solve_maze()
```

Reusable components include:
- Maze generation engine
- BFS solver logic
- Configuration-driven execution pipeline

---

## Advanced Features
- Pattern embedding with connectivity validation to preserve solvability
- Constraint system to prevent large open spaces
- Hexadecimal export format for compatibility with external tools
- Generation history tracking for animation playback

---

## Bonus Features
- Multiple generation algorithms (DFS and Eller’s)
- “42” pattern connectivity handling
- Reusable package distribution (.whl / .tar.gz)

---

## Team and Project Management

### Team Roles
- ssujaude  
  DFS implementation, BFS solver, pattern connectivity logic, animation system

- sobied  
  Eller’s algorithm implementation, memory optimization, unit testing

- Shared Responsibilities  
  Core architecture design, MazeGenerator class development, packaging

### Planning and Evolution
The project was developed through iterative sprints. Initial work focused on building the DFS-based generator and core class structure. As the project progressed, Eller’s Algorithm was introduced to address scalability concerns.

Midway through development, adjustments were made to integrate row-based logic with existing optimizations. The design evolved to ensure compatibility between different generation strategies and shared infrastructure.

### Retrospective
- What worked well  
  Modular design enabled parallel development with minimal conflicts.

- What could be improved  
  Pattern embedding initially introduced disconnected regions. Earlier validation design would have reduced rework.

### Tools Used
- Git and GitHub for version control
- Python virtual environments for dependency management
- Unit testing for validation
- Collaborative planning through iterative development

---

## Resources
- Eller’s Algorithm by Jamis Buck  (https://weblog.jamisbuck.org/2010/12/29/maze-generation-eller-s-algorithm)

- Computerphile Maze Generation Video (https://www.youtube.com/watch?v=uctN47p_KVk)

- Graph Theory concepts: spanning trees and traversal algorithms

---

## AI Usage Disclosure
AI was used in the following areas:
- Assistance in refining documentation

---
