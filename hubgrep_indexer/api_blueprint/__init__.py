from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api/v1")

from hubgrep_indexer.api_blueprint.hosters import hosters
from hubgrep_indexer.api_blueprint.add_repos import add_repos
from hubgrep_indexer.api_blueprint.get_block import get_block, get_loadbalanced_block

"""
# memleak tooling :)

import logging
logger = logging.getLogger(__name__)

import gc
import os
import tracemalloc

import psutil
process = psutil.Process(os.getpid())
tracemalloc.start()
s = None


@api.route('/memory')
def print_memory():
    return {'memory': process.memory_info().rss}


@api.route("/snapshot")
def snap():
    global s
    if not s:
        s = tracemalloc.take_snapshot()
        return "taken snapshot\n"
    else:
        lines = []
        top_stats = tracemalloc.take_snapshot().compare_to(s, 'lineno')
        for stat in top_stats[:15]:
            lines.append(str(stat))
        return "\n".join(lines)
"""
