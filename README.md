
# PrintSync

A full-stack 3D printer management system that simulates multiple printers and automatically schedules print jobs using the Shortest Job First (SJF) algorithm.

## Features

- Three simulated 3D printers operating concurrently
- Non-preemptive Shortest Job First scheduling
- Thread-safe job queue and printer synchronization
- Interactive web dashboard
- Live printer progress updates through API polling
- REST API built with FastAPI
- SQLite database for persistent job storage
- Recovery of interrupted jobs after server restart
- Average waiting-time and turnaround-time statistics
- Automated tests using pytest

## Technologies

- Python
- FastAPI
- SQLite
- JavaScript
- HTML and CSS
- Python threading and PriorityQueue
- pytest
- Git and GitHub

## Scheduling Algorithm

PrintSync uses non-preemptive Shortest Job First (SJF).

Jobs are assigned according to their estimated printing duration. Shorter jobs are selected before longer jobs, and jobs with equal durations retain their submission order.

Three simulated printers process jobs concurrently. When a printer finishes, it takes the shortest remaining job from the queue.

SJF can reduce average waiting time compared with FIFO for certain workloads, although long jobs may experience starvation.

## Performance Metrics

The dashboard displays:

- Average waiting time
- Average turnaround time
- Individual job durations
- Printer assignments
- Completed-job history

Waiting and turnaround times are measured relative to the start of each scheduling batch.

## Installation

Clone the repository:

    git clone https://github.com/DavidHernandesz14/PrintSync.git
    cd PrintSync

Create a virtual environment:

    python -m venv .venv

Activate it on Windows:

    .venv\Scripts\Activate.ps1

Install dependencies:

    python -m pip install -r requirements.txt

## Running PrintSync

Start the FastAPI server:

    python -m uvicorn backend.main:app --reload

Open the dashboard:

    http://127.0.0.1:8000/

API documentation:

    http://127.0.0.1:8000/docs

## Running Tests

Run the automated test suite:

    python -m pytest -v

The initial Version 1.0 test suite contains 14 tests covering scheduling, REST API behavior, and SQLite persistence.

## Project Structure

    PrintSync/
    ├── backend/
    │   ├── main.py
    │   ├── printer.py
    │   ├── scheduler.py
    │   └── database.py
    ├── frontend/
    │   ├── index.html
    │   ├── style.css
    │   └── script.js
    ├── tests/
    │   ├── test_scheduler.py
    │   ├── test_api.py
    │   └── test_persistence.py
    ├── .gitignore
    ├── requirements.txt
    └── README.md

## Limitations

- Printers are simulated; no physical hardware is connected.
- Jobs are submitted in batches.
- The current dashboard uses polling rather than WebSockets.
- The application is designed for local, single-user use.

## Author

David Hernandez

Computer Engineering Student
Cal Poly Pomona
