import time
import logging
from typing import Dict, Union, List

from hubgrep_indexer.lib.block import Block

logger = logging.getLogger(__name__)


class AbstractStateManager:
    """
    Base class for state managers.
    """

    def __init__(self, batch_size=1000, block_timeout=1000):
        self.batch_size = batch_size  # block size for a crawler
        self.block_timeout = block_timeout  # seconds

    def init_app(self, *args, **kwargs):
        pass

    def get_state_dict(self, hoster_prefix: str) -> Dict:
        return dict(
            highest_block_repo_id=self.get_highest_block_repo_id(hoster_prefix),
            highest_confirmed_repo_id=self.get_highest_confirmed_block_repo_id(hoster_prefix),
            empty_results_count=self.get_empty_results_counter(hoster_prefix),
            run_created_ts=self.get_run_created_ts(hoster_prefix),
            run_is_finished=self.get_has_run_hit_end(hoster_prefix),
        )

    def get_highest_block_repo_id(self, hoster_prefix: str) -> int:
        """
        The highest (last) repo_id we have tried asking for,
        but do not know for sure exist.
        """
        raise NotImplementedError

    def set_highest_block_repo_id(self, hoster_prefix: str, repo_id):
        """
        The highest (last) repo_id we have tried asking for,
        but do not know for sure exist.
        """
        raise NotImplementedError

    def get_highest_confirmed_block_repo_id(self, hoster_prefix: str) -> int:
        """
        The highest (last) repo_id we have received from crawlers,
        guaranteeing its existence.
        """
        raise NotImplementedError

    def set_highest_confirmed_block_repo_id(self, hoster_prefix: str, repo_id):
        """
        The highest (last) repo_id we have received from crawlers,
        guaranteeing its existence.
        """
        raise NotImplementedError

    def set_empty_results_counter(self, hoster_prefix: str, count: int):
        raise NotImplementedError

    def get_empty_results_counter(self, hoster_prefix: str) -> int:
        raise NotImplementedError

    def increment_empty_results_counter(self, hoster_prefix: str, amount: int = 1):
        prev = self.get_empty_results_counter(hoster_prefix=hoster_prefix)
        self.set_empty_results_counter(hoster_prefix=hoster_prefix, count=prev + amount)

    def push_new_block(self, hoster_prefix: str, block: Block) -> None:
        raise NotImplementedError

    def _delete_block(self, hoster_prefix: str, block_uid: str) -> Block:
        """Deletes from state and returns the deleted Block."""
        raise NotImplementedError

    def get_blocks_dict(self, hoster_prefix: str) -> Dict[str, Block]:
        """Get all blocks as a dict accessed by their id."""
        raise NotImplementedError

    def get_blocks_list(self, hoster_prefix: str) -> List[Block]:
        """Get all blocks in a list."""
        raise NotImplementedError

    def get_block(self, hoster_prefix: str, block_uid: str) -> Block:
        """Return an existing Block or None"""
        blocks = self.get_blocks_dict(hoster_prefix=hoster_prefix)
        return blocks.get(block_uid, None)

    def update_block(self, hoster_prefix: str, block: Block):
        """Store changes applied to a block."""
        raise NotImplementedError

    def finish_block(self, hoster_prefix: str, block_uid: str):
        """Cleanup after a block is considered completed."""
        return self._delete_block(hoster_prefix, block_uid)

    def set_run_created_ts(self, hoster_prefix: str, timestamp: float = None):
        """Set a timestamp for when a run was created. No value or None will use time.time()."""
        raise NotImplementedError

    def get_run_created_ts(self, hoster_prefix) -> float:
        """
        When was the current run created?
        Defaults to 0 if it never ran
        """
        raise NotImplementedError

    def _reset_blocks(self, hoster_prefix: str):
        for block in self.get_blocks_list(hoster_prefix):
            self._delete_block(hoster_prefix, block_uid=block.uid)

    def reset(self, hoster_prefix: str):
        """
        Reset state under a specific prefix
        (i.e. one gitea instance, but not the rest).
        """
        logger.warning(f"reset state for hoster: {hoster_prefix}")
        self.set_run_created_ts(hoster_prefix, None)
        self.set_has_run_hit_end(hoster_prefix, False)
        self.set_highest_block_repo_id(hoster_prefix, 0)
        self.set_highest_confirmed_block_repo_id(hoster_prefix, 0)
        self.set_empty_results_counter(hoster_prefix, 0)
        self._reset_blocks(hoster_prefix)

    def finish_run(self, hoster_prefix: str):
        """Wrap up and end the current run."""
        logger.warning(f"hoster_prefix: {hoster_prefix} was finished, resetting for a new run!")
        self.reset(hoster_prefix=hoster_prefix)

    def set_has_run_hit_end(self, hoster_prefix: str, has_hit_end: bool):
        raise NotImplementedError

    def get_has_run_hit_end(self, hoster_prefix: str) -> bool:
        raise NotImplementedError

    def get_next_block(self, hoster_prefix: str) -> Block:
        """
        Return the next new block.
        """
        if self.get_has_run_hit_end(hoster_prefix):
            logger.warning(f"{hoster_prefix} - hoster was finished, resetting for a new run!")
            self.finish_run(hoster_prefix)
        highest_block_repo_id = self.get_highest_block_repo_id(hoster_prefix)
        from_id = highest_block_repo_id + 1
        to_id = highest_block_repo_id + self.batch_size

        run_created_ts = self.get_run_created_ts(hoster_prefix)
        if not run_created_ts:
            self.set_run_created_ts(hoster_prefix)
            run_created_ts = self.get_run_created_ts(hoster_prefix)

        block = Block.new(run_created_ts=run_created_ts, from_id=from_id, to_id=to_id)
        self.push_new_block(hoster_prefix, block)
        self.set_highest_block_repo_id(hoster_prefix, block.to_id)
        return block

    def get_timed_out_block(self, hoster_prefix: str, timestamp_now=None) -> Union[Block, None]:
        """
        Try to get a block we didnt receive an answer for.

        timestamp_now: use a timestamp instead of time.time()
        (useful for testing (...and time travel?))
        """
        if not timestamp_now:
            timestamp_now = time.time()

        for block in self.get_blocks_list(hoster_prefix):
            age = timestamp_now - block.attempts_at[-1]
            if age > self.block_timeout:
                block.attempts_at.append(timestamp_now)
                self.update_block(hoster_prefix=hoster_prefix, block=block)
                return block
        return None

    def set_machine_api_key(self, hosting_service_id: str, machine_id: str, api_key: str):
        """ Attach an api_key to a machine_id. """
        raise NotImplementedError

    def get_machine_api_key(self, hosting_service_id: str, machine_id: str) -> str:
        """ Get an active api_key attached to a machine_id. """
        raise NotImplementedError

    def get_machine_id_by_api_key(self, hosting_service_id: str, api_key: str):
        """ Reverse lookup; get the machine_id attached to a api_key. """
        raise NotImplementedError

    def remove_machine_api_key(self, hosting_service_id: str, api_key: str) -> Union[str, None]:
        """
        Unlock an api_key from being attached to x machine_id.

        Return machine_id for a released api_key, or None if it wasn't attached.
        """
        raise NotImplementedError

    def is_api_key_active(self, hosting_service_id: str, api_key: str) -> bool:
        """ Query if an api_key is currently attached to a machine_id. """
        raise NotImplementedError
