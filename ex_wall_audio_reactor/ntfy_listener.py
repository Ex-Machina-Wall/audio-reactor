import requests
import threading
import time
import queue
import json
import logging
from decouple import config


class NTFYListener:

    def __init__(self):
        self.logger = logging.getLogger("NTFYListener")
        self.queue = queue.Queue()
        self._stop_thread = False
        self.thread = threading.Thread(target=self._add_to_queue_periodically)

    def _add_to_queue_periodically(self):
        resp = requests.get(
            config("NTFY_SERVER"),
            stream=True,
            headers={"Authorization": f"Bearer {config('NTFY_BEARER_KEY')}"}
            )
        try:
            for line in resp.iter_lines():
                if self._stop_thread:
                    raise StopIteration()
                if line:
                    message = json.loads(str(line)[2:-1])
                    if message['event'] == "message":
                        self.queue.put(message['message'])
                        # self.logger.debug(message)
        except StopIteration:
            pass

    def start_thread(self):
        self.thread.start()

    def stop_thread(self):
        self._stop_thread = True
        self.thread.join()

    def get_queue(self):
        items = list()
        while not self.queue.empty():
            items.append(self.queue.get())
        return items


def main():
    queue_manager = NTFYListener()
    queue_manager.start_thread()

    try:
        while True:
            queue_manager.check_queue()
            time.sleep(1)  # Check the queue every 2 seconds
    except KeyboardInterrupt:
        queue_manager.stop_thread()


if __name__ == "__main__":
    main()
