# 🚌 Dhaka Bus Route Finder

This is a simple web application built with Flask that helps users find bus routes in Dhaka, Bangladesh. Users can select a starting point and a destination to find direct routes or routes with transfers, based on their preferred criteria.

## ✨ Features

*   Find direct bus routes between two locations.
*   Find routes with transfers.
*   Option to find the fastest route, route with the least transfers, or shortest route (based on number of stops).
*   Interactive location selection using a modal with search functionality.
*   Multilingual support (English and Bengali) using Flask sessions for language persistence.

## 🚀 Technologies Used

*   **Backend:** Python (Flask)
*   **Frontend:** HTML, CSS, JavaScript
*   **Data:** JSON (for bus data), JavaScript array (for locations)

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

*   Python 3.6 or higher
*   pip (Python package installer)

## 🛠️ Setup and Installation

1.  **Clone the repository** (if applicable): 
    ```bash
    # Replace with your repository URL if available
    # git clone <repository_url>
    # cd <project_directory>
    ```
    If you downloaded the project files directly, navigate to the project directory in your terminal.

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ensure data files are present:**
    Make sure `bus_data.json` and `static/places.js` are in the correct locations within the project directory.

## ▶️ Running the Application

1.  **Navigate to the project directory** in your terminal.

2.  **Run the Flask application:**
    ```bash
    python app.py
    ```

3.  **Access the application:**
    Open your web browser and go to `http://127.0.0.1:5000/` (or the address shown in the terminal output).

    *Note: The Flask development server is suitable for local testing. For production deployment, consider using a production-ready WSGI server like Gunicorn.*

## 📁 Project Structure

```
.
├── app.py             # Flask application main file
├── bus_data.json      # Data file containing bus routes
├── requirements.txt   # List of Python dependencies
├── static/
│   └── places.js      # JavaScript file containing the list of locations
├── templates/
│   └── index.html     # HTML template for the main page
└── translations.py    # Python file for language translations
```

## 🌐 Usage

1.  Open the application in your web browser.
2.  Select your **Starting Point** and **Destination** by clicking on the input fields and choosing from the list in the modal.
3.  Optionally, select your preferred **Route Preference**.
4.  Click the "Find Routes" button.
5.  The results section will display direct routes and/or a suggested route with transfers, along with instructions.

## Contributing

If you'd like to contribute to this project, please feel free to fork the repository and submit a pull request.

## License

This project is open source and available under the [Specify your license here, e.g., MIT License].

---

*Built with ❤️ and Flask* 