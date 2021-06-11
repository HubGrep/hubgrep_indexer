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

        if not self.redis.get(self.highest_repo_id_key):
            self.set_current_highest_repo_id(0)


    def set_current_highest_repo_id(self, highest_repo_id):
        self.redis.set(self.highest_repo_id_key, highest_repo_id)

    def get_current_highest_repo_id(self):
        return int(self.redis.get(self.highest_repo_id_key)) or 0

    def push_new_block(self, block: Block):
        self.redis.hset(self.block_map_key, block.uid, block.to_dict())

    def delete_block(self, block_uid):
        block = self.redis.hget(self.block_map_key, block_uid)
        self.redis.hdel(self.block_map_key, block_uid)
        return block

    def get_blocks(self):
        block_jsons = self.redis.hgetall(self.block_map_key)
        blocks = {}
        for block_json in block_jsons.values():
            block = Block.from_json(block_json)
            blocks[block.uid] = block
        return blocks
