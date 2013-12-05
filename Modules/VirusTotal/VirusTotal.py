import logging
from Model import Report, ReportSection, Session
from json import JSONEncoder
from Tools.virustotal.virustotal import VirusTotal as VirusTotalLib
from Tools.tools import EnableProxy
from Modules.Skeleton.Skeleton import Skeleton, skeletonWorker


class VirusTotal(Skeleton):
    def __init__(self, **kwargs):
        self.worker_class = Worker
        Skeleton.__init__(self)


class Worker(skeletonWorker):

    def _preRun(self):
        self.vt = VirusTotalLib(self.module_config['apikey'], self.module_config['request_rate'])
        EnableProxy()

    def _do_work(self, submission):
        #Do the actual work
        report = self.vt.get(submission.file.sha256)
        s = Session()
        r = Report(
            module=self.__ModuleName__,
            short="Short desc...",
            full="",
            submission=submission
        )
        s.add(r)
        new_vt_submission = False
        if report is None:
            # Unknown in VT
            r.short = "Unknown on VT"
            if self.module_config['submit_unknown']:
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
        return r

