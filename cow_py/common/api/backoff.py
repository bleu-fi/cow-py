import backoff
import httpx

DEFAULT_BACKOFF_OPTIONS = {
    "max_tries": 10,
    "max_time": None,
    "jitter": None,
}


def dig(self, *keys):
    try:
        for key in keys:
            self = self[key]
        return self
    except KeyError:
        return None


def with_backoff():
    def decorator(func):
        async def wrapper(*args, **kwargs):
            backoff_opts = dig(kwargs, "context_override", "backoff_opts")

            if backoff_opts is None:
                internal_backoff_opts = DEFAULT_BACKOFF_OPTIONS
            else:
                internal_backoff_opts = backoff_opts

            @backoff.on_exception(
                backoff.expo, httpx.HTTPStatusError, **internal_backoff_opts
            )
            async def closure():
                return await func(*args, **kwargs)

            return await closure()

        return wrapper

    return decorator
