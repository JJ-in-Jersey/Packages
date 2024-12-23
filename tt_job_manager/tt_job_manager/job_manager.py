from tt_singleton.singleton import Singleton
from tt_semaphore import simple_semaphore as semaphore
from tt_date_time_tools.date_time_tools import mins_secs
from multiprocessing import Manager, Pool, cpu_count, Process
from time import sleep, perf_counter


class JobManager(metaclass=Singleton):

    manager = None
    queue = None
    results_key_dict = {}

    @staticmethod
    def submit_job(job):
        JobManager.queue.put(job)
        return job.result_key

    @staticmethod
    def get_result(key):
        return JobManager.results_key_dict.pop(key)

    @staticmethod
    def wait():
        JobManager.queue.join()
        

    @staticmethod
    def stop_queue():
        semaphore.off('QueueManager')

    def __init__(self, pool_size=cpu_count()):
        print(f'\nStarting multiprocess job manager')
        JobManager.manager = Manager()
        JobManager.queue = JobManager.manager.JoinableQueue()
        JobManager.results_key_dict = JobManager.manager.dict()
        self.qm = WaitForProcess(target=QueueManager, name='QueueManager', args=(JobManager.queue, JobManager.results_key_dict, pool_size,))
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
                            results_dict[key] = job_result[1]  # results format is tuple of (key, data, init time)
                        else:
                            results_dict[key] = None
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
        init_time = perf_counter()
        print(f'+     {self.job_name}', flush=True)
        return tuple([self.result_key, self.execute_function(*self.execute_function_arguments), mins_secs(perf_counter()-init_time)])

    def execute_callback(self, result):
        print(f'-     {self.job_name} {result[2]}', flush=True)

    def error_callback(self, result):
        print(f'!     {self.job_name} error: {result}', flush=True)

    def __init__(self, job_name, result_key, function, arguments):
        self.job_name = job_name
        self.result_key = result_key
        self.execute_function = function
        self.execute_function_arguments = arguments
