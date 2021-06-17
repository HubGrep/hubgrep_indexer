import json
import redis
import time
import uuid

from typing import Dict, List


class Block:
    """
    represents a "block" in the github repository id range

    """

    # todo: add "ids" for ranges we already know, instead of from/to_id
    #
    def __init__(self):
        self.uid = uuid.uuid4().hex
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
        return block

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j)
        return cls.from_dict(d)

    def to_dict(self):
        return dict(
            uid=self.uid,
            from_id=self.from_id,
            to_id=self.to_id,
            attempts_at=self.attempts_at,
            status=self.status,
        )

    def to_json(self):
        d = self.to_dict()
        return json.dumps(d)

    def __repr__(self):
        return f"<Block {self.uid}: {self.from_id}-{self.to_id}>"


class StateManager:
    """
    base class for state managers
    """

    def __init__(self, batch_size=1000, block_timeout=1000):
        self.batch_size = batch_size  # block size for a crawler
        self.block_timeout = block_timeout  # seconds

    def get_current_highest_repo_id(self, hoster_prefix: str) -> int:
        raise NotImplementedError

    def push_new_block(self, hoster_prefix: str, block: Block) -> None:
        raise NotImplementedError

    def _delete_block(self, hoster_prefix: str, block_uid: str) -> Block:
        """
        deletes from state and returns block with block_id
        """
        raise NotImplementedError

    def get_blocks(self, hoster_prefix: str) -> Dict[str, Block]:
        raise NotImplementedError

    def set_current_highest_repo_id(self, hoster_prefix: str, highest_repo_id):
        raise NotImplementedError

    def finish_block(self, hoster_prefix: str, block_uid: str):
        return self._delete_block(hoster_prefix, block_uid)

    def reset(self, hoster_prefix: str):
        """
        reset state manager
        """
        self.set_current_highest_repo_id(hoster_prefix, 0)
        for block in list(self.get_blocks(hoster_prefix).values())[:]:
            print("deleting", block)
            self.delete_block(hoster_prefix, block_uid=block.uid)

    def get_next_block(self, hoster_prefix: str) -> Block:
        """
        return the next new block
        """
        current_highest_repo_id = self.get_current_highest_repo_id(hoster_prefix)
        from_id = current_highest_repo_id + 1
        to_id = current_highest_repo_id + self.batch_size

        block = Block.new(from_id=from_id, to_id=to_id)
        self.push_new_block(hoster_prefix, block)
        self.set_current_highest_repo_id(hoster_prefix, block.to_id)
        return block

    def get_timed_out_block(self, hoster_prefix: str, timestamp_now=None) -> Block:
        """
        try to get a block we didnt receive an answer for

        timestamp_now: use a timestamp instead of time.time()
        (useful for testing (...and time travel?))
        """
        if not timestamp_now:
            timestamp_now = time.time()

        for uid, block in self.get_blocks(hoster_prefix).items():
            age = timestamp_now - block.attempts_at[-1]
            if age > self.block_timeout:
                return block
        return None


class LocalStateManager(StateManager):
    """
    local state manager, using plain dicts for storage
    mostly to run tests for the StateManager code without much overhead

    stored in memory, at runtime
    """

    def __init__(self):
        super().__init__()

        #
        # blocks: {"hoster_prefix": {"uuid": block}
        # current_highest_repo_ids = {"hoster_prefix" : {current_highest_repo_id": 0}
        self.blocks: Dict[str, Dict[str, Block]] = {}
        self.current_highest_repo_ids = {}

    def push_new_block(self, hoster_prefix, block: Block) -> None:
        if not self.blocks.get(hoster_prefix, False):
            self.blocks[hoster_prefix] = {}
        self.blocks[hoster_prefix][block.uid] = block

    def get_blocks(self, hoster_prefix) -> Dict[str, Block]:
        return self.blocks.get(hoster_prefix, {})

    def set_current_highest_repo_id(self, hoster_prefix, highest_repo_id) -> None:
        self.current_highest_repo_ids[hoster_prefix] = highest_repo_id

    def delete_block(self, hoster_prefix, block_uid: str) -> Block:
        hoster_blocks = self.blocks[hoster_prefix]
        block = hoster_blocks.pop(block_uid)
        return block

    def get_current_highest_repo_id(self, hoster_prefix) -> int:
        if not self.current_highest_repo_ids.get(hoster_prefix, False):
            self.current_highest_repo_ids[hoster_prefix] = 0
        return self.current_highest_repo_ids[hoster_prefix]
