from threading import Thread
from Queue import Queue
from config import ConfigBorg
from Tools.tools import exiftool
import logging
from Model import Report
from json import JSONEncoder

__ModuleName__ = "Exiftools"

class Exiftools():
    def __init__(self, log_queue=None):
        self.workers = []
        self.queue = Queue()
        self.result_queue = Queue()
        self.log_queue = log_queue
        self.config = ConfigBorg()
        self.exif_tool = exiftool()
        self.__init_workers()

    def __init_workers(self):
        logging.debug("Spawning workers")
        for w in range(self.config.worker_threads):
            p = skeletonWorker(self.queue, self.result_queue, self.log_queue, self.exif_tool)
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
        else:
            self._filter_submissions(submission)

    def _filter_submissions(self, submission):
        if True:
            return self._accept(submission)
        else:
            return self._reject(submission)

    def _accept(self, submission):
        logging.debug("Accepted")
        self.queue.put(submission)
        return True

    def _reject(self, submission):
        logging.debug("Rejected")
        return False


class skeletonWorker(Thread):
    def __init__(self, job_queue, result_queue, log_queue, exif_tool):
        Thread.__init__(self)
        self.log_queue = log_queue
        self.queue = job_queue
        self.result_queue = result_queue
        self.exif_tool = exif_tool

    def run(self):
    #if self.log_queue is not None:
    #EnableLogging(self.log_queue)
        while True:
            logging.debug("Waiting for a job...")
            job = self.queue.get()
            if job is None:
                logging.warning("Got None job, exiting...")
                self.queue.task_done()
                break
            logging.debug("Got a job %s"%(job))
            self._do_work(job)
            logging.debug("job done %s"%(job))
            self.queue.task_done()
        return 0

    def _do_work(self, submission):
        #Do the actual work
        metadata = self.exif_tool.get_metadata(submission.file.path)
        metadata_hierarchy = {}
        for value, key in enumerate(metadata):
            parent = metadata_hierarchy
            subkeys = key.split(':')
            for i in range(len(subkeys) - 1):
                current = subkeys[i]
                if current not in parent:
                    parent[current] = {}
                parent = parent[current]
            current = subkeys[-1]
            parent[current] = value
        json = JSONEncoder().encode(metadata_hierarchy)
        r = Report(
            module=__ModuleName__,
            short="Short desc...",
            full=json,
            submission=submission
        )
        self.result_queue.put(r)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    s =Skeleton()