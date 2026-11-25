
import time

import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend.printer import Printer
from backend.scheduler import PrintScheduler


@pytest.fixture
def client(monkeypatch):
    # Give each test a fresh scheduler.
    monkeypatch.setattr(main, "scheduler", PrintScheduler())
    monkeypatch.setattr(main, "scheduler_running", False)

    with TestClient(main.app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_submit_print_job(client):
    response = client.post(
        "/jobs",
        json={
            "job_name": "Phone Stand",
            "duration": 10,
        },
    )

    assert response.status_code == 201
    assert response.json()["job_name"] == "Phone Stand"

    status = client.get("/status").json()

    assert len(status["pending_jobs"]) == 1
    assert status["pending_jobs"][0]["duration"] == 10


def test_invalid_job_duration(client):
    response = client.post(
        "/jobs",
        json={
            "job_name": "Invalid Job",
            "duration": -5,
        },
    )

    assert response.status_code == 422


def test_sjf_queue_order(client):
    jobs = [
        ("Long Job", 10),
        ("Short Job", 2),
        ("Medium Job", 5),
    ]

    for name, duration in jobs:
        response = client.post(
            "/jobs",
            json={
                "job_name": name,
                "duration": duration,
            },
        )

        assert response.status_code == 201

    status = client.get("/status").json()

    names = [
        job["job_name"]
        for job in status["pending_jobs"]
    ]

    assert names == [
        "Short Job",
        "Medium Job",
        "Long Job",
    ]


def test_start_scheduler_with_empty_queue(client):
    response = client.post("/scheduler/start")

    assert response.status_code == 400


def test_scheduler_completes_job(client, monkeypatch):
    # Avoid real printing delays during the test.
    def fake_print(self, job_name, duration):
        return True

    monkeypatch.setattr(
        Printer,
        "start_print",
        fake_print,
    )

    response = client.post(
        "/jobs",
        json={
            "job_name": "Test Print",
            "duration": 2,
        },
    )

    assert response.status_code == 201

    response = client.post("/scheduler/start")

    assert response.status_code == 200

    # Wait briefly for the background scheduler.
    deadline = time.monotonic() + 2

    while time.monotonic() < deadline:
        status = client.get("/status").json()

        if (
            not status["scheduler_running"]
            and len(status["completed_jobs"]) == 1
        ):
            break

        time.sleep(0.01)

    assert status["scheduler_running"] is False
    assert len(status["completed_jobs"]) == 1

    completed = status["completed_jobs"][0]

    assert completed["job_name"] == "Test Print"
    assert completed["waiting_time"] >= 0
    assert completed["turnaround_time"] >= 0
