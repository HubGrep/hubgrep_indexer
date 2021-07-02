"""
All hoster repo classes are inherited from the AbstractRepository class defined here.

This module contains helpers to export the repos as well.
"""

import gzip
import json
import datetime
from typing import Union
from pathlib import Path

from flask import current_app
from sqlalchemy.ext.declarative import declared_attr

from hubgrep_indexer.constants import (
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITEA,
    HOST_TYPE_GITLAB,
)

from hubgrep_indexer import db


class DateTimeEncoder(json.JSONEncoder):
    """
    json encoder that can dump datetimes
    """

    # https://stackoverflow.com/a/12126976
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()


class StreamArray(list):
    """
    Converts a generator into a list object that can be json serialisable
    while still retaining the iterative nature of a generator.

    IE. It converts it to a list without having to exhaust the generator
    and keep it's contents in memory.
    """

    # https://stackoverflow.com/a/45143995
    def __init__(self, generator):
        self.generator = generator
        self._len = 1

    def __iter__(self):
        self._len = 0
        for item in self.generator:
            yield item
            self._len += 1

    def __len__(self):
        """
        Json parser looks for a this method to confirm whether or not it can
        be parsed
        """
        return self._len


class Repository(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

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
    def _yield_repo_list(cls, hosting_service_id=None, chunk_size=1000):
        """
        yield chunks of objects from the database

        buffers <chunk_size> elements in ram, but yields one element
        """
        if hosting_service_id:
            repos_query = cls.query.filter_by(hosting_service_id=hosting_service_id)
        else:
            repos_query = cls.query

        for repo in repos_query.order_by(cls.id.asc()).yield_per(chunk_size).all():
            yield repo.to_dict()

    @classmethod
    def export_json_gz(
        cls,
        hosting_service_id,
        filename,
        results_base_path: Union[Path, str] = None,
        chunk_size=1000,
    ):
        """
        write chunks from the database into a gzipped json file.

        writes to <results_base_path>/<filename>
        """
        if not results_base_path:
            results_base_path = current_app.config["RESULTS_PATH"]
        results_base_path = Path(results_base_path)
        with gzip.open(
            results_base_path.joinpath(filename), "wt", encoding="UTF-8"
        ) as zipfile:
            # first call to get the generator
            large_generator_handle = cls._yield_repo_list(
                hosting_service_id, chunk_size
            )
            # serialize to json chunks, so we can write piece by piece,
            # without using too much memory
            stream_array = StreamArray(large_generator_handle)
            for chunk in DateTimeEncoder().iterencode(stream_array):
                zipfile.write(chunk)

    def to_dict(self):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, hosting_service_id, d: dict, update=True):
        raise NotImplementedError

    @classmethod
    def repo_class_for_type(cls, type: str) -> 'Repository':
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