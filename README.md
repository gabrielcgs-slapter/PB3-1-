# Plataforma Brasil Update Notifier

## Description

This script automates the process of checking for updates on the Plataforma Brasil website for specific research projects (CAAEs). It logs into the platform, extracts information about designated CAAEs, compares this information with data from the previous run, and sends an email notification if any changes or new entries are detected. The script is designed to handle credentials securely using environment variables and provides structured logging for monitoring and troubleshooting.

## Features

*   **Automated Login**: Securely logs into Plataforma Brasil using credentials stored in an environment file.
*   **CAAE Data Extraction**: Navigates the platform to find and extract details for a predefined set of CAAEs (currently filtered by those containing '5262').
*   **Change Detection**: Compares the extracted data for each CAAE against the data from the previous run, identifying new studies or changes in existing ones.
*   **Email Notifications**: Sends a detailed HTML email to a specified recipient if updates are found. The email includes information about the changed/new studies.
*   **Secure Credential Handling**: Uses a `.env` file to store sensitive information (login credentials, email passwords), which is excluded from version control.
*   **Structured Logging**: Outputs logs to both the console and a `registro.txt` file, with timestamps, log levels, and informative messages.
*   **Automated WebDriver Management**: Uses `webdriver-manager` to automatically download and manage the correct version of `chromedriver`.
*   **Unit Tested**: Core data comparison logic is unit tested using `pytest`.

## Prerequisites

*   **Python 3.x**: Python 3.8 or higher is recommended.
*   **Google Chrome**: The script uses Google Chrome browser for web automation. Ensure it is installed on the system where the script will run.
*   **`chromedriver`**: Handled automatically by the `webdriver-manager` library. No manual installation is typically required.

## Setup & Configuration

1.  **Clone the Repository / Obtain Files**:
    If you have a Git repository:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
    Otherwise, ensure you have `PB3.py`, `requirements.txt`, and other necessary files in a local directory.

2.  **Install Dependencies**:
    Navigate to the project directory in your terminal and run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up the `.env` File**:
    The `.env` file is crucial for storing sensitive credentials and configuration details securely. It should **never** be committed to version control (it's included in `.gitignore`).

    *   Create a file named `.env` in the root directory of the project.
    *   Add the following environment variables to the file, replacing the placeholder values with your actual information:

        ```dotenv
        DESTINATARIO_EMAIL=your_recipient_email@example.com
        PB_LOGIN=your_plataforma_brasil_login_email
        PB_SENHA=your_plataforma_brasil_password
        EMAIL_PASSWORD=your_gmail_app_password_for_sender_email
        ```

    *   **Variable Explanations**:
        *   `DESTINATARIO_EMAIL`: The email address where update notifications will be sent.
        *   `PB_LOGIN`: Your email/login for Plataforma Brasil.
        *   `PB_SENHA`: Your password for Plataforma Brasil.
        *   `EMAIL_PASSWORD`: The password for the email account used to send notifications (e.g., `regulatorios.aids@gmail.com` as currently hardcoded in the script).
            *   **Important for Gmail**: If using a Gmail account for sending notifications and 2-Factor Authentication (2FA) is enabled, you **must** generate an "App Password" for this script. Do not use your regular Gmail password directly. Search for "Sign in with App Passwords" on Google Account help for instructions.

## Running the Script

To execute the script, navigate to the project directory in your terminal and run:

```bash
python PB3.py
```

The script will perform its operations, and if updates are found, an email will be sent to the configured `DESTINATARIO_EMAIL`.

## Logging

The script provides logging to both the console and a file named `registro.txt` located in the project's root directory.

*   **Console Output**: Provides real-time information about the script's progress and significant events (e.g., login attempts, CAAE processing, email sending status).
*   **`registro.txt` File**: Contains more detailed logs, including timestamps, log levels (INFO, WARNING, ERROR, CRITICAL), the module and function where the log originated, and the log message. This file is useful for troubleshooting and historical tracking. The file is appended to with each run.

Log Format (in `registro.txt`): `YYYY-MM-DD HH:MM:SS,ms - LEVELNAME - module.funcName - Message`

## Running Tests

The project includes unit tests for the core data comparison logic. To run these tests:

1.  Ensure `pytest` is installed (it's included in `requirements.txt`).
2.  Navigate to the root directory of the project in your terminal.
3.  Run the following command:

    ```bash
    pytest
    ```
    Or, if `pytest` is not directly in your PATH:
    ```bash
    python -m pytest
    ```

The tests will execute and report their status (pass/fail).

## Troubleshooting

*   **Missing Environment Variables**: If the script exits with a "CRITICAL" error message about missing environment variables, ensure your `.env` file is correctly set up in the root directory and contains all required variables.
*   **Login Failures**:
    *   Double-check your `PB_LOGIN` and `PB_SENHA` in the `.env` file.
    *   Plataforma Brasil might have changed its login page structure. If so, Selenium selectors in `PB3.py` might need updating.
*   **Email Sending Failures (`SMTPAuthenticationError`)**:
    *   Verify the `EMAIL_PASSWORD` in your `.env` file.
    *   If using Gmail, ensure you are using an App Password if 2FA is enabled.
    *   Check if the sender email account has any security alerts or blocks for "less secure app access" (though App Passwords should bypass this).
*   **`WebDriverException` or Chrome/Chromedriver Issues**:
    *   Although `webdriver-manager` handles `chromedriver` versions, ensure Google Chrome browser is installed and up-to-date.
    *   Rarely, network issues or security software might interfere with `webdriver-manager` downloading `chromedriver`.
*   **CAAEs Not Found / Incorrect Data**:
    *   The script currently filters for CAAEs containing '5262'. This might need adjustment if your target CAAEs have different identifiers.
    *   The Selenium selectors used to extract data from Plataforma Brasil pages are subject to break if the website's HTML structure changes significantly. These would need to be updated in `PB3.py`.

## Project Structure

*   `PB3.py`: The main Python script that performs all operations.
*   `requirements.txt`: Lists all Python package dependencies.
*   `.env` (you create this): Stores sensitive credentials and configuration.
*   `registro.txt`: Log file where detailed execution logs are stored.
*   `new.csv` / `old.csv`: CSV files used by the script to store data from current and previous runs for comparison.
*   `test_pb_logic.py`: Contains unit tests for the data comparison logic.
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore (like `.env`, `__pycache__`).
