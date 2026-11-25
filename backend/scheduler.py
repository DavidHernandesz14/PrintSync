
import queue
import threading
import time

from backend import database
from backend.printer import Printer


class PrintScheduler:
    def __init__(self, persist=False):
        self.printers = [
            Printer(1, "Printer 1"),
            Printer(2, "Printer 2"),
            Printer(3, "Printer 3"),
        ]

        self.job_queue = queue.PriorityQueue()
        self.job_counter = 0
        self.completed_jobs = []
        self.lock = threading.Lock()
        self.batch_start_time = None
        self.persist = persist

        if self.persist:
            database.initialize_database()
            database.recover_interrupted_jobs()

            for job in database.list_jobs():
                self.job_counter = max(
                    self.job_counter, job["id"]
                )

                if job["status"] == "Queued":
                    self.job_queue.put((
                        job["duration"],
                        job["id"],
                        job["job_name"],
                        time.perf_counter(),
                    ))

                elif job["status"] == "Completed":
                    self.completed_jobs.append({
                        "job_id": job["id"],
                        "job_name": job["job_name"],
                        "printer": job["printer"],
                        "duration": job["duration"],
                        "waiting_time": job["waiting_time"],
                        "turnaround_time": job["turnaround_time"],
                    })

    def add_job(self, job_name, duration):
        if (
            not isinstance(duration, (int, float))
            or duration <= 0
        ):
            raise ValueError("Job duration must be positive.")

        with self.lock:
            if self.persist:
                job_id = database.insert_job(
                    job_name, duration
                )
                self.job_counter = max(
                    self.job_counter, job_id
                )
            else:
                self.job_counter += 1
                job_id = self.job_counter

            self.job_queue.put((
                duration,
                job_id,
                job_name,
                time.perf_counter(),
            ))

        print(f"Added: {job_name} ({duration} seconds)")

    def printer_worker(self, printer):
        while True:
            try:
                duration, job_id, job_name, submitted_at = (
                    self.job_queue.get_nowait()
                )
            except queue.Empty:
                break

            try:
                start_time = time.perf_counter()

                measurement_start = max(
                    submitted_at,
                    self.batch_start_time,
                )

                waiting_time = (
                    start_time - measurement_start
                )

                if self.persist:
                    database.set_printing(
                        job_id, printer.name
                    )

                success = printer.start_print(
                    job_name, duration
                )

                finish_time = time.perf_counter()

                if success:
                    turnaround_time = (
                        finish_time - measurement_start
                    )

                    result = {
                        "job_id": job_id,
                        "job_name": job_name,
                        "printer": printer.name,
                        "duration": duration,
                        "waiting_time": waiting_time,
                        "turnaround_time": turnaround_time,
                    }

                    if self.persist:
                        database.set_completed(
                            job_id,
                            waiting_time,
                            turnaround_time,
                        )

                    with self.lock:
                        self.completed_jobs.append(result)

                elif self.persist:
                    database.set_failed(job_id)

            except Exception:
                if self.persist:
                    database.set_failed(job_id)
                raise

            finally:
                self.job_queue.task_done()

    def run(self):
        print("\nStarting SJF scheduler...\n")

        self.batch_start_time = time.perf_counter()
        threads = []

        for printer in self.printers:
            thread = threading.Thread(
                target=self.printer_worker,
                args=(printer,),
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print("\nAll scheduled jobs completed!")
        self.print_statistics()

    def print_statistics(self):
        if not self.completed_jobs:
            print("No completed jobs.")
            return

        jobs = sorted(
            self.completed_jobs,
            key=lambda job: job["job_id"],
        )

        avg_wait = sum(
            job["waiting_time"] for job in jobs
        ) / len(jobs)

        avg_turnaround = sum(
            job["turnaround_time"] for job in jobs
        ) / len(jobs)

        print("\n--- PrintSync Job Statistics ---")

        for job in jobs:
            print(
                f"{job['job_name']}: "
                f"Wait = {job['waiting_time']:.2f}s, "
                f"Turnaround = "
                f"{job['turnaround_time']:.2f}s"
            )

        print(
            f"\nAverage Waiting Time: {avg_wait:.2f}s"
        )
        print(
            f"Average Turnaround Time: "
            f"{avg_turnaround:.2f}s"
        )


if __name__ == "__main__":
    scheduler = PrintScheduler()

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
