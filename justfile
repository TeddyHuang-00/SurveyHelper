# Lint and format Python code using Ruff
format:
    ruff check --select I,NPY,RUF,UP,F401 --fix .
    ruff format .

# Lint Python code using Ruff
lint:
    ruff check --select I,NPY,RUF,UP,F401 .

# Clear all caches
clear:
    ruff clean