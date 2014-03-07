from Model import Report, ReportSection, Session
from Modules.Skeleton.Skeleton import Skeleton, skeletonWorker
from Tools.AnalyzePDFCustom import AnalyzePDF

class Pdf(Skeleton):
    def __init__(self, **kwargs):
        self.worker_class = Worker
        Skeleton.__init__(self)

    def _filter_submissions(self, submission):
        # TODO Filter by file type
        pass
        if (not self.reportAlreadyAvailable(submission)) \
            and (
                        (submission.extension.lower() == "pdf")
                    or
                        (submission.file.type.lower() == "pdf")
                    or
                        (submission.file.mimetype.lower() == "application/pdf")
            ):
            return self._accept(submission)
        else:
            return self._reject(submission)


class Worker(skeletonWorker):

    def _do_work(self, submission):
        a = AnalyzePDF(submission.file.path, toolpath=self.module_config['tool_path'])
        sev, comment = a.analyze() #  (sev (0-5+), "comment")
        r = Report(
            module=self.__ModuleName__,
            short="%s (%s)" % (sev, comment),
            full="",
            submission=submission
        )
        if sev >= 5:
            r.threat_level = 100
        elif sev >=2:
            r.threat_level = 50
        else:
            r.threat_level = 0
        Session.add(r)


        section = ReportSection(
            type='text',
            value=a.anomalies_string,
            report=r
        )
        Session.add(section)

        section = ReportSection(
            type='text',
            value=a.pdfid_str,
            report=r
        )

        Session.add(section)

        Session.commit()
        #r._sa_instance_state.session.expunge(r)
        return r

