import re
import json
import logging
from hubgrep_indexer import db

logger = logging.getLogger(__name__)


class HostingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("hosting_services", lazy=True))

    type = db.Column(db.String(80), nullable=False)

    # main instance website
    landingpage_url = db.Column(db.String(500))

    # should this be unique, or can we use it to store multiple
    # api keys for a backend?
    api_url = db.Column(db.String(500), unique=True, nullable=False)

    # individual config for a specific service (eg. api-key)
    # could be json, but thats only supported for postgres
    config = db.Column(db.Text)

    # frontend label
    label = db.Column(db.String(80))

    state = db.Column(db.String(1024))

    def set_service_label(self):
        self.label = re.split("//", self.landingpage_url)[1].rstrip("/")

    def update_state(self, state: dict):
        if self.state:
            new_state = {**json.loads(self.state), **state}
        else:
            new_state = state
        self.state = json.dumps(new_state)
        logger.info(f'updating state to {new_state}')
        db.session.add(self)
        db.session.commit()

    def get_state(self):
        return json.loads(self.state)

