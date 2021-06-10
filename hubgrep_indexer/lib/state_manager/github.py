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

    @classmethod
    def from_json(cls, j: str):
        d = json.loads(j)
        return cls.from_dict(d)

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

    def to_json(self):
        d = self.to_dict()
        return json.dumps(d)


class StateManager:
    """
    base class for state managers
    """

    def __init__(self):
        self.batch_size = 1000  # block size for a crawler
        self.block_timeout = 1000  # seconds

    def get_current_highest_repo_id(self) -> int:
        raise NotImplementedError

    def push_new_block(self, block: Block) -> None:
        raise NotImplementedError

    def delete_block(self, block_uid: str) -> Block:
        """
        deletes from state and returns block with block_id
        """
        raise NotImplementedError

    def get_blocks(self) -> Dict[Block]:
        raise NotImplementedError

    def set_current_highest_repo_id(self, highest_repo_id):
        raise NotImplementedError

    def finish_block(self, block_uid: str):
        block = self.delete_block(block_uid)
        highest_repo_id = self.get_current_highest_repo_id()
        if highest_repo_id < block.to_id:
            self.set_current_highest_repo_id(highest_repo_id)

    def get_next_block(self):
        current_highest_repo_id = self.get_current_highest_repo_id()
        from_id = current_highest_repo_id + 1
        to_id = current_highest_repo_id + self.batch_size

        block = Block.new(from_id=from_id, to_id=to_id)
        self.push_new_block(block)

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

        for uid, block in self.get_blocks():
            if timestamp_now - block.attempts_at[-1] < self.block_timeout:
                return block
        return None


class LocalStateManager(StateManager):
    """
    local state manager

    stored in memory, at runtime
    """

    def __init__(self):
        super().__init__()

        # {uuid: block}
        self.blocks: Dict[str, Block] = {}
        self.current_highest_repo_id = 0  # new blocks start here

    def push_new_block(self, block: Block) -> None:
        self.blocks[block.uid] = block

    def get_blocks(self) -> Dict[Block]:
        return self.blocks

    def set_current_highest_repo_id(self, highest_repo_id) -> None:
        self.current_highest_repo_id = highest_repo_id

    def delete_block(self, block_uid: str) -> Block:
        return self.blocks.pop(block_uid)

    def get_current_highest_repo_id(self) -> int:
        return self.current_highest_repo_id


class RedisStateManager(StateManager):
    """
    redis state manager
    """

    def __init__(self):
        super().__init__()
        self.redis = redis.client()

        self.block_map_key = "blocks"
        self.highest_repo_id_key = "highest_repo_id"

    def set_current_highest_repo_id(self, highest_repo_id):
        self.redis.set(self.highest_repo_id_key, highest_repo_id)

    def get_current_highest_repo_id(self):
        return self.redis.get(self.highest_repo_id_key) or 0

    def push_new_block(self, block: Block):
        self.redis.hset(self.block_map_key, block.uid, block.to_dict())

    def delete_block(self, block_uid):
        block = self.redis.hget(self.block_map_key, block_uid)
        self.redis.hdel(self.block_map_key, block_uid)
        return block

    def get_blocks(self):
        block_jsons = self.redis.hgetall(self.block_map_key)
        blocks = {}
        for block_json in block_jsons:
            block = Block.from_json(block_json)
            blocks[block.uid] = block
        return blocks
