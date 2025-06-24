# Streamlit App

This project is a Streamlit application designed to manage and display policies and claims data. The application is structured to connect to a SQL Server database for data retrieval.

## Project Structure

```
streamlit-app
├── src
│   ├── app.py          # Main entry point of the Streamlit application
│   └── utils
│       └── db_utils.py # Utility functions for database operations
├── requirements.txt    # Project dependencies
└── README.md           # Documentation for the project
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd streamlit-app
   ```

2. **Install dependencies:**
   Ensure you have Python installed, then run:
   ```
   pip install -r requirements.txt
   ```

3. **Run the application:**
   Execute the following command to start the Streamlit app:
   ```
   streamlit run src/app.py
   ```

## Usage Guidelines

- The application consists of two main tabs:
  - **Policies:** This tab will display a table of policies fetched from the SQL Server database.
  - **Claims:** This tab will display a table of claims, also fetched from the SQL Server database.

- Further functionality will be added to connect to the database and populate the tables with real data.

## Future Enhancements

- Implement database connection and data fetching in `src/utils/db_utils.py`.
- Add error handling and user authentication features.
- Enhance the UI for better user experience.