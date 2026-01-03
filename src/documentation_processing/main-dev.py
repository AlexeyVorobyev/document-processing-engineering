import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, command) -> None:
        self.command = command
        self.process = None
        self.restart_program()

    def restart_program(self) -> None:
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                print("Forcefully killing process...")
                self.process.kill()
        print("Starting new process...")
        self.process = subprocess.Popen(self.command, shell=False) # type: ignore

    def on_modified(self, event) -> None:
        if event.src_path.endswith(".py"):
            print(f"File {event.src_path} modified, restarting...")
            self.restart_program()


if __name__ == "__main__":
    command = ["python", "-m", "src.documentation_processing.main"]
    event_handler = FileChangeHandler(command)
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    finally:
        if event_handler.process:
            event_handler.process.terminate()
        observer.join()
