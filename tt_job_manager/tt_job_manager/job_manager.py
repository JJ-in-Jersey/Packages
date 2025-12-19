from tt_singleton.singleton import Singleton
from tt_semaphore import simple_semaphore as semaphore
from multiprocessing import Manager, Pool, cpu_count, Process, JoinableQueue
from time import sleep

class JobManager(metaclass=Singleton):

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
        self.qm = WaitForProcess(target=QueueManager, name='QueueManager', args=(self._queue, self._results_key_dict, pool_size,))
        self.qm.start()

class QueueManager:

    def __init__(self, q, results_dict, size):
        print(f'+     queue manager (Pool size = {size})\n', flush=True)
        semaphore.on(self.__class__.__name__)
        job_key_dict = {}
        with Pool(size) as p:
            while semaphore.is_on(self.__class__.__name__):  # pull submitted jobs and start them in the pool
                while not q.empty():
                    job = q.get()  # retrieve the job, launch the job
                    job_key_dict[job.result_key] = p.apply_async(job.execute, callback=job.execute_callback, error_callback=job.error_callback)

                # check results for complete job and put them on external lookup
                for key in list(job_key_dict.keys()):
                    if job_key_dict[key].ready():  # job is complete, but not necessarily successful
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
        print(f'<!>   {self.job_name}, {error.__class__.__name__} {error}', flush=True)

    def __init__(self, job_name, result_key, function, arguments, keyword_arguments):
        self.job_name = job_name
        self.result_key = result_key
        self.execute_function = function
        self.execute_function_arguments = arguments
        self.execute_function_keyword_arguments = keyword_arguments
