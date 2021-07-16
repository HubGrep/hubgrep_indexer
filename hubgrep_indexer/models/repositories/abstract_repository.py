"""
All hoster repo classes are inherited from the AbstractRepository class defined here.

This module contains helpers to export the repos as well.
"""
import logging
import gzip
from pathlib import Path

from flask import current_app
from sqlalchemy.ext.declarative import declared_attr

from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITEA,
    HOST_TYPE_GITLAB,
)

from hubgrep_indexer import db

logger = logging.getLogger(__name__)


class Repository(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    is_completed = db.Column(db.Boolean, nullable=True)

    # foreign keys in abstract classes need to be defined in attributes
    # https://stackoverflow.com/questions/32341408/sqlalchemy-concrete-inheritance-but-parent-has-foreignkey/32344269#32344269
    @declared_attr
    def hosting_service_id(cls):
        return db.Column(
            db.Integer, db.ForeignKey("hosting_service.id"), nullable=False
        )

    @declared_attr
    def hosting_service(cls):
        return db.relationship("HostingService")

    @classmethod
    def rotate(cls, hosting_service):
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
    def export_csv_gz(
        cls,
        hosting_service_id,
        hosting_service_type,
        filename,
        results_base_path=None,
        select_statement_template=None,
    ):
        """
        export table content to a csv

        this feels horribly hacky, but its fast.
        """
        repo_class = cls.repo_class_for_type(hosting_service_type)

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
            TABLE_NAME=repo_class.__tablename__,
            HOSTING_SERVICE_ID=hosting_service_id,
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
        hosting_service_id,
        hosting_service_type,
        filename,
        results_base_path=None,
    ):
        select_statement_template = cls.unified_select_statement_template
        cls.export_csv_gz(
            hosting_service_id,
            hosting_service_type,
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
