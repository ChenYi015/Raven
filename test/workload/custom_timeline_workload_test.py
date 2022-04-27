from queue import Queue
from threading import Thread

from benchmark.workload.manager import WorkloadManager


def print_queries(queue: Queue):
    while True:
        query = queue.get()
        print(query)


if __name__ == '__main__':
    workload = WorkloadManager.get_workload('custom', 'timeline')

    queue = Queue()

    generate_thread = Thread(
        target=workload.generate_queries,
        args=(queue,),
        name='QueryGenerator'
    )
    generate_thread.start()

    print_thread = Thread(
        target=print_queries,
        args=(queue,),
        name='QueryPrinter'
    )
    print_thread.start()
