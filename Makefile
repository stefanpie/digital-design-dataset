# Makefile to clean up development artifacts

# Directories and files to clean
CLEAN_ITEMS := \
    **/__pycache__ \
    .mypy_cache \
    .ruff_cache \
    .pytest_cache \
    .coverage \
    htmlcov \
    **/.ipynb_checkpoints \


# Default target
clean:
	@echo "Cleaning up development artifacts..."
	@for item in $(CLEAN_ITEMS); do \
		echo "Removing $$item"; \
		rm -rf $$item; \
	done
	@echo "Cleanup complete."

.PHONY: clean

clean-pycache:
	@echo "Cleaning up __pycache__ directories..."
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@echo "Cleanup complete."

.PHONY: clean-pycache