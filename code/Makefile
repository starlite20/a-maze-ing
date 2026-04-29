all: install run

install:
    pip install -e .

run:
    python3 a_maze_ing.py config.txt

clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name .mypy_cache -exec rm -rf {} +

lint:
    flake8 .
    mypy . --ignore-missing-imports --disallow-untyped-defs

.PHONY: all install run clean lint