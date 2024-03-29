import time
from typing import List
import logging

from flask import request
from flask import jsonify
from flask_login import login_required

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.lib.state_manager.host_state_helpers import get_state_helper
from hubgrep_indexer import db, state_manager, executor

from hubgrep_indexer.api_blueprint import api

logger = logging.getLogger(__name__)


def _append_repos(hosting_service: HostingService, repo_dicts: List[dict]):
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

    return parsed_repos


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

    repo_class = Repository.repo_class_for_type(hosting_service.type)
    if not repo_class:
        return jsonify(status="error", msg="unknown repo type"), 403

    logger.debug(f"adding repos to {hosting_service}")
    ts_db_start = time.time()
    parsed_repos = _append_repos(
        hosting_service=hosting_service, repo_dicts=repo_dicts
    )

    ts_db_end = time.time()
    logger.debug(
        f"added {len(parsed_repos)} repos for {hosting_service} - took {ts_db_end - ts_db_start}s"
    )
    state_helper = get_state_helper(hosting_service=hosting_service)

    # will block, if the lock is already aquired, and go on after release
    with state_manager.get_lock(hosting_service_id):
        is_run_finished = state_helper.resolve_state(
            hosting_service=hosting_service,
            block_uid=block_uid,
            parsed_repos=parsed_repos,
        )
    ts_state_end = time.time()
    logger.debug(
        f"updated state for {hosting_service} and block uid: {block_uid} - took {ts_state_end - ts_db_end}s"
    )

    if is_run_finished:
        executor.submit(hosting_service.handle_finished_run)

    return jsonify(dict(status="ok")), 200
