from flask import request
from flask import jsonify
from flask_login import current_user

import logging

from hubgrep_indexer.models.hosting_service import HostingService
from hubgrep_indexer.lib.hosting_service_validator import HostingServiceValidator
from hubgrep_indexer import db

from hubgrep_indexer.api_blueprint import api

logger = logging.getLogger(__name__)


@api.route("/hosters", methods=["GET", "POST"])
def hosters():
    """
    GET:
        if authorized, returns a list of hosters including secrets. used by the crawlers.
        if not authorized, it just returns a list of the hosting services.

    POST:
        the payload is validated as a new hosting service to add.
    """
    if request.method == "GET":
        hosting_services = []
        for hosting_service in HostingService.query.all():
            hosting_services.append(
                hosting_service.to_dict(include_secrets=current_user.is_authenticated, include_exports=True)
            )
        return jsonify(hosting_services)

    elif request.method == "POST":
        """
        dict(
            type="github",
            landingpage_url="https://...",
            api_url="https://...",
            config="{...}"
        )
        """
        hosting_service = HostingService.from_dict(request.json)
        logger.debug(f"trying to add hoster {hosting_service}")

        # test if hoster dict is valid
        if not HostingServiceValidator.test_hoster_is_valid(hosting_service):
            logger.debug(f"invalid hoster: {hosting_service}")
            return jsonify(
                dict(
                    added=False,
                    reason="wrong_response"
                    # reason="A response from the hoster did not look like we expected - are you sure this is correct?"
                )
            )

        # test if we already have this hoster
        if HostingService.query.filter_by(api_url=hosting_service.api_url).first():
            logger.debug(f"hoster already in list: {hosting_service}")
            return jsonify(
                dict(
                    added=False,
                    reason="already_in_list"
                    # reason="Thanks, but we already have this hoster in our list! :)"
                )
            )

        # otherwise, add the new hoster!
        logger.info(f"adding hoster {hosting_service}")
        db.session.add(hosting_service)
        db.session.commit()
        return jsonify(
            dict(
                added=True,
                hosting_service=hosting_service.to_dict(),
            )
        )
    else:
        return "login required", 401
