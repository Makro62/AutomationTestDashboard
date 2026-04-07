# Run automation tests
# Usage: make test, make clean, make all

.PHONY: test clean all report

test:
	robot --outputdir results tests/

clean:
	rm -rf results/*

all: clean test report

report:
	@echo "Test results are available in results/ folder"
