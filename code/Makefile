PYTHON = python3
PIP = pip3
MAIN = a_maze_ing.py
CONFIG = config.txt
PACKAGE_DIR = .
VENV = venv
BIN = $(VENV)/bin


all: install lint

install:
	$(PIP) install --upgrade pip
	$(PIP) install flake8 mypy
	
run:
	$(PYTHON) $(MAIN) $(CONFIG)


debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	rm -rf __pycache__
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Cleaned up temporary files."


lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy .


lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict


package:
	$(PYTHON) -m build

.PHONY: all install run debug clean lint lint-strict package