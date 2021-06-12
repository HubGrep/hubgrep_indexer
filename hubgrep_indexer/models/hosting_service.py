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

    # individual config for a specific service (eg. api-key)
    # could be json, but thats only supported for postgres
    config = db.Column(db.Text)

    def get_service_label(self):
        return re.split("//", self.landingpage_url)[1].rstrip("/")

    def to_dict(self):
        return dict(
            id=self.id,
            type=self.type,
            landingpage_url=self.landingpage_url,
            api_url=self.api_url,
            export_url=self.export_url,
            export_date=self.export_date,
            #config=self.config,
            service_label=self.get_service_label(),
        )

    @classmethod
    def from_dict(cls, d: dict):
        hosting_service = HostingService()
        hosting_service.type = d["type"]
        hosting_service.landingpage_url = d["landingpage_url"]
        hosting_service.api_url = d["api_url"]
        hosting_service.config = d["config"]

        return hosting_service
