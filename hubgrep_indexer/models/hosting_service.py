import re
import json
import logging
from hubgrep_indexer import db

logger = logging.getLogger(__name__)


class HostingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), nullable=False)

    # main instance website
    landingpage_url = db.Column(db.String(500))

    # should this be unique, or can we use it to store multiple
    # api keys for a backend?
    api_url = db.Column(db.String(500), unique=True, nullable=False)

    export_url = db.Column(db.String(500))
    export_date = db.Column(db.DateTime(500))

    api_key = db.Column(db.String(500), nullable=True)

    def get_request_headers(self):
        """
        get request headers for this service
        """
        if self.type == "github":
            return dict(access_token=self.api_key)
        elif self.type == "gitea":
            return {}
        elif self.type == "gitlab":
            return {"PRIVATE-TOKEN": self.api_key}
        else:
            logger.error(f"unknown hoster {self.type}!")
            return {}

    def get_service_label(self):
        return re.split("//", self.landingpage_url)[1].rstrip("/")

    def to_dict(self, include_secrets=False):
        d = dict(
            id=self.id,
            type=self.type,
            landingpage_url=self.landingpage_url,
            api_url=self.api_url,
            export_url=self.export_url,
            export_date=self.export_date,
            service_label=self.get_service_label(),
        )
        if include_secrets:
            d["request_headers"] = self.get_request_headers()
        return d

    @classmethod
    def from_dict(cls, d: dict):
        hosting_service = HostingService()
        hosting_service.type = d["type"]
        hosting_service.landingpage_url = d["landingpage_url"]
        hosting_service.api_url = d["api_url"]
        hosting_service.api_key = d["api_key"]

        return hosting_service
