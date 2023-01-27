from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import UniqueConstraint
from sqlalchemy.orm import sessionmaker
import random as r

r.seed(2345)

Base = declarative_base()


class Course(Base):
    __tablename__ = "course"

    id = Column("id", Integer, primary_key=True)
    code = Column("code", String)
    name = Column("name", String)
    description = Column("description", String)
    gpa = Column("gpa", String)
    gpa_url = Column("gpa_url", String)
    enroll = Column("enroll", String)
    profName = Column("professor_name", String)
    rmp = Column("rate_my_prof", String)
    rmp_url = Column("rate_my_prof_url", String)
    __table_args__ = (
        UniqueConstraint(
            "code",
            "description",
            "gpa",
            "gpa_url",
            "enroll",
            "professor_name",
            "rate_my_prof",
            "rate_my_prof_url",
            name="name",
        ),
    )

    def asdict(self):
        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "gpa": self.gpa,
            "gpa_url": self.gpa_url,
            "enroll": self.enroll,
            "professor_name": self.profName,
            "rate_my_prof": self.rmp,
            "rate_my_prof_url": self.rmp_url,
        }

    def __repr__(self):
        return f"({self.id}) {self.code} {self.description} {self.gpa} {self.gpa_url} {self.profName} {self.rmp} {self.rmp_url}"


if __name__ == "__main__":
    engine = create_engine("sqlite:///courseFind.db", echo=True)
    Base.metadata.create_all(bind=engine)
