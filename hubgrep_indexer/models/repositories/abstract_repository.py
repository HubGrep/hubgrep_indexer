"""
All hoster repo classes are inherited from the AbstractRepository class defined here.

This module contains helpers to export the repos as well.
"""
import logging
import gzip

from typing import Union, TYPE_CHECKING

from flask import current_app
from sqlalchemy.ext.declarative import declared_attr
from hubgrep_indexer.lib.table_helper import TableHelper

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

    # foreign keys in abstract classes need to be defined in attributes
    # https://stackoverflow.com/questions/32341408/sqlalchemy-concrete-inheritance-but-parent-has-foreignkey/32344269#32344269
    @declared_attr
    def hosting_service_id(cls):
        return db.Column(
            db.Integer, db.ForeignKey("hosting_service.id"), nullable=False
        )

    @classmethod
    def get_finished_table_name(cls, hosting_service: 'HostingService'):
        return f"hoster_{hosting_service.id}_repositories_complete"

    # order is important here!
    # should be the same as in hubgrep_search/hubgrep/cli_blueprint/import_data.py
    unified_select_template = """
        {foreign_id} as foreign_id,
        {name} as name,
        {username} as username,
        {description} as description,
        {created_at} as created_at,
        {updated_at} as updated_at,
        {pushed_at} as pushed_at,
        {stars_count} as stars_count,
        {forks_count} as forks_count,
        {is_fork} as is_fork,
        {is_archived} as is_archived,
        {is_mirror} as is_mirror,
        {is_empty} as is_empty,
        {homepage_url} as homepage_url,
        {repo_url} as repo_url
        """

    @property
    def unification_mapping(self):
        """
        has to be defined for all subclasses

        cls.unification_mapping has to be defined for all subclasses
        and reflects the mapping from the specific repo fields to its unified version.

        all variables used in `unified_select_mapping` have to be defined.

        eg:
        ```unification_mapping = dict(
                foreign_id="my_hosters_id_field",
                name='my_hosters_repo_name',
                ...
                )
        ```
        """
        raise NotImplementedError

    @classmethod
    def get_unified_select_sql(cls, hosting_service: "HostingService") -> str:
        """
        get the sql statement for a "unified" export for this hostingservices repos.

        fills out the select field part from `unified_select_mapping` for the specfic repo,
        and wraps it in the select statement
        """
        # cls.unified_select_mapping is a dict, defined for each subclass
        unified_select_part = cls.unified_select_template.format_map(cls.unification_mapping)
        unified_select_template = """
        select
            {SELECT_MAPPING}
        from
            {TABLE_NAME}
        """
        select_statement = unified_select_template.format(
            SELECT_MAPPING=unified_select_part,
            TABLE_NAME=cls.get_finished_table_name(hosting_service),
        )
        return select_statement

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
        drop and recreate the table for the hoster repos of this run

        use at the end of a hoster run to put the newest version of the hosters repos
        in its separate table before making exports
        """
        logger.debug(f"rotating repos for {hosting_service}")
        repo_class = cls.repo_class_for_type(hosting_service.type)

        with TableHelper._cursor() as cur:
            TableHelper.recreate_finished_hoster_repo_table(cur, hosting_service)

            # clean up our working table
            cur.execute(
                f"""
                delete
                from {repo_class.__tablename__}
                where
                    hosting_service_id = %s
                """,
                (
                    hosting_service.id,
                ),
            )

    @classmethod
    def _copy_to_csv(cls, select_statement, export_filename):
        logger.debug("running export...")
        con = db.engine.raw_connection()
        try:
            cur = con.cursor()
            result_path = f"{current_app.config['RESULTS_PATH']}/{export_filename}"
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
    def export_csv_gz(
        cls,
        hosting_service: "HostingService",
        filename: str,
    ) -> None:
        """
        export table content to a csv
        """
        finished_table_name = cls.get_finished_table_name(hosting_service)
        select_statement = f"select * from {finished_table_name}"
        cls._copy_to_csv(select_statement, filename)

    @classmethod
    def export_unified_csv_gz(
        cls,
        hosting_service: "HostingService",
        filename: str,
    ) -> None:
        select_statement = cls.get_unified_select_sql(hosting_service)
        cls._copy_to_csv(select_statement, filename)

    @classmethod
    def count_export_rows(cls, hosting_service: "HostingService") -> int:
        """
        count the rows of the finished repository table for this hosting_service
        """
        finished_table_name = cls.get_finished_table_name(hosting_service)
        with TableHelper._cursor() as cur:
            return TableHelper.count_table_rows(cur, finished_table_name)

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
