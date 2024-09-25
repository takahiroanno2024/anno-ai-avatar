import time


def measure_time(func):
    """関数の実行時間を計測するデコレータ"""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        return result, elapsed_time

    return wrapper
