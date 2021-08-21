import logging
from typing import TYPE_CHECKING
from contextlib import contextmanager

from hubgrep_indexer import db

if TYPE_CHECKING:
    from hubgrep_indexer.models.hosting_service import HostingService

logger = logging.getLogger(__name__)


class TableHelper:
    """
    helper class for raw db requests

    use like
    ```
    with TableHelper._cursor() as cur:
        TableHelper.drop_table(cur, "some_table")
    ```

    commit runs on leaving context
    """

    @classmethod
    @contextmanager
    def _cursor(cls):
        con = db.engine.raw_connection()
        try:
            cur = con.cursor()
            yield cur
            con.commit()
        finally:
            con.close()

    @classmethod
    def drop_table(cls, cur, table_name):
        """
        drop table (if exists)
        """
        cur.execute(f"drop table if exists {table_name}")

    @classmethod
    def recreate_finished_table(cls, cur, hosting_service: 'HostingService'):
        """
        drop and recreate the finished table for a hosting service
        """
        from hubgrep_indexer.models.repositories.abstract_repository import Repository
        repo_class = Repository.repo_class_for_type(hosting_service.type)
        source_table = repo_class.__tablename__
        target_table = Repository.get_finished_table_name(hosting_service)

        cls.drop_table(cur, target_table)

        cur.execute(
            f"""
                create table {target_table}
                as select *
                from {source_table}
                where hosting_service_id = %s
                """,
            (hosting_service.id,),
        )
