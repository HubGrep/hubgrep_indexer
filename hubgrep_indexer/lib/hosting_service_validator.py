import logging
from urllib.parse import urljoin
import requests

from hubgrep_indexer.models.hosting_service import HostingService

from hubgrep_indexer.constants import (
    HOST_TYPE_GITEA,
    HOST_TYPE_GITHUB,
    HOST_TYPE_GITLAB,
)

logger = logging.getLogger(__name__)


class HostingServiceValidator:
    @classmethod
    def _is_gitea_hoster(cls, hosting_service: HostingService):
        """
        check if the version route returns json with a "version" key
        """
        version_url = urljoin(hosting_service.api_url, "/api/v1/version")
        response = requests.get(version_url)
        try:
            if response.json().get("version", False):
                return True
        except Exception:
            return False

    @classmethod
    def _is_gitlab_hoster(cls, hosting_service: HostingService):
        """
        request a list of projects,
        since the version route is behing a login :facepalm:
        """
        response = requests.get(urljoin(hosting_service.api_url, "/api/v4/projects"))
        logger.debug(f"got gitlab response: {response.text}")
        if response.ok:
            # just check if its json. it should be.
            try:
                response.json()
            except Exception:
                return False
            return True
        return False

    @classmethod
    def _is_github_hoster(cls, hosting_service: HostingService):
        """
        check if the hoster has githubs "zen" route
        """
        # no good way to test the github api?
        # https://docs.github.com/en/rest/guides/getting-started-with-the-rest-api
        response = requests.get(urljoin(hosting_service.api_url, "zen"))
        if response.ok:
            return True
        return False

    @classmethod
    def test_hoster_is_valid(cls, hosting_service: HostingService):
        """
        check if a hosting service is valid by checking http responses
        """
        hosting_service_tests = {
            HOST_TYPE_GITEA: HostingServiceValidator._is_gitea_hoster,
            HOST_TYPE_GITHUB: HostingServiceValidator._is_github_hoster,
            HOST_TYPE_GITLAB: HostingServiceValidator._is_gitlab_hoster,
        }
        test_function = hosting_service_tests[hosting_service.type]
        is_valid = test_function(hosting_service)
        if not is_valid:
            logger.warning(f"negative validation for {hosting_service}")

        return is_valid
