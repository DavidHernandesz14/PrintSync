
from backend import database
from backend.printer import Printer
from backend.scheduler import PrintScheduler


def test_queued_jobs_survive_restart(tmp_path, monkeypatch):
    # Use a temporary database to protect personal data.
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "printsync.db",
    )

    scheduler = PrintScheduler(persist=True)

    scheduler.add_job("Long Job", 10)
    scheduler.add_job("Short Job", 2)

    # Simulate restarting the application.
    restarted = PrintScheduler(persist=True)

    jobs = sorted(list(restarted.job_queue.queue))

    assert [job[2] for job in jobs] == [
        "Short Job",
        "Long Job",
    ]


def test_completed_jobs_survive_restart(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "printsync.db",
    )

    scheduler = PrintScheduler(persist=True)

    # Skip printing delays during automated tests.
    monkeypatch.setattr(
        Printer,
        "start_print",
        lambda self, name, duration: True,
    )

    scheduler.add_job("Test Print", 2)
    scheduler.run()

    # Create another scheduler to simulate a restart.
    restarted = PrintScheduler(persist=True)

    assert len(restarted.completed_jobs) == 1
    assert (
        restarted.completed_jobs[0]["job_name"]
        == "Test Print"
    )
    assert restarted.job_queue.empty()


def test_interrupted_job_recovers_as_queued(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "printsync.db",
    )

    scheduler = PrintScheduler(persist=True)

    scheduler.add_job("Interrupted Print", 3)

    # Simulate a job interrupted during printing.
    database.set_printing(1, "Printer 1")

    restarted = PrintScheduler(persist=True)

    assert restarted.job_queue.qsize() == 1

    assert (
        database.list_jobs()[0]["status"]
        == "Queued"
    )
