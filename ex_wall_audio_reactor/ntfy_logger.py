import logging
import requests
from threading import Thread
from decouple import config


def _send_post_thread(data):
    requests.post(
        config("NTFY_LOGS_URL"),
        data=data,
        headers={
            "Authorization": f"Bearer {config('NTFY_BEARER_KEY')}"
        })


class NTFYLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)

    def emit(self, record):
        log_entry = self.format(record)
        data = log_entry.encode(encoding='utf-8')
        thread = Thread(target=_send_post_thread, args=(data,), daemon=True)
        thread.start()


def main():
    import time
    logging.basicConfig()
    logger = logging.getLogger("main")
    ntfy_logger = NTFYLogger()
    logger.addHandler(ntfy_logger)
    for i in range(120):
        logger.error(i)
        time.sleep(1)


if __name__ == "__main__":
    main()
