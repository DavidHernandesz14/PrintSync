
import sqlite3
from pathlib import Path


# Location of the SQLite database
DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "printsync.db"
)


def connect():
    connection = sqlite3.connect(
        DB_PATH,
        timeout=10
    )

    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the jobs table if it does not exist."""

    with connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                duration REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Queued',
                printer TEXT,
                waiting_time REAL,
                turnaround_time REAL
            )
        """)


def recover_interrupted_jobs():
    """Return interrupted printing jobs to the queue."""

    with connect() as connection:
        connection.execute("""
            UPDATE jobs
            SET status = 'Queued',
                printer = NULL
            WHERE status = 'Printing'
        """)


def list_jobs():
    """Retrieve all jobs from the database."""

    with connect() as connection:
        rows = connection.execute("""
            SELECT *
            FROM jobs
            ORDER BY id
        """).fetchall()

        return [dict(row) for row in rows]


def insert_job(job_name, duration):
    """Save a new print job."""

    with connect() as connection:
        cursor = connection.execute("""
            INSERT INTO jobs (
                job_name,
                duration,
                status
            )
            VALUES (?, ?, 'Queued')
        """, (job_name, duration))

        return cursor.lastrowid


def set_printing(job_id, printer):
    """Mark a job as currently printing."""

    with connect() as connection:
        connection.execute("""
            UPDATE jobs
            SET status = 'Printing',
                printer = ?
            WHERE id = ?
        """, (printer, job_id))


def set_completed(
    job_id,
    waiting_time,
    turnaround_time
):
    """Save the results of a completed print job."""

    with connect() as connection:
        connection.execute("""
            UPDATE jobs
            SET status = 'Completed',
                waiting_time = ?,
                turnaround_time = ?
            WHERE id = ?
        """, (
            waiting_time,
            turnaround_time,
            job_id
        ))


def set_failed(job_id):
    """Mark an unsuccessful print job as failed."""

    with connect() as connection:
        connection.execute("""
            UPDATE jobs
            SET status = 'Failed'
            WHERE id = ?
        """, (job_id,))
