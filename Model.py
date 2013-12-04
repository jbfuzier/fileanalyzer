__author__ = 'jb'
from Tools.tools import hashdigest, exiftool
import logging
from config import ConfigBorg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, DateTime, Boolean
from sqlalchemy.orm import relationship, backref, sessionmaker, scoped_session
import os
import json
from json import JSONEncoder
from datetime import datetime


Base = declarative_base()
config = ConfigBorg()


class Db():
    # If needed distribute a Thread Lock with the db...
    #__shared_state = {}
    def __init__(self, db=config.db_path):
        logging.debug("INIT DB")
        #self.__dict__ = self.__shared_state
        #if self.engine is None:
        self._initDb(db)
#    engine = None
#    session = None
#    meta = None

    def _initDb(self, db):
        #self.engine = create_engine(db, echo=False, connect_args={'timeout': 15})
        self.engine = create_engine(db, echo=False)
        session_factory = sessionmaker(bind=self.engine)
        print "SESSIONFACTORY"
        self.session = scoped_session(session_factory)
        Base.metadata.create_all(self.engine)
        self.meta = Base.metadata

    def _truncate(self):
        for tbl in reversed(self.meta.sorted_tables):
            self.engine.execute(tbl.delete())

    def close(self):
        self.session.close()
        logging.debug("DB session closed...")




class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sha256 = Column(String, unique=True, nullable=False)
    md5 = Column(String)
    sha1 = Column(String)
    type = Column(String)
    mimetype = Column(String)
    size = Column(String)
    config = ConfigBorg()

    @property
    def path(self):
        path = os.path.join(self.config.flask['upload_dir'], self.sha256)
        return path

    @property
    def last_submission(self):
        Session.expire_all()
        s = Session.query(Submission).filter(File.id == self.id).order_by(-Submission.id).first()
        return s

    @property
    def wip(self):
        if self.last_submission.done is not True:
                return True
        return False

    @property
    def progress(self):
        d = {
            'results': self.last_submission.results,
            'totals': self.last_submission.working_modules
        }
        if d['results'] == d['totals']:
            d['done'] = True
        else:
            d['done'] = False
        json = JSONEncoder().encode(d)
        return json

    def __str__(self):
        return "{:<6} {:<20} {:<10} {:<10} {} {} {}".format(
            self.id,
            self.sha256,
            self.sha1,
            self.md5,
            self.type,
            self.mimetype,
            self.size,
            )


class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow())
    name = Column(String)
    working_modules = Column(Integer, default=0)
    results = Column(Integer, default=0)
    extension = Column(String)
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship("File", backref='submissions')
    exif_tools = exiftool()

    @property
    def done(self):
        return self.working_modules == self.results

    def __init__(self, path, name):
        self.config = ConfigBorg()
        self.path = path
        self.name = name
        #self.db = db
        logging.debug(path)
        self.new_file = True
        self._populate()  # Hash and type and create File object
        logging.debug("%s"%self)
        Session().add(self)
        Session().commit()

    def _populate(self):
        """
            Compute data related to the file : type, hash, version,....
        """

        #Hash
        h = hashdigest(self.path)
        sha256 = h['sha256'].lower()

        #Type
        et = self.exif_tools
        metadata = et.get_metadata(self.path)
        #self.name = metadata['File:FileName']

        #Extension
        if '.' in self.name:
            self.extension = self.name.split('.')[-1].lower()
        else:
            self.extension = ""

        file = Session().query(File).filter_by(sha256=sha256).all()
        if len(file) != 0:
            self.new_file = False
            self.file = file[0]
        else:
            try:
                type = metadata['File:FileType'].lower()
            except KeyError:
                type = "unknown"
            try:
                mimetype = metadata['File:MIMEType'].lower()
            except KeyError:
                mimetype = "unknown"
            self.file = File(
                md5=h['md5'].lower(),
                sha1=h['sha1'].lower(),
                sha256=h['sha256'].lower(),
                type=type,
                mimetype=mimetype,
                size=metadata['File:FileSize'],
            )
            Session().add(self.file)
            Session().commit()

    def __str__(self):
        if self.file is None:
            return ""
        return "{:<20} {:<6} {:<10} {:<10} {} {} {} {}".format(
            self.name,
            self.extension,
            self.file.type,
            self.file.mimetype,
            self.file.size,
            self.file.md5,
            self.file.sha1,
            self.file.sha256,
            )


class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    module = Column(String)
    short = Column(String)
    full = Column(String)
    threat_level = Column(Integer, default=50)
    submission_id = Column(Integer, ForeignKey('submissions.id'))
    submission = relationship("Submission", backref='reports')

    @property
    def full_dict(self):
        return json.loads(self.full)

    def __str__(self):
        return "{:<20} {:<6} {:<10} {:<10}".format(
            self.module,
            self.short,
            self.submission,
            self.submission.file,
            )
#db = Db()
#session = db.session


class ReportSection(Base):
    __tablename__ = 'sections'
    id = Column(Integer, primary_key=True)
    type = Column(String)
    value = Column(String)
    report_id = Column(Integer, ForeignKey('reports.id'))
    report = relationship("Report", backref='sections')
    @property
    def value_dict(self):
        return json.loads(self.value)


Session = Db().session

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    f = Submission("c:\\windows\\system32\\calc.exe")