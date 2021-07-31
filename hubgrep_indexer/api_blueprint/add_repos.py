import time
from typing import List
import logging

from flask import request
from flask import jsonify
from flask_login import login_required

from prometheus_client import Counter

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.lib.state_manager.host_state_helpers import get_state_helper
from hubgrep_indexer import db, state_manager

from hubgrep_indexer.api_blueprint import api

logger = logging.getLogger(__name__)


# todo: put in lib
"""
counter = Counter(
    "indexer_collected_repos",
    "collected repos in indexer",
    labelnames=("hosting_service_type", "hosting_service_id"),
)
"""

def _append_repos(hosting_service: HostingService, repo_dicts: List[dict]):
    repo_class = Repository.repo_class_for_type(hosting_service.type)
    if not repo_class:
        return jsonify(status="error", msg="unknown repo type"), 403

    # add repos to the db :)
    logger.debug(f"adding repos to {hosting_service}")
    repo_class = Repository.repo_class_for_type(hosting_service.type)
    parsed_repos = []
    for repo_dict in repo_dicts:
        try:
            r = repo_class.from_dict(hosting_service.id, repo_dict)
            parsed_repos.append(r)
        except Exception:
            logger.exception(f"could not parse repo dict for {hosting_service}")
            logger.warning(f"(skipping) repo dict: {repo_dict}")

    db.session.bulk_save_objects(parsed_repos)
    db.session.commit()

    #counter.labels(
    #    hosting_service_type=hosting_service.type,
    #    hosting_service_id=hosting_service.id,
    #).inc(len(parsed_repos))

    return parsed_repos, repo_class


@api.route("/hosters/<hosting_service_id>/", methods=["PUT"])
@api.route("/hosters/<hosting_service_id>/<block_uid>", methods=["PUT"])
@login_required
def add_repos(hosting_service_id: int, block_uid: int = None):
    """
    Add repository data used in our search-index.

    :param hosting_service_id: int - the registered hosting_service these repos belong to.
    :param block_uid: (optional) int - if this arg is missing the repos will be added without affecting internal state.
    """
    hosting_service: HostingService = HostingService.query.get(hosting_service_id)
    repo_dicts = request.json

    logger.debug(f"adding repos to {hosting_service}")
    ts_db_start = time.time()
    parsed_repos, repo_class = _append_repos(
        hosting_service=hosting_service, repo_dicts=repo_dicts
    )

    ts_db_end = time.time()
    logger.debug(
        f"added {len(parsed_repos)} repos for {hosting_service} - took {ts_db_end - ts_db_start}s"
    )
    state_helper = get_state_helper(hosting_service.type)

    # will block, if the lock is already aquired, and go on after release
    with state_manager.get_lock(hosting_service_id):
        run_is_finished = state_helper.resolve_state(
            hosting_service_id=hosting_service_id,
            state_manager=state_manager,
            block_uid=block_uid,
            parsed_repos=parsed_repos,
        )
    ts_state_end = time.time()
    logger.debug(
        f"updated state for {hosting_service} and block uid: {block_uid} - took {ts_state_end - ts_db_end}s"
    )

    if run_is_finished:
        logger.info(f"{hosting_service} run is finished, rotating repos! :confetti:")
        repo_class.rotate(hosting_service)
        ts_rotate_end = time.time()
        logger.debug(
            f"rotated repos for {hosting_service} - took {ts_rotate_end - ts_state_end}s"
        )

        logger.info(f"{hosting_service}: exporting raw!")
        export = hosting_service.export_repositories(unified=False)
        db.session.add(export)
        db.session.commit()

        logger.info(f"{hosting_service}: exporting unified!")
        export = hosting_service.export_repositories(unified=True)
        db.session.add(export)
        db.session.commit()

        ts_export_end = time.time()
        logger.debug(
            f"exported repos for {hosting_service} - took {ts_export_end - ts_rotate_end}s"
        )

    return jsonify(dict(status="ok")), 200
