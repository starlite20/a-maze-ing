PYTHON = python3
PIP = pip3
PACKAGE_DIR = .
VENV = .venv
VENV_PYTHON = $(VENV)/bin/$(PYTHON)
VENV_PIP = $(VENV)/bin/pip
MAIN = a_maze_ing.py
CONFIG = config.txt


all: install

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install flake8 mypy build
# 	$(VENV_PIP) install -r requirements.txt
	@echo "Dependencies installed in $(VENV)."

run:
	$(VENV_PYTHON) $(MAIN) $(CONFIG)

debug:
	$(VENV_PYTHON) -m pdb $(MAIN) $(CONFIG)

clean:
	rm -rf .mypy_cache .pytest_cache build dist *.egg-info
	rm -f output_maze.txt history.json
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Cleaned up temporary files."

fclean: clean
	rm -rf $(VENV)
	@echo "Removed virtual environment."

lint: install
	$(VENV_PYTHON) -m flake8 .
	$(VENV_PYTHON) -m mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: install
	$(VENV_PYTHON) -m flake8 .
	$(VENV_PYTHON) -m mypy . --strict

package:
	$(VENV_PYTHON) -m build

.PHONY: all venv install run debug clean fclean lint lint-strict package