from threading import Thread
from Queue import Queue
from config import ConfigBorg
import logging
from Model import Report, Session, Submission

class Skeleton():
    def __init__(self, log_queue=None, **kwargs):
        self.__ModuleName__ = self.__class__.__name__
        self.workers = []
        self.queue = Queue()
        self.result_queue = Queue()
        self.log_queue = log_queue
        self.config = ConfigBorg()
        self.module_config = getattr(self.config, self.__ModuleName__)
        self.__init_workers()

    def __init_workers(self):
        logging.debug("Spawning workers")
        for w in range(self.module_config['worker_threads']):
            p = self.worker_class(self.queue, self.result_queue, self.log_queue, self.module_config, self.__ModuleName__)
            self.workers.append(p)
            p.start()
        logging.debug("Done : %s" % self.workers)

    def analyse(self, submission):
        if submission is None:
            logging.debug("Notifying every worker to exit...")
            for m in self.workers:
                self.queue.put(None)
                logging.debug("Waiting for %s worker to exit" % m)
            for m in self.workers:
                m.join()
                logging.debug("%s worker exit success" % m)
            logging.debug("Module ended")
            return False
        else:
            return self._filter_submissions(submission)

    def reportAlreadyAvailable(self, submission):
        return len([r for s in submission.file.submissions for r in s.reports if r.module == self.__ModuleName__]) != 0

    def _filter_submissions(self, submission):
        #  Default : reject if file already analyzed, accept every types
        if not self.reportAlreadyAvailable(submission):  # Check if a report has already been generated for this file
            return self._accept(submission)
        else:
            return self._reject(submission)

    def _accept(self, submission):
        logging.debug("Accepted")
        self.queue.put(submission.id)
        return True

    def _reject(self, submission):
        logging.debug("Rejected")
        return False


class skeletonWorker(Thread):
    def __init__(self, job_queue, result_queue, log_queue, module_config, module_name):
        Thread.__init__(self)
        self.log_queue = log_queue
        self.queue = job_queue
        self.result_queue = result_queue
        self.module_config = module_config
        self.__ModuleName__ = module_name

    def _preRun(self):
        pass

    def _postRun(self):
        return 0

    def run(self):
    #if self.log_queue is not None:
    #EnableLogging(self.log_queue)
        self._preRun()
        while True:
            logging.debug("Waiting for a job...")
            job = self.queue.get()
            if job is None:
                logging.warning("Got None job, exiting...")
                self.queue.task_done()
                break
            logging.debug("Got a job %s"%(job))
            self._do_work_wrapper(job)
            logging.debug("job done %s"%(job))
            self.queue.task_done()
        return self._postRun()

    def _do_work_wrapper(self, submission_id):
        s = Session()
        submission = s.query(Submission).filter(Submission.id==submission_id).one()
        try:
            r = self._do_work(submission)
            s.expunge(r)
            self.result_queue.put(r)
        except Exception as e:
            logging.error("Got exception : %s"%e)
            r = Report(
                module=self.__ModuleName__,
                short="Got an exception in module : %s"%e,
                full="",
                submission=submission
            )
            s.add(r)
            s.expunge(r)
            self.result_queue.put(r)

    def _do_work(self, submission):
        raise Exception("To be implemented in child")