__author__ = 'jb'
from Tools.tools import hashdigest, exiftool
import logging
from config import ConfigBorg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker
import os


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
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
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
    name = Column(String)
    extension = Column(String)
    file_id = Column(Integer, ForeignKey('files.id'))
    file = relationship("File", backref='submissions')
    exif_tools = exiftool()

    def __init__(self, path, name, db):
        self.config = ConfigBorg()
        self.path = path
        self.name = name
        self.db = db
        logging.debug(path)
        self.new_file = True
        self._populate()  # Hash and type and create File object
        logging.debug("%s"%self)
        self.db.session.add(self)
        self.db.session.commit()

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

        file = self.db.session.query(File).filter_by(sha256=sha256).all()
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
            self.db.session.add(self.file)
            self.db.session.commit()

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
    submission_id = Column(Integer, ForeignKey('submissions.id'))
    submission = relationship("Submission", backref='reports')

#db = Db()
#session = db.session

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    f = Submission("c:\\windows\\system32\\calc.exe")