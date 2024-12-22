"""
Support for parallelisation

This always feels so much harder than it should be
"""

from __future__ import annotations

import concurrent.futures
from collections.abc import Iterable
from typing import Callable, TypeVar

import tqdm
from loguru import logger
from typing_extensions import Concatenate, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")
U = TypeVar("U")


def run_parallel(
    func_to_call: Callable[Concatenate[U, P], T],
    iterable_input: Iterable[U],
    input_desc: str,
    n_processes: int,
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[T, ...]:
    if n_processes == 1:
        logger.debug("Running serially")
        res = [
            func_to_call(inv, *args, **kwargs)
            for inv in tqdm.tqdm(iterable_input, desc=input_desc)
        ]

    else:
        logger.info(f"Submitting {input_desc} to {n_processes} parallel processes")
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=n_processes
        ) as executor:
            futures = [
                executor.submit(
                    func_to_call,
                    inv,
                    *args,
                    **kwargs,
                )
                for inv in tqdm.tqdm(
                    iterable_input, desc=f"Submitting {input_desc} to queue"
                )
            ]

            res = [
                future.result()
                for future in tqdm.tqdm(
                    concurrent.futures.as_completed(futures),
                    desc="Retrieving parallel results",
                    total=len(futures),
                )
            ]

    return tuple(res)
