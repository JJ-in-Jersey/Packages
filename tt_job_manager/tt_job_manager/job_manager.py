from tt_singleton.singleton import Singleton
from tt_semaphore import simple_semaphore as semaphore
from tt_date_time_tools.date_time_tools import mins_secs
from multiprocessing import Manager, Pool, cpu_count, Process
from time import sleep, perf_counter


class JobManager(metaclass=Singleton):

    def put(self, job):
        self.queue.put(job)
        return job.result_key

    def get(self, key):
        return self.results_lookup[key]

    def wait(self):
        self.queue.join()

    @staticmethod
    def stop_queue():
        semaphore.off('QueueManager')

    def __init__(self, pool_size=None):
        self.manager = Manager()
        self.queue = self.manager.JoinableQueue()
        self.results_lookup = self.manager.dict()
        self.qm = WaitForProcess(target=QueueManager, name='QueueManager', args=(self.queue, self.results_lookup, pool_size,))
        self.qm.start()


class QueueManager:

    def __init__(self, q, lookup, size):
        print(f'+     queue manager (Pool size = {cpu_count()})\n', flush=True)
        semaphore.on(self.__class__.__name__)
        results = {}
        with Pool(size) as p:
            while semaphore.is_on(self.__class__.__name__):
                # pull submitted jobs and start them in the pool
                while not q.empty():
                    job = q.get()
                    results[job] = p.apply_async(job.execute, callback=job.execute_callback, error_callback=job.error_callback)

                # check results for complete job and put them on external lookup
                jobs = list(results.keys())
                for job in jobs:
                    if results[job].ready():
                        result = results[job].get()
                        lookup[result[0]] = result[1]  # results format is tuple of (key, data, init time)
                        q.task_done()
                        del results[job]
                sleep(0.01)
        print(f'-     queue manager\n', flush=True)


class WaitForProcess(Process, metaclass=Singleton):

    def start(self, **kwargs):
        semaphore_file_name = Process.__getattribute__(self, 'name')
        if semaphore.is_on(semaphore_file_name):
            semaphore.off(semaphore_file_name)
        # noinspection PyArgumentList
        super().start(**kwargs)
        while not semaphore.is_on(semaphore_file_name):
            sleep(0.1)


class Job:

    def execute(self):
        init_time = perf_counter()
        print(f'+     {self.job_name}', flush=True)
        return tuple([self.result_key, self.execute_function(*self.execute_function_arguments), mins_secs(perf_counter()-init_time)])

    def execute_callback(self, result):
        print(f'-     {self.job_name} {result[2]} minutes', flush=True)

    def error_callback(self, result):
        print(f'!     {self.job_name} process has raised an error {result}', flush=True)

    def __init__(self, job_name, result_key, function, arguments):
        self.job_name = job_name
        self.result_key = result_key
        self.execute_function = function
        self.execute_function_arguments = arguments
