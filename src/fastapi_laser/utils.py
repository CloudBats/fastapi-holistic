import resource


# From fastapi-utils project
# https://github.com/dmontagu/fastapi-utils/blob/master/fastapi_utils/timing.py
def get_cpu_time() -> float:
    """
    Generates the cpu time to report. Adds the user and system time, following the implementation from timing-asgi
    """
    resources = resource.getrusage(resource.RUSAGE_SELF)
    # add up user time (ru_utime) and system time (ru_stime)
    return resources[0] + resources[1]
