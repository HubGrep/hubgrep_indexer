"""
All hoster repo classes are inherited from the AbstractRepository class defined here.

This module contains helpers to export the repos as well.
"""
import logging
import time
import gzip
from pathlib import Path
from contextlib import contextmanager

from typing import Union, TYPE_CHECKING

from flask import current_app
from sqlalchemy.ext.declarative import declared_attr

from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITEA,
    HOST_TYPE_GITLAB,
)

from hubgrep_indexer import db

if TYPE_CHECKING:
    from hubgrep_indexer.models.hosting_service import HostingService

logger = logging.getLogger(__name__)


class Repository(db.Model):
    __abstract__ = True

    id = db.Column(db.BigInteger, primary_key=True)
    is_completed = db.Column(db.Boolean, nullable=True)

    # foreign keys in abstract classes need to be defined in attributes
    # https://stackoverflow.com/questions/32341408/sqlalchemy-concrete-inheritance-but-parent-has-foreignkey/32344269#32344269
    @declared_attr
    def hosting_service_id(cls):
        return db.Column(
            db.Integer, db.ForeignKey("hosting_service.id"), nullable=False
        )

    @classmethod
    def clean_string(cls, string: Union[str, None]) -> str:
        """
        clean strings for text fields before saving them to the db
        """
        if string:
            # postgres was throwing
            # `ValueError: A string literal cannot contain NUL (0x00) characters.`
            # since the NUL byte was part of some random description.
            # we follow the suggestion from https://stackoverflow.com/a/61958678
            string = string.replace("\x00", "\uFFFD")
        return string

    @declared_attr
    def hosting_service(cls):
        return db.relationship("HostingService")

    @classmethod
    def rotate(cls, hosting_service: "HostingService") -> None:
        """
        delete repos from old runs, set `is_completed` to new ones
        """
        logger.debug(f"rotating repos for {hosting_service}")
        repo_class = cls.repo_class_for_type(hosting_service.type)
        con = db.engine.raw_connection()
        try:
            cur = con.cursor()
            cur.execute(
                f"""
                delete
                from {repo_class.__tablename__}
                where
                    is_completed is true
                and
                    hosting_service_id = %s
                """,
                (hosting_service.id,),
            )
            # set our new imports to "is_completed", and add the hoster id
            cur.execute(
                f"""
                update {repo_class.__tablename__}
                set
                    is_completed = true
                where
                    is_completed is null
                    and
                    hosting_service_id = %s
                """,
                (hosting_service.id,),
            )
            # commit!
            con.commit()
        finally:
            con.close()

    @classmethod
    @contextmanager
    def make_tmp_table(cls, hosting_service: "HostingService") -> str:
        """
        make a temporary table as a copy of the table for <hosting_service>
        use as context_manager:
            ```
            with repo_class.make_tmp_table(hosting_service) as table_name:
                do_stuff(table_name)
            ```
        table will be deleted when leaving the context
        """
        tmp_table_name = (
            f"{hosting_service.type}_{hosting_service.id}_tmp_{int(time.time())}"
        )
        before = time.time()
        con = db.engine.raw_connection()
        try:
            cur = con.cursor()
            # todo: test if it makes a difference in time when we filter this here,
            # and let the temp table only have the hoster included
            cur.execute(
                f"""CREATE TABLE {tmp_table_name} as table {cls.__tablename__}
                """
                # select from ...
                # where
                #    hosting_service_id = %s,
                # and
                #    is_completed = true
                # (hosting_service_id,),
            )
            con.commit()
        finally:
            con.close()
        logger.info(
            f"creating temp table {tmp_table_name} took {time.time() - before}s"
        )
        try:
            yield tmp_table_name
        finally:
            cls._drop_tmp_table(tmp_table_name)

    @classmethod
    def _drop_tmp_table(cls, tmp_table_name: str) -> str:
        """
        drop table `tmp_table_name`
        returns `tmp_table_name`
        """
        before = time.time()
        con = db.engine.raw_connection()
        try:
            cur = con.cursor()
            cur.execute(
                f"""
                DROP TABLE {tmp_table_name}
                """
                # select from ...
                # where
                #    hosting_service_id = %s,
                # and
                #    is_completed = true
                # (hosting_service_id,),
            )
            con.commit()
        finally:
            con.close()
        logger.info(
            f"dropping temp table {tmp_table_name} took {time.time() - before}s"
        )
        return tmp_table_name

    @classmethod
    def export_csv_gz(
        cls,
        table_name: str,
        hosting_service: "HostingService",
        filename: str,
        results_base_path: str = None,
        select_statement_template: str = None,
    ) -> None:
        """
        export table content to a csv

        this feels horribly hacky, but its fast.
        """
        if not results_base_path:
            results_base_path = current_app.config["RESULTS_PATH"]
        results_base_path = Path(results_base_path)

        if not select_statement_template:
            select_statement_template = """
            select * from {TABLE_NAME}
            where
                hosting_service_id = {HOSTING_SERVICE_ID}
            and
                is_completed = true
            """
        select_statement = select_statement_template.format(
            TABLE_NAME=table_name,
            HOSTING_SERVICE_ID=hosting_service.id,
        )

        logger.debug("running export...")
        con = db.engine.raw_connection()
        try:
            cur = con.cursor()
            result_path = f"{current_app.config['RESULTS_PATH']}/{filename}"
            with gzip.open(result_path, "w") as gzfile:
                cur.copy_expert(
                    f"""
                        COPY ({select_statement})
                        TO STDOUT
                        delimiter ';'
                        csv header
                        """,
                    gzfile,
                )
        finally:
            con.close()

    @classmethod
    def export_unified_csv_gz(
        cls,
        table_name: str,
        hosting_service: "HostingService",
        filename: str,
        results_base_path: str = None,
    ) -> None:
        select_statement_template = cls.unified_select_statement_template
        cls.export_csv_gz(
            table_name,
            hosting_service,
            filename,
            results_base_path,
            select_statement_template,
        )

    def to_dict(self):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, hosting_service_id, d: dict, update=True):
        raise NotImplementedError

    @classmethod
    def repo_class_for_type(cls, type: str) -> "Repository":
        # prevent circular import
        from hubgrep_indexer.models.repositories.gitea import GiteaRepository
        from hubgrep_indexer.models.repositories.github import GithubRepository
        from hubgrep_indexer.models.repositories.gitlab import GitlabRepository

        RepoClasses = {
            HOST_TYPE_GITHUB: GithubRepository,
            HOST_TYPE_GITEA: GiteaRepository,
            HOST_TYPE_GITLAB: GitlabRepository,
        }
        return RepoClasses[type]
