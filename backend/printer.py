
import threading
import time


class Printer:
    def __init__(self, printer_id, name):
        self.printer_id = printer_id
        self.name = name
        self.status = "Idle"
        self.progress = 0
        self.current_job = None
        self.lock = threading.Lock()

    def start_print(self, job_name, duration):
        if duration <= 0:
            raise ValueError("Duration must be positive.")

        if not self.lock.acquire(blocking=False):
            print(f"{self.name} is already busy!")
            return False

        try:
            self.status = "Printing"
            self.progress = 0
            self.current_job = job_name

            print(
                f"\n{self.name} started: {job_name} "
                f"({duration} seconds)"
            )

            for step in range(1, 11):
                time.sleep(duration / 10)

                self.progress = step * 10

                print(
                    f"{self.name} - {job_name}: "
                    f"{self.progress}%"
                )

            self.status = "Completed"
            self.current_job = None

            print(f"{self.name} finished: {job_name}\n")
            return True

        finally:
            self.lock.release()


if __name__ == "__main__":
    printer = Printer(1, "Printer 1")
    printer.start_print("Phone Stand", 5)
