import asyncio
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import duckdb
import gradio as gr
import httpx

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel


# ============================================================
# CONFIG
# ============================================================

PARALLELISM = int(os.environ.get("ICMR_PARALLEL", "2"))
THREADS_PER_CONN = int(os.environ.get("ICMR_THREADS_PER_CONN", "2"))

pool = ThreadPoolExecutor(
    max_workers=PARALLELISM,
    thread_name_prefix="duck"
)


# ============================================================
# FASTAPI
# ============================================================

fastapi_app = FastAPI(
    title="Search API",
    description="Authorized synthetic-data search API"
)


# ============================================================
# DUCKDB CONNECTION POOL
# ============================================================

_conns = []
_conns_lock = threading.Lock()
_thread_local = threading.local()


def _new_conn():
    con = duckdb.connect()

    con.execute(
        f"SET threads = {THREADS_PER_CONN}"
    )

    return con


def _thread_id():
    tid = getattr(
        _thread_local,
        "id",
        None
    )

    if tid is None:

        with _conns_lock:

            tid = len(_conns)

            _thread_local.id = tid

    return tid


def _get_conn():

    ident = _thread_id()

    with _conns_lock:

        while len(_conns) <= ident:

            _conns.append(
                _new_conn()
            )

    return _conns[ident]


# ============================================================
# SYNTHETIC TEST DATA
# ============================================================

TEST_DATA = [
    {
        "name": "Test User",
        "fathersName": "Test Father",
        "phoneNumber": "1234567890",
        "aadharNumber": "000000000000",
        "otherNumber": "",
        "address": "Synthetic Test Address",
        "district": "Test District",
        "pincode": "000000",
        "state": "Test State",
        "town": "Test Town",
        "source": "synthetic"
    },
    {
        "name": "Demo User",
        "fathersName": "Demo Father",
        "phoneNumber": "9876543210",
        "aadharNumber": "111111111111",
        "otherNumber": "",
        "address": "Demo Test Address",
        "district": "Demo District",
        "pincode": "111111",
        "state": "Demo State",
        "town": "Demo Town",
        "source": "synthetic"
    }
]


# ============================================================
# SEARCH
# ============================================================

def search_test
