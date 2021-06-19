import uuid

from .abstract_state_manager import StateManager, Block

import redis


class RedisStateManager(StateManager):
    """
    redis state manager
    """

    def __init__(self):
        super().__init__()
        self.redis = redis.from_url("redis://localhost")

        self.run_uid_key = "run_uid"
        self.block_map_key = "blocks"
        self.highest_block_repo_id_key = "highest_block_repo_id"
        self.highest_confirmed_repo_id_key = "highest_confirmed_repo_id"
        self.empty_results_counter_key = "empty_results_counter"

    def set_highest_block_repo_id(self, hoster_prefix: str, repo_id: int):
        redis_key = f"{hoster_prefix}:{self.highest_block_repo_id_key}"
        self.redis.set(redis_key, repo_id)

    def get_highest_block_repo_id(self, hoster_prefix: str) -> int:
        redis_key = f"{hoster_prefix}:{self.highest_block_repo_id_key}"
        highest_repo_id_str: str = self.redis.get(redis_key)
        if not highest_repo_id_str:
            highest_repo_id = 0
        else:
            highest_repo_id = int(highest_repo_id_str)
        return highest_repo_id

    def set_highest_confirmed_repo_id(self, hoster_prefix: str, repo_id: int):
        redis_key = f"{hoster_prefix}:{self.highest_confirmed_repo_id_key}"
        self.redis.set(redis_key, repo_id)

    def get_highest_confirmed_repo_id(self, hoster_prefix: str) -> int:
        redis_key = f"{hoster_prefix}:{self.highest_confirmed_repo_id_key}"
        repo_id_str: str = self.redis.get(redis_key)
        if not repo_id_str:
            highest_repo_id = 0
        else:
            highest_repo_id = int(repo_id_str)
        return highest_repo_id

    def set_empty_results_counter(self, hoster_prefix: str, count: int):
        redis_key = f"{hoster_prefix}:{self.empty_results_counter_key}"
        self.redis.set(redis_key, count)

    def get_empty_results_counter(self, hoster_prefix: str) -> int:
        redis_key = f"{hoster_prefix}:{self.empty_results_counter_key}"
        if not self.redis.get(redis_key):
            self.set_empty_results_counter(hoster_prefix, 0)
        counter_str: str = self.redis.get(redis_key)
        return int(counter_str)

    def push_new_block(self, hoster_prefix, block: Block):
        redis_key = f"{hoster_prefix}:{self.block_map_key}"
        self.redis.hset(redis_key, block.uid, block.to_json())

    def set_run_uid(self, hoster_prefix):
        run_uid = uuid.uuid4().hex
        redis_key = f"{hoster_prefix}:{self.run_uid_key}"
        self.redis.set(redis_key, run_uid)

    def get_run_uid(self, hoster_prefix):
        redis_key = f"{hoster_prefix}:{self.run_uid_key}"
        if not self.redis.get(redis_key):
            self.set_run_uid(hoster_prefix)
        run_uid_bytes: bytes = self.redis.get(redis_key)
        return run_uid_bytes.decode()

    def _delete_block(self, hoster_prefix, block_uid):
        redis_key = f"{hoster_prefix}:{self.block_map_key}"
        block = self.redis.hget(redis_key, block_uid)
        self.redis.hdel(redis_key, block_uid)
        return block

    def get_blocks(self, hoster_prefix):
        redis_key = f"{hoster_prefix}:{self.block_map_key}"
        block_jsons = self.redis.hgetall(redis_key)
        blocks = {}
        for block_json in block_jsons.values():
            block = Block.from_json(block_json)
            blocks[block.uid] = block
        return blocks
