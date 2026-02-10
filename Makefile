# GeekCode Makefile
# Build and distribute filesystem-driven AI agent

.PHONY: all build install clean test dist release

VERSION := $(shell grep 'version = ' pyproject.toml | head -1 | cut -d'"' -f2)
PLATFORM := $(shell uname -s | tr '[:upper:]' '[:lower:]')
ARCH := $(shell uname -m)

# Default target
all: build

# Build standalone binary using PyInstaller
build:
	@echo "Building GeekCode $(VERSION) for $(PLATFORM)-$(ARCH)..."
	pip install pyinstaller
	pyinstaller --onefile \
		--name geekcode \
		--add-data "geekcode:geekcode" \
		--hidden-import=tiktoken_ext.openai_public \
		--hidden-import=tiktoken_ext \
		geekcode/cli/main.py
	@echo "Binary created: dist/geekcode"

# Install to system (requires sudo on Unix)
install: build
	@echo "Installing geekcode..."
ifeq ($(PLATFORM),darwin)
	sudo cp dist/geekcode /usr/local/bin/
	sudo chmod +x /usr/local/bin/geekcode
else ifeq ($(PLATFORM),linux)
	sudo cp dist/geekcode /usr/local/bin/
	sudo chmod +x /usr/local/bin/geekcode
else
	@echo "On Windows, copy dist/geekcode.exe to a directory in your PATH"
endif
	@echo "Installed! Run 'geekcode --version' to verify."

# Install for development (editable)
dev:
	pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
coverage:
	pytest tests/ -v --cov=geekcode --cov-report=html

# Lint and format
lint:
	ruff check geekcode tests
	mypy geekcode

format:
	black geekcode tests
	isort geekcode tests

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	rm -f *.spec
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Create distribution packages
dist: clean
	@echo "Creating distribution packages..."
	pip install build
	python -m build

# Create release artifacts for all platforms
release: clean
	@echo "Creating release $(VERSION)..."
	mkdir -p releases/$(VERSION)

	# Build for current platform
	$(MAKE) build
	cp dist/geekcode releases/$(VERSION)/geekcode-$(VERSION)-$(PLATFORM)-$(ARCH)

	# Create tarball
	tar -czf releases/$(VERSION)/geekcode-$(VERSION)-$(PLATFORM)-$(ARCH).tar.gz \
		-C dist geekcode

	# Create SHA256
	cd releases/$(VERSION) && shasum -a 256 *.tar.gz > checksums.txt

	@echo "Release artifacts created in releases/$(VERSION)/"

# Homebrew formula generation
homebrew:
	@echo "Generating Homebrew formula..."
	@cp Formula/geekcode.rb geekcode.rb
	@HASH=$$(shasum -a 256 dist/geekcode-$(VERSION).tar.gz | cut -d' ' -f1) && \
		sed -i '' "s/REPLACE_WITH_SHA256_OF_RELEASE_TARBALL/$$HASH/" geekcode.rb
	@echo "Formula created: geekcode.rb"

# Uninstall from system
uninstall:
	@echo "Uninstalling geekcode..."
	brew uninstall geekcode 2>/dev/null || sudo rm -f /usr/local/bin/geekcode
	brew untap sur950/geekcode 2>/dev/null || true
	rm -rf ~/.geekcode
	@echo "Uninstalled."

# Quick run (for development)
run:
	python -m geekcode.cli.main $(ARGS)

# Help
help:
	@echo "GeekCode Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  build      Build standalone binary"
	@echo "  install    Install binary to /usr/local/bin"
	@echo "  dev        Install for development (editable)"
	@echo "  test       Run tests"
	@echo "  coverage   Run tests with coverage"
	@echo "  lint       Run linters"
	@echo "  format     Format code"
	@echo "  clean      Clean build artifacts"
	@echo "  dist       Create Python distribution packages"
	@echo "  release    Create release artifacts"
	@echo "  homebrew   Generate Homebrew formula"
	@echo "  help       Show this help"
