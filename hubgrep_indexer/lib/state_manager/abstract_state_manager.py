import json
import time
import uuid
import logging

from typing import Dict

logger = logging.getLogger(__name__)


class Block:
    """
    A "block" is a range of repository ID's to be crawled as a batch job.
    """

    def __init__(self):
        self.uid = uuid.uuid4().hex
        self.run_created_ts = None
        self.from_id = None
        self.to_id = None
        # todo: add specific "ids" when we already know they exist (github)
        self.ids = None
        self.attempts_at = []
        self.status = ""

    @classmethod
    def new(cls, from_id, to_id, run_created_ts=None, ids=None):
        block = Block()
        block.from_id = from_id
        block.to_id = to_id
        block.ids = ids
        block.attempts_at.append(time.time())
        block.run_created_ts = run_created_ts
        return block

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
            ids=self.ids,
            attempts_at=self.attempts_at,
            status=self.status,
            run_created_ts=self.run_created_ts,
        )

    def to_json(self):
        d = self.to_dict()
        return json.dumps(d)

    def __repr__(self):
        # TODO new repr as we have either from/to_id and/or ids
        return f"<Block {self.uid}: {self.from_id}-{self.to_id}>"


class AbstractStateManager:
    """
    Base class for state managers.
    """

    def __init__(self, batch_size=1000, block_timeout=1000):
        self.batch_size = batch_size  # block size for a crawler
        self.block_timeout = block_timeout  # seconds

    def get_state_dict(self, hoster_prefix: str) -> Dict:
        return dict(
            highest_block_repo_id=self.get_highest_block_repo_id(hoster_prefix),
            highest_confirmed_repo_id=self.get_highest_confirmed_repo_id(hoster_prefix),
            empty_results_count=self.get_empty_results_counter(hoster_prefix),
            run_created_ts=self.get_run_created_ts(hoster_prefix),
            run_is_finished=self.get_run_is_finished(hoster_prefix),
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

    def get_highest_confirmed_repo_id(self, hoster_prefix: str) -> int:
        """
        The highest (last) repo_id we have received from crawlers,
        guaranteeing its existence.
        """
        raise NotImplementedError

    def set_highest_confirmed_repo_id(self, hoster_prefix: str, repo_id):
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

    def get_blocks(self, hoster_prefix: str) -> Dict[str, Block]:
        raise NotImplementedError

    def finish_block(self, hoster_prefix: str, block_uid: str):
        """Cleanup after a block is considered completed."""
        return self._delete_block(hoster_prefix, block_uid)

    def set_run_created_ts(self, hoster_prefix: str, timestamp: float = None):
        raise NotImplementedError

    def get_run_created_ts(self, hoster_prefix) -> float:
        """
        When was the current run created?
        Defaults to 0 if it never ran
        """
        raise NotImplementedError

    def _reset_blocks(self, hoster_prefix: str):
        for block in list(self.get_blocks(hoster_prefix).values())[:]:
            self._delete_block(hoster_prefix, block_uid=block.uid)

    def reset(self, hoster_prefix: str):
        """
        Reset state under a specific prefix
        (i.e. one gitea instance, but not the rest).
        """
        logger.warning(f"reset state for hoster: {hoster_prefix}")
        self.set_run_created_ts(hoster_prefix, None)
        self.set_run_is_finished(hoster_prefix, False)
        self.set_highest_block_repo_id(hoster_prefix, 0)
        self.set_highest_confirmed_repo_id(hoster_prefix, 0)
        self._reset_blocks(hoster_prefix)

    def finish_run(self, hoster_prefix: str):
        """
        after we have finished crawling this hoster,
        set run_is_finished
        """
        self.set_run_is_finished(hoster_prefix, True)

    def set_run_is_finished(self, hoster_prefix: str, is_finished: bool):
        raise NotImplementedError

    def get_run_is_finished(self, hoster_prefix: str) -> bool:
        raise NotImplementedError

    def get_next_block(self, hoster_prefix: str) -> Block:
        """
        Return the next new block.
        """
        if self.get_run_is_finished(hoster_prefix):
            logger.warning("hoster was finished, resetting for a new run!")
            self.reset(hoster_prefix)
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

    def get_timed_out_block(self, hoster_prefix: str, timestamp_now=None) -> Block:
        """
        Try to get a block we didnt receive an answer for.

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


class LocalStateManager(AbstractStateManager):
    """
    Local state manager, using plain dicts for storage.

    Stored in memory, at runtime, as a convenience class for testing without overhead.
    """

    def __init__(self):
        super().__init__()

        #
        # blocks: {"hoster_prefix": {"uuid": block}
        # current_highest_repo_ids = {"hoster_prefix" : {current_highest_repo_id": 0}
        self.blocks: Dict[str, Dict[str, Block]] = {}
        self.current_highest_repo_ids = {}
        self.highest_confirmed_repo_ids = {}
        self.empty_results_counter = {}
        self.run_created_timestamps = {}

        # bools, if the run, started at created_at is finished
        self.run_is_finished = False

    def push_new_block(self, hoster_prefix, block: Block) -> None:
        if not self.blocks.get(hoster_prefix, False):
            self.blocks[hoster_prefix] = {}
        self.blocks[hoster_prefix][block.uid] = block

    def get_blocks(self, hoster_prefix) -> Dict[str, Block]:
        return self.blocks.get(hoster_prefix, {})

    def set_highest_block_repo_id(self, hoster_prefix, repo_id) -> None:
        self.current_highest_repo_ids[hoster_prefix] = repo_id

    def get_highest_block_repo_id(self, hoster_prefix) -> int:
        if not self.current_highest_repo_ids.get(hoster_prefix, False):
            self.current_highest_repo_ids[hoster_prefix] = 0
        return self.current_highest_repo_ids[hoster_prefix]

    def _delete_block(self, hoster_prefix, block_uid: str) -> Block:
        hoster_blocks = self.blocks[hoster_prefix]
        block = hoster_blocks.pop(block_uid)
        return block

    def set_highest_confirmed_repo_id(self, hoster_prefix: str, repo_id: int):
        self.highest_confirmed_repo_ids[hoster_prefix] = repo_id

    def get_highest_confirmed_repo_id(self, hoster_prefix: str) -> int:
        if not self.highest_confirmed_repo_ids.get(hoster_prefix, False):
            self.highest_confirmed_repo_ids[hoster_prefix] = 0
        return self.highest_confirmed_repo_ids[hoster_prefix]

    def set_run_created_ts(self, hoster_prefix, timestamp: float = None):
        if timestamp is None:
            timestamp = time.time()
        self.run_created_timestamps[hoster_prefix] = timestamp

    def get_run_created_ts(self, hoster_prefix):
        if not self.run_created_timestamps.get(hoster_prefix, False):
            self.set_run_created_ts(hoster_prefix, 0)
        return self.run_created_timestamps[hoster_prefix]

    def get_run_is_finished(self, hoster_prefix) -> bool:
        return self.run_is_finished.get(hoster_prefix, False)

    def set_run_is_finished(self, hoster_prefix, is_finished: bool):
        self.run_is_finished[hoster_prefix] = is_finished

    def set_empty_results_counter(self, hoster_prefix: str, count: int):
        self.empty_results_counter[hoster_prefix] = count

    def get_empty_results_counter(self, hoster_prefix: str) -> int:
        if not self.empty_results_counter.get(hoster_prefix, False):
            self.set_empty_results_counter(hoster_prefix, 0)
        return self.empty_results_counter[hoster_prefix]
