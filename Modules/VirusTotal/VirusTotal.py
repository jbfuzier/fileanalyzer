from threading import Thread
from Queue import Queue
from config import ConfigBorg
import logging
from Model import Report, ReportSection, Session, Submission
from json import JSONEncoder
from Tools.virustotal.virustotal import VirusTotal as VirusTotalLib
from Tools.tools import EnableProxy

__ModuleName__ = "VirusTotal"

class VirusTotal():
    def __init__(self, log_queue=None):
        self.workers = []
        self.queue = Queue()
        self.result_queue = Queue()
        self.log_queue = log_queue
        self.config = ConfigBorg()
        self.vt = VirusTotalLib(self.config.virustotal['apikey'], self.config.virustotal['request_rate'])
        self.__init_workers()

    def __init_workers(self):
        logging.debug("Spawning workers")
        for w in range(self.config.virustotal['worker_threads']):
            p = skeletonWorker(self.queue, self.result_queue, self.log_queue, self.vt)
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
        return len([r for s in submission.file.submissions for r in s.reports if r.module == __ModuleName__]) != 0

    def _filter_submissions(self, submission):
        # TODO Filter by file type
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
    def __init__(self, job_queue, result_queue, log_queue, vt):
        Thread.__init__(self)
        self.log_queue = log_queue
        self.queue = job_queue
        self.result_queue = result_queue
        self.vt = vt
        self.config = ConfigBorg()

    def run(self):
    #if self.log_queue is not None:
    #EnableLogging(self.log_queue)
        EnableProxy()
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

    def _do_work(self, submission_id):
        s = Session()
        submission = s.query(Submission).filter(Submission.id==submission_id).one()
        #Do the actual work
        report = self.vt.get(submission.file.sha256)
        s = Session()
        r = Report(
            module=__ModuleName__,
            short="Short desc...",
            full="",
            submission=submission
        )
        s.add(r)
        new_vt_submission = False
        if report is None:
            # Unknown in VT
            r.short = "Unknown on VT"
            if self.config.virustotal['submit_unknown']:
                report = self.vt.scan(submission.file.path, reanalyze=True)
                report.join()
                new_vt_submission = True
        try:
            assert report.done is True
            # Known in VT
            r.short = "Detection rate : %s/%s - %s" % (report.positives, report.total, report.verbose_msg)
            if new_vt_submission:
                r.short += " (First submission in VT)"
            if report.positives == 0:
                r.threat_level = 0
            elif report.positives > 5:
                r.threat_level = 100
            report_details = report._report
            json = JSONEncoder().encode(report_details)
            section = ReportSection(
                type='json',
                value=json,
                report=r
            )
            s.add(section)
        except Exception as e:
            logging.error("Could not get report from vt : %s"%e)

        s.commit()
        #r._sa_instance_state.session.expunge(r)
        s.expunge(r)
        self.result_queue.put(r)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    s =Skeleton()