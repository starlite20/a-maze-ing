# Maze Cell
Each cell can have a max value of 15. This is a combination of 2^3 + 2^2 + 2^1 + 2^0.
	0 = North
	1 = East
	2 = South
	3 = West

If a wall exists, that directional value raised to the power for 2, gets added.

# Perfect Maze
All parts of the maze are accessible, while having 1 path from entry to exit.
Perfect Mazes are a form of Spanning tree with N-1 edges.

# Maze Generation Logic
We will be carving pathway out of a fully walled maze. 
To achieve maze generation, we have the following algorithms.
- Depth First Search. 
	Goes through each cell, picks a random unvisited neighbour cell, and moves to it, and loops.
	If it gets stuck, where there are no unvisited neighbour cells for current position, it retraces back to previous node and checks if there are any. Retracing backwards occurs until it finds an unvisited neighbour cell, and continues depth wise search once again.

- Hunt and Kill 
	This algorithm will go through each cell, picks a random unvisited neighbour cell, and moves to it, and loops.
	If it gets stuck, where there are no unvisited neighbour cells for current position, it will goto the top left node, and start checking each node to see if it finds any cell which has a unvisited neighbour, and proceeds from that until it gets stuck again.
	This is resource intensive as it keeps repeating checks for all nodes continuously.


# Perfect Maze Generation
DFS is the best fit, as it guarantees the perfect maze path, and also bydefault ensures that no corridors are larger or equal to 3x3 at any chance.


# Imperfect Maze Generation
We run perfect maze generation first, and then iteratively remove a few walls and continuously ensure this doesnt create a larger corridor by chance.

# Corridor Conditioning
Corridor / Open Spaces must not reach 3x3 at any point.
Here is a sample corridor of 3x3.
913
802
C46

Based on the algorithm I have set, it will go through each cell from top left to bottom right.
We check the cells ignoring the last row and column, to have a controlled imperfect maze generation.

We check using the 3x3 open check function.
Initially we verify if the neighbouring cells are hitting bounds, or if any of them have a RIGHT or BOTTOM wall.
We verify walls using bit wise operation.
This would mean that the 3x3 is not possible to form.

if so far its all good, we return True stating that 3x3 open area is found.




# Maze Generation
We are using the DFS algorithm in a iterative manner, rather than a recursive approach. This is to ensure that we dont hit limits of recursion in Python. 

## Embedding the 42 Logo
The approach is simple. We set up the pattern map in a 2D List, and use this as the reference to block the cells that are needed for the pattern to be achieved. This logo embedding into the maze will be run prior to wall carving using any of the algorithms. So the moment we create a blank grid, we block the cells we need for the pattern. Following which, we add an additional condition check to verify if the cell is blocked for a pattern or not, before removing any wall.


# Maze Solving
## BFS
We traverse from the entry point cell, by collection all unvisited neigbours which have a direct path, and move towards it. As BFS requires first in, first out, we use a Queue Data Structure Pattern to achieve this. The moment we identify the exit point, we stop traversing, and begin retracing the path towards the entry, and note the path how it reached here.


# Visual Representation
We have set up a basic ASCII terminal reporesentation of the maze. It shows the walls, the open pathways and the entry and exit point. 

## Minilibx
Inorder to use the Minilibx functionality, we will need to install the mlx library provided from the subject. 
This is because, minilibx is originally a C Program. Inorder to work with Python here, the installed package will work as a wrapper to help acheive this.

Install within virtual environment



# Configuration
```
# Essential Environment Variables
WIDTH = <width of the grid>
HEIGHT = <height of the grid>
ENTRY = <coordinate of start point>
EXIT = <coordinate of end point>
OUTPUT_FILE = <output file name>
PERFECT = <boolean  to state if the maze should be perfect or not>


#optional parameters
INTERACTIVE_MODE = <boolean to state if you want the interactive mode on>
SEED = <randomness seed value>
ALGORITHM = <algorithm to be used for the maze generation>
DISPLAY_MODE = <display mode either ascii or mlx>
PATTERN_42 = <boolean to state if you want 42 pattern within the maze>
```


# I moved the output_validator.py inside to be at the same dir with output_mzae.txt
according to the output_validator.py comment