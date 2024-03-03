import time

# Added decorator to automatically retry on unpredictable module failures
def retry_on_failure(ExceptionsToCheck, max_retries=5, delay=5, backoff=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            mdelay = delay
            for _ in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ExceptionsToCheck as e:
                    print(f"Error occurred: {e}. Retrying...")
                    time.sleep(delay)
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator