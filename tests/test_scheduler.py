
import threading

import pytest

from backend.scheduler import PrintScheduler
from backend.printer import Printer


def test_sjf_order(monkeypatch):
    scheduler = PrintScheduler()

    # One printer makes execution order predictable.
    scheduler.printers = [Printer(1, "Test Printer")]

    processed = []

    def fake_print(self, job_name, duration):
        processed.append(job_name)
        return True

    monkeypatch.setattr(Printer, "start_print", fake_print)

    scheduler.add_job("Long Job", 10)
    scheduler.add_job("Short Job", 2)
    scheduler.add_job("Medium Job", 5)

    scheduler.run()

    assert processed == [
        "Short Job",
        "Medium Job",
        "Long Job",
    ]


def test_equal_duration_fifo(monkeypatch):
    scheduler = PrintScheduler()
    scheduler.printers = [Printer(1, "Test Printer")]

    processed = []

    def fake_print(self, job_name, duration):
        processed.append(job_name)
        return True

    monkeypatch.setattr(Printer, "start_print", fake_print)

    scheduler.add_job("First Job", 5)
    scheduler.add_job("Second Job", 5)
    scheduler.add_job("Third Job", 5)

    scheduler.run()

    assert processed == [
        "First Job",
        "Second Job",
        "Third Job",
    ]


def test_invalid_duration():
    scheduler = PrintScheduler()

    with pytest.raises(ValueError):
        scheduler.add_job("Invalid Job", 0)

    with pytest.raises(ValueError):
        scheduler.add_job("Negative Job", -5)


def test_all_jobs_complete(monkeypatch):
    scheduler = PrintScheduler()

    processed = []
    processed_lock = threading.Lock()

    def fake_print(self, job_name, duration):
        with processed_lock:
            processed.append(job_name)
        return True

    monkeypatch.setattr(Printer, "start_print", fake_print)

    jobs = [
        ("Phone Stand", 10),
        ("Gear Assembly", 4),
        ("Miniature House", 15),
        ("Robot Arm", 8),
        ("Keychain", 2),
        ("Cable Holder", 5),
    ]

    for name, duration in jobs:
        scheduler.add_job(name, duration)

    scheduler.run()

    assert len(processed) == 6
    assert len(set(processed)) == 6
    assert len(scheduler.completed_jobs) == 6
    assert scheduler.job_queue.empty()


def test_waiting_and_turnaround_times(monkeypatch):
    scheduler = PrintScheduler()
    scheduler.printers = [Printer(1, "Test Printer")]

    def fake_print(self, job_name, duration):
        return True

    monkeypatch.setattr(Printer, "start_print", fake_print)

    scheduler.add_job("Test Job", 3)

    scheduler.run()

    assert len(scheduler.completed_jobs) == 1

    job = scheduler.completed_jobs[0]

    assert job["waiting_time"] >= 0
    assert job["turnaround_time"] >= 0
    assert job["turnaround_time"] >= job["waiting_time"]
