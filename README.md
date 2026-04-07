# AutomationTestDashboard

Here is a website that displays the results of the automation running.

<img width="1437" alt="image" src="https://github.com/user-attachments/assets/3cb4a6aa-0893-444b-a10e-dca8bac0941f" />

## Project Structure

```
/workspace/
├── config/              # Configuration files
│   ├── __init__.py
│   └── settings.ini     # Test configuration settings
├── data/                # Test data files
├── lib/                 # Custom keyword libraries
│   ├── __init__.py
│   └── LoginKeywords.py
├── resources/           # Resource files for tests
├── results/             # Test execution results
├── tests/               # Test cases (Robot Framework)
│   └── LoginWebTest.robot
├── utils/               # Utility functions
│   └── __init__.py
├── Dashboard/           # Dashboard application
│   ├── app.py
│   ├── static/
│   └── templates/
├── .github/             # GitHub configurations
├── .git/
├── history.json         # Test history data
├── Makefile             # Build automation
├── README.md            # This file
└── requirements.txt     # Python dependencies
```

## Prerequisites

- Python 3.8+
- pip (Python package manager)

**Note:** This project uses a mock/simulation mode for testing login functionality due to environment constraints. 
For full browser automation tests with Selenium, ensure you have:
- Google Chrome/Chromium browser installed
- ChromeDriver or use webdriver-manager for automatic driver management

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

### Using Make
```bash
make test          # Run all tests
make clean         # Clean results directory
make all           # Clean, run tests, and show report
```

### Using Robot Framework directly
```bash
robot --outputdir results tests/
```

### Run specific test
```bash
robot --outputdir results tests/LoginWebTest.robot
```

## Test Results

Test results are stored in the `results/` directory after execution:
- `output.xml` - Machine-readable test results
- `log.html` - Detailed execution log
- `report.html` - Test report

## Dashboard

To run the dashboard application:
```bash
cd Dashboard
python app.py
```

The dashboard will be available at `http://localhost:5000`

## Configuration

Edit `config/settings.ini` to customize:
- Browser type
- Headless mode
- Base URL
- Timeout settings

## Adding New Tests

1. Create new test case files in `tests/` directory
2. Add custom keywords in `lib/` if needed
3. Place test data in `data/` directory
4. Update resource files in `resources/` if needed

## CI/CD

This project includes GitHub Actions workflows in `.github/workflows/` for automated testing.
