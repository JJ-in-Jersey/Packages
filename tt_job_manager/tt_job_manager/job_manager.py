from tt_singleton.singleton import Singleton
from tt_semaphore import simple_semaphore as semaphore
from multiprocessing import Manager, Pool, cpu_count, Process, JoinableQueue
from time import sleep
import psutil
import platform

class JobManager(metaclass=Singleton):

    _worker_counter = None
    _worker_lock = None

    def init_worker(worker_lock, worker_counter):
        """Called once when each worker process starts"""
        with worker_lock:
            worker_id = worker_counter.value
            worker_counter.value += 1

        # Pinning required to use all cores on Windows
        if platform.system() == 'Windows':
                p = psutil.Process()
                p.cpu_affinity([worker_id])
                # print(f'Worker {worker_id} pinned to core {worker_id}', flush=True)

    @property
    def queue(self):
        return self._queue

    def submit_job(self, job):
        self._queue.put(job)
        return job.result_key

    def get_result(self, key):
        return self._results_key_dict.pop(key)

    def wait(self):
        self._queue.join()

    @staticmethod
    def stop_queue():
        semaphore.off('QueueManager')

    def __init__(self, pool_size=cpu_count()):
        print(f'\nStarting multiprocess job manager')

        self._manager = Manager()
        self._queue = JoinableQueue()
        self._results_key_dict = self._manager.dict()

        # Initialize worker counter and lock
        JobManager._worker_counter = self._manager.Value('i', 0)
        JobManager._worker_lock = self._manager.Lock()

        self.qm = WaitForProcess(
            target=QueueManager,
            name='QueueManager',
            args=(self._queue, self._results_key_dict, pool_size,
                  JobManager._worker_lock, JobManager._worker_counter)
        )
        self.qm.start()

class QueueManager:

    def __init__(self, q, results_dict, size, worker_lock, worker_counter):
        print(f'+     queue manager (Pool size = {size})\n', flush=True)
        semaphore.on(self.__class__.__name__)
        job_key_dict = {}

        # Pass lock and counter to init_worker
        with Pool(size, initializer=JobManager.init_worker,
                  initargs=(worker_lock, worker_counter)) as p:
            while semaphore.is_on(self.__class__.__name__):
                while not q.empty():
                    job = q.get()
                    job_key_dict[job.result_key] = p.apply_async(
                        job.execute,
                        callback=job.execute_callback,
                        error_callback=job.error_callback
                    )

                # check results for complete job and put them on external lookup
                for key in list(job_key_dict.keys()):
                    if job_key_dict[key].ready():
                        async_return = job_key_dict.pop(key)
                        if async_return.successful():
                            job_result = async_return.get()
                            results_dict[key] = job_result
                        else:
                            try:
                                async_return.get()
                            except Exception as e:
                                results_dict[key] = e
                        q.task_done()
                sleep(1)
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
        # init_time = perf_counter()
        print(f'+     {self.job_name}', flush=True)
        return self.execute_function(*self.execute_function_arguments, **self.execute_function_keyword_arguments)

    def execute_callback(self, result, message: str = None):
        if message is not None:
            print(f'-     {self.job_name}  {message}', flush=True)
        else:
            print(f'-     {self.job_name}', flush=True)

    def error_callback(self, error):
        print(f'<!>  {self.job_name}, {error.__class__.__name__} {error}', flush=True)

    def __init__(self, job_name, result_key, function, arguments, keyword_arguments):
        self.job_name = job_name
        self.result_key = result_key
        self.execute_function = function
        self.execute_function_arguments = arguments
        self.execute_function_keyword_arguments = keyword_arguments
