import json
import logging
from crawler_controller import db

logger = logging.getLogger(__name__)

class Platform(db.Model):
    __tablename__ = 'platforms'
    id = db.Column(db.Integer, primary_key=True)
    platform_type = db.Column(db.String(128))
    base_url = db.Column(db.String(128))
    state = db.Column(db.String(1024))

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

