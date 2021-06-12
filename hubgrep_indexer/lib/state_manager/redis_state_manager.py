from .abstract_state_manager import StateManager, Block

import redis


class RedisStateManager(StateManager):
    """
    redis state manager
    """

    def __init__(self):
        super().__init__()
        self.redis = redis.from_url("redis://localhost")

        self.block_map_key = "blocks"
        self.highest_repo_id_key = "highest_repo_id"

    def set_current_highest_repo_id(self, hoster_prefix, highest_repo_id):
        redis_key = f"{hoster_prefix}:{self.highest_repo_id_key}"
        self.redis.set(redis_key, highest_repo_id)

    def get_current_highest_repo_id(self, hoster_prefix):
        redis_key = f"{hoster_prefix}:{self.highest_repo_id_key}"
        highest_repo_id_str: str = self.redis.get(redis_key)
        if not highest_repo_id_str:
            highest_repo_id = 0
        else:
            highest_repo_id = int(highest_repo_id_str)
        return highest_repo_id

    def push_new_block(self, hoster_prefix, block: Block):
        redis_key = f"{hoster_prefix}:{self.block_map_key}"
        self.redis.hset(redis_key, block.uid, block.to_json())

    def delete_block(self, hoster_prefix, block_uid):
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
