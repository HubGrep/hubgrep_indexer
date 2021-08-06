import logging
import time
import json
import uuid
from typing import List
from flask import url_for

from hubgrep_indexer.constants import BLOCK_STATUS_CREATED, BLOCK_STATUS_READY, BLOCK_STATUS_SLEEP

logger = logging.getLogger(__name__)


class Block:
    """
    A "block" is a range of repository ID's to be crawled as a batch job.
    """
    uid: str
    run_created_ts: float
    from_id: int
    to_id: int
    ids: List[int]
    attempts_at: List[float]
    status: str
    callback_url: str = None
    _hosting_service_dict: dict = None

    def __init__(self):
        self.uid = uuid.uuid4().hex
        self.attempts_at = []
        self.status = BLOCK_STATUS_CREATED

    @classmethod
    def new(cls, from_id: int, to_id: int, run_created_ts: float = None, ids: List[int] = None):
        block = Block()
        block.from_id = from_id
        block.to_id = to_id
        block.ids = ids
        block.attempts_at.append(time.time())
        block.run_created_ts = run_created_ts
        return block

    @property
    def hosting_service(self) -> dict:
        return self._hosting_service_dict

    @hosting_service.setter
    def hosting_service(self, hosting_service_dict: dict):
        self._hosting_service_dict = hosting_service_dict
        self.callback_url = self._get_callback_url(hosting_service_dict=hosting_service_dict)
        self.status = BLOCK_STATUS_READY

    def _get_callback_url(self, hosting_service_dict: dict) -> str:
        return url_for(
            "api.add_repos",
            hosting_service_id=hosting_service_dict["id"],
            block_uid=self.uid,
            _external=True
        )

    @classmethod
    def from_dict(cls, d: dict):
        block = Block()
        block.uid = d["uid"]
        block.from_id = d["from_id"]
        block.to_id = d["to_id"]
        block.ids = d.get("ids", None)
        block.attempts_at = d["attempts_at"]
        block.status = d["status"]
        block.run_created_ts = d["run_created_ts"]
        hosting_service_dict = d.get("hosting_service", False)
        if hosting_service_dict:
            block.hosting_service = hosting_service_dict
        return block

    @classmethod
    def from_json(cls, j: str) -> "Block":
        d = json.loads(j)
        return cls.from_dict(d)

    def to_dict(self) -> dict:
        return dict(
            uid=self.uid,
            from_id=self.from_id,
            to_id=self.to_id,
            ids=self.ids,
            attempts_at=self.attempts_at,
            status=self.status,
            run_created_ts=self.run_created_ts,
            hosting_service=self.hosting_service,
            callback_url=self.callback_url
        )

    def to_json(self):
        d = self.to_dict()
        return json.dumps(d)

    @classmethod
    def get_sleep_dict(cls) -> dict:
        return {
            "status": BLOCK_STATUS_SLEEP,
            "retry_at": time.time() + 300,  # 5min from now
        }

    def __repr__(self) -> str:
        range_suffix = f"{self.from_id}-{self.to_id}"
        if isinstance(self.ids, list) and len(self.ids) > 0:
            range_suffix = f"cached-ids:{self.ids[0]}-{self.ids[-1]}"
        return f"<Block_{self.uid}-{self.status}:{range_suffix}>"
