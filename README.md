
# FinTracker

FinTracker is a financial tracking application designed to monitor and analyze personal investments, particularly in Real Estate Investment Trusts (REITs). It utilizes Python, Flask, SQLite, and Bootstrap among other technologies.

## Getting Started

These instructions will guide you through setting up and running FinTracker on your local machine.

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3
- Git

### Installation

Follow these steps to get your development environment running:

1. **Clone the repository**
   ```
   git clone https://github.com/titofonseca/FinTracker.git
   ```

2. **Navigate to the project directory**
   ```
   cd FinTracker
   ```

3. **Create and Activate Virtual Environment (optional)**
   ```
   python -m venv fintracker_env
   source fintracker_env/bin/activate
   ```
   On Windows, activation is slightly different:
   ```
   fintracker_env\Scripts\activate
   ```

4. **Install required packages**
   ```
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   Copy `.env.example` to a new file named `.env` and fill in the necessary API key.
   ```
   cp .env.example .env
   ```

6. **Initialize the database**
   The application will automatically set up the database upon the first run.

### Running the Application

To run the application, use the following command in the project root directory:
```
python app/app.py
```
The Flask server will start, and the application will be accessible at `http://localhost:5000` by default.

### Usage

Once the application is running, navigate to `http://localhost:5000` in your web browser. You can start tracking your financial data by entering it into the application.

### Updating Database Tables

Database tables can be updated via the user interface in the application. The application provides a feature to refresh all tables with the latest data.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

- This project was created as part of a personal investment tracking initiative.
- Special thanks to all contributors and users of the FinTracker.
