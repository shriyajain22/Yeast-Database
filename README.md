# Yeast Database Web Application

## Overview

The **Yeast Database** is a web-based application that allows users to search and explore yeast-related biological data through an interactive interface.

The system is designed to query a backend database and dynamically display results based on user input. For example, users can search for specific genes (e.g., *NOP1*) and retrieve relevant database entries in real time.

This project demonstrates integration of backend database querying, web development, and data visualization techniques.


## Features

* **Search functionality** for yeast genes/proteins (e.g., NOP1)
* **Dynamic query handling** using URL parameters
* **Asynchronous data loading (AJAX)** for smooth user experience
* **Data visualization support** (charts/plots where applicable)
* **Template-based frontend rendering** using Flask
* **Database-driven backend** for structured biological data


## Biological Context

Yeast (*Saccharomyces cerevisiae*) is widely used as a model organism in biology due to its well-characterized genome and importance in studying cellular processes. It is commonly used in systems biology and genetics research to understand gene function and regulatory networks.


## Project Structure

```bash
Yeast-Database/
│
├── data_tables/        # Yeast dataset files used for querying
├── scripts/            # Backend scripts for data processing
├── static/             # Static assets
│   └── css/            # Styling files
├── templates/          # HTML templates (Flask frontend)
├── yeast_db.py         # Main Flask application
└── README.md
```


## Technologies Used

* **Python (Flask)** – backend web framework
* **MariaDB** – relational database
* **HTML / CSS** – frontend structure and styling
* **JavaScript + AJAX** – dynamic interaction and data fetching
* **Matplotlib / Charts** – data visualization (if applicable)


## How It Works

1. User enters a search query (e.g., `NOP1`)
2. The request is sent to the backend via Flask routes
3. The backend queries the database
4. Results are returned and rendered dynamically in the browser


## Contributors

* Shriya Jain
* Addison Yam
* Tungalan Ganbaatar
* Manish Danda
