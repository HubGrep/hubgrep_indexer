import json
import redis
import time
import uuid

from typing import Dict


class Block:
    """
    represents a "block" in the github repository id range

    """

    # todo: add "ids" for ranges we already know, instead of from/to_id
    #
    def __init__(self):
        self.uid = uuid.uuid4()
        self.from_id = None
        self.to_id = None
        self.attempts_at = []
        self.status = ""

    @classmethod
    def new(cls, from_id, to_id):
        block = Block()
        block.from_id = from_id
        block.to_id = to_id
        block.attempts_at.append(time.time())
        return block

    @classmethod
    def from_dict(cls, d: dict):
        block = Block()
        block.uid = d["uid"]
        block.from_id = d["from_id"]
        block.to_id = d["to_id"]
        block.attempts_at = d["attempts_at"]
        block.status = d["status"]

    def to_dict(self):
        return json.dumps(
            dict(
                uid=self.uid,
                from_id=self.from_id,
                to_id=self.to_id,
                attempts_at=self.attempts_at,
                status=self.status,
            )
        )


class GitHubStateManager:
    """
    state manager for github

    no backend yet - stored in memory, at runtime
    """

    def __init__(self):
        # {uuid: block}
        self.blocks: Dict[str, Block] = {}

        self.current_highest_repo_id = 0  # new blocks start here
        self.batch_size = 1000  # block size for a crawler
        self.block_timeout = 1000  # seconds

    def get_next_block(self):
        from_id = self.current_highest_repo_id + 1
        to_id = self.current_highest_repo_id + self.batch_size

        block = Block.new(from_id=from_id, to_id=to_id)
        self.blocks[block.uid] = block

        self.current_highest_repo_id = to_id
        return block

    def get_timed_out_block(self, timestamp_now=None):
        """
        try to get a block we didnt receive an answer for

        timestamp_now: use a timestamp instead of time.time()
        (useful for testing (...and time travel?))
        """
        if not timestamp_now:
            timestamp_now = time.time()

        for uid, block in self.blocks.items():
            if timestamp_now - block.attempts_at[-1] < self.block_timeout:
                return block
        return None

