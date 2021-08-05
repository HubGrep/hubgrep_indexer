import time
import logging

from hubgrep_indexer.lib.state_manager.abstract_state_manager import AbstractStateManager
from hubgrep_indexer.lib.block import Block

import redis
import redislite

logger = logging.getLogger(__name__)


class RedisStateManager(AbstractStateManager):
    """
    redis state manager
    """

    def __init__(self):
        super().__init__()
        self.redis = None

        self.lock_key = "lock"

        self.run_created_ts_key = "run_created_ts"
        self.block_map_key = "blocks"
        self.highest_block_repo_id_key = "highest_block_repo_id"
        self.highest_confirmed_block_repo_id_key = "highest_confirmed_block_repo_id"
        self.empty_results_counter_key = "empty_results_counter"
        self.run_is_finished_key = "run_is_finished"
        self.machine_api_key_key = "machine_api_key"
        self.active_api_keys_key = "active_api_key"

    def init_app(self, app, *args, **kwargs):
        redis_url = app.config["REDIS_URL"]
        if redis_url:
            self.redis = redis.from_url(redis_url)
        else:
            self.redis = redislite.Redis()

    @classmethod
    def _get_redis_key(cls, key_prefix: str, key: str):
        return f"{key_prefix}:{key}"

    def get_lock(self, hoster_prefix: str):
        redis_key = self._get_redis_key(hoster_prefix, self.lock_key)
        lock = self.redis.lock(redis_key)
        return lock

    def set_highest_block_repo_id(self, hoster_prefix: str, repo_id: int):
        redis_key = self._get_redis_key(hoster_prefix, self.highest_block_repo_id_key)
        self.redis.set(redis_key, repo_id)

    def get_highest_block_repo_id(self, hoster_prefix: str) -> int:
        redis_key = self._get_redis_key(hoster_prefix, self.highest_block_repo_id_key)
        highest_repo_id_str: str = self.redis.get(redis_key)
        if not highest_repo_id_str:
            highest_repo_id = 0
        else:
            highest_repo_id = int(highest_repo_id_str)
        return highest_repo_id

    def set_highest_confirmed_block_repo_id(self, hoster_prefix: str, repo_id: int):
        redis_key = self._get_redis_key(
            hoster_prefix, self.highest_confirmed_block_repo_id_key
        )
        self.redis.set(redis_key, repo_id)

    def get_highest_confirmed_block_repo_id(self, hoster_prefix: str) -> int:
        redis_key = self._get_redis_key(
            hoster_prefix, self.highest_confirmed_block_repo_id_key
        )
        repo_id_str: str = self.redis.get(redis_key)
        if not repo_id_str:
            highest_repo_id = 0
        else:
            highest_repo_id = int(repo_id_str)
        return highest_repo_id

    def set_empty_results_counter(self, hoster_prefix: str, count: int):
        redis_key = self._get_redis_key(hoster_prefix, self.empty_results_counter_key)
        self.redis.set(redis_key, count)

    def get_empty_results_counter(self, hoster_prefix: str) -> int:
        redis_key = self._get_redis_key(hoster_prefix, self.empty_results_counter_key)
        if not self.redis.get(redis_key):
            self.set_empty_results_counter(hoster_prefix, 0)
        counter_str: str = self.redis.get(redis_key)
        return int(counter_str)

    def push_new_block(self, hoster_prefix: str, block: Block):
        redis_key = self._get_redis_key(hoster_prefix, self.block_map_key)
        self.redis.hset(redis_key, block.uid, block.to_json())

    def set_run_created_ts(self, hoster_prefix: str, timestamp: float = None):
        if timestamp is None:
            timestamp = time.time()
        redis_key = self._get_redis_key(hoster_prefix, self.run_created_ts_key)
        self.redis.set(redis_key, timestamp)

    def get_run_created_ts(self, hoster_prefix: str):
        redis_key = self._get_redis_key(hoster_prefix, self.run_created_ts_key)
        if not self.redis.get(redis_key):
            self.set_run_created_ts(hoster_prefix, 0)
        return float(self.redis.get(redis_key))

    def get_is_run_finished(self, hoster_prefix: str) -> bool:
        redis_key = self._get_redis_key(hoster_prefix, self.run_is_finished_key)
        is_finished_str = self.redis.get(redis_key)
        if is_finished_str:
            is_finished_str = int(is_finished_str)
        return bool(is_finished_str)

    def set_is_run_finished(self, hoster_prefix: str, is_finished: bool):
        redis_key = self._get_redis_key(hoster_prefix, self.run_is_finished_key)
        self.redis.set(redis_key, int(is_finished))

    def update_block(self, hoster_prefix: str, block: Block):
        """Store changes applied to a block."""
        redis_key = self._get_redis_key(hoster_prefix, self.block_map_key)
        old_block = self.redis.hget(redis_key, block.uid)
        if old_block:
            # only update existing blocks
            self.redis.hset(redis_key, block.uid, block.to_json())
        else:
            logger.info(
                f"(ignoring call) attempted to update non-existing block state, uid: {block.uid}"
            )

    def _delete_block(self, hoster_prefix: str, block_uid: str):
        redis_key = self._get_redis_key(hoster_prefix, self.block_map_key)
        block = self.redis.hget(redis_key, block_uid)
        self.redis.hdel(redis_key, block_uid)
        return block

    def get_blocks(self, hoster_prefix: str):
        redis_key = self._get_redis_key(hoster_prefix, self.block_map_key)
        block_jsons = self.redis.hgetall(redis_key)
        blocks = {}
        for block_json in block_jsons.values():
            block = Block.from_json(block_json)
            blocks[block.uid] = block
        return blocks

    def get_machine_api_key(self, machine_id: str) -> str:
        machine_key = self._get_redis_key(machine_id, self.machine_api_key_key)
        api_key = self.redis.get(machine_key)
        if api_key:
            api_key = api_key.decode("utf-8")
        return api_key

    def set_machine_api_key(self, machine_id: str, api_key: str):
        # store the api_key behind a machine_id key
        machine_key = self._get_redis_key(machine_id, self.machine_api_key_key)
        self.redis.set(machine_key, api_key)

        # register all api_keys which are in use (by storing the machine_key attached to it)
        api_key_key = self._get_redis_key(api_key, self.active_api_keys_key)
        self.redis.set(api_key_key, machine_key)

    def remove_active_api_key(self, api_key: str):
        api_key_key = self._get_redis_key(api_key, self.active_api_keys_key)
        machine_key = self.redis.get(api_key_key)
        self.redis.delete(api_key_key, machine_key)

    def is_api_key_active(self, api_key: str) -> bool:
        api_key_key = self._get_redis_key(api_key, self.active_api_keys_key)
        return bool(self.redis.exists(api_key_key))
