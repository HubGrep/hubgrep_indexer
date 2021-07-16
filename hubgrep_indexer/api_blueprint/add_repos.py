import time
from flask import request
from flask import jsonify
from flask_login import login_required

import logging

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.models.repositories.abstract_repository import Repository
from hubgrep_indexer.lib.state_manager.host_state_helpers import get_state_helper
from hubgrep_indexer import db, state_manager

from hubgrep_indexer.api_blueprint import api

logger = logging.getLogger(__name__)


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

    # add repos to the db :)
    logger.debug(f"adding repos to {hosting_service}")
    before = time.time()
    repo_class = Repository.repo_class_for_type(hosting_service.type)
    parsed_repos = []
    for repo_dict in repo_dicts:
        try:
            r = repo_class.from_dict(hosting_service_id, repo_dict)
            parsed_repos.append(r)
        except Exception as e:
            logger.exception(f"could not parse repo dict for {hosting_service}")
            logger.warning(f"(skipping) repo dict: {repo_dict}")

    db.session.bulk_save_objects(parsed_repos)
    db.session.commit()
    logger.debug(f"adding {len(parsed_repos)} repos to {hosting_service} took {time.time() - before}s")

    state_helper = get_state_helper(hosting_service.type)

    # will block, if the lock is already aquired, and go on after release
    with state_manager.get_lock(hosting_service_id):
        run_is_finished = state_helper.resolve_state(
            hosting_service_id=hosting_service_id,
            state_manager=state_manager,
            block_uid=block_uid,
            parsed_repos=parsed_repos,
        )
    
    if run_is_finished:
        logger.info(f"{hosting_service} run is finished, rotating repos! :confetti:")
        repo_class.rotate(hosting_service)

        logger.info(f"{hosting_service}: exporting raw!")
        export = hosting_service.export_repositories(unified=False)
        db.session.add(export)
        db.session.commit()

        logger.info(f"{hosting_service}: exporting unified!")
        export = hosting_service.export_repositories(unified=True)
        db.session.add(export)
        db.session.commit()

    return jsonify(dict(status="ok")), 200
