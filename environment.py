# environment.py

GRID_SIZE = 10

# 0 = empty cell, 1 = obstacle
grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# function to add obstacle
def add_obstacle(x, y):
    grid[x][y] = 1

# function to check if cell is free
def is_free(x, y):
    return grid[x][y] == 0

# (optional) print grid
def show_grid():
    for row in grid:
        print(row)