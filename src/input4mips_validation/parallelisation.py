"""
Support for parallelisation

This always feels so much harder than it should be
"""

from __future__ import annotations

import concurrent.futures
import multiprocessing
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
    mp_context: multiprocessing.BaseContext = multiprocessing.get_context("spawn"),
    **kwargs: P.kwargs,
) -> tuple[T, ...]:
    """
    Run a function in parallel

    Yet another abstraction for this,
    because the ones we had weren't doing what we wanted.

    Parameters
    ----------
    func_to_call
        Function to call

    iterable_input
        Input with which to call the function.

    input_desc
        Description of the input (used to make the progress bars more helpful)

    n_processes
        Number of processes to use during the processing.

        If set to `1`, we run the process serially
        (very helpful for debugging).

    *args
        Arguments to use for every call of `func_to_call`.

    mp_context
        Multiprocessing context to use.

        By default, we use a spawn context.

        The whole multiprocessing context universe is a bit complex,
        particularly given we also have logging.
        In short, spawn is slower, but safer.
        Full docs on multiprocessing contexts are here:
        https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods.

    **kwargs
        Keyword arguments to use for every call of `func_to_call`.

    Returns
    -------
    :
        Result of calling `func_to_call` with every element in `iterable_input`
        in combination with `args` and `kwargs`.
    """
    if n_processes == 1:
        logger.debug("Running serially")
        res = [
            func_to_call(inv, *args, **kwargs)
            for inv in tqdm.tqdm(iterable_input, desc=input_desc)
        ]

    else:
        logger.info(f"Submitting {input_desc} to {n_processes} parallel processes")
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=n_processes, mp_context=mp_context
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
