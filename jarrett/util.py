from queue import Queue
from threading import Thread


def thread_task(_func, _items, num_workers=10, **kwargs):
    def worker():
        while True:
            item = q.get()
            if item is None:
                break
            _func(item, **kwargs)
            q.task_done()

    q = Queue()
    threads = []
    for w in range(num_workers):
        t = Thread(target=worker)
        t.start()
        threads.append(t)

    for i in _items:
        q.put(i)

    for w in range(num_workers):
        t = Thread(target=worker)
        t.start()
        threads.append(t)