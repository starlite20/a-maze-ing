
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



# Maze Generation
We are using the DFS algorithm in a iterative manner, rather than a recursive approach. This is to ensure that we dont hit limits of recursion in Python. 


# Visual Representation
We have set up a basic ASCII terminal reporesentation of the maze. It shows the walls, the open pathways and the entry and exit point. 

## Minilibx
Inorder to use the Minilibx functionality, we will need to install the mlx library provided from the subject. 
This is because, minilibx is originally a C Program. Inorder to work with Python here, the installed package will work as a wrapper to help acheive this.

Install within virtual environment
