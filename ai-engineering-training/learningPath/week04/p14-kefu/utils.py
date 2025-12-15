import logging
import time
from functools import wraps

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retry_with_backoff(max_attempts=3, base_delay=1.0):
    """自定义重试装饰器，实现指数退避"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"重试失败，已达到最大尝试次数: {e}")
                        raise e

                    delay = base_delay * (2 ** attempt)  # 指数退避
                    logger.warning(f"第{attempt + 1}次尝试失败，{delay}秒后重试: {e}")
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


def timeout_handler(timeout_seconds=30.0):
    """超时控制装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_signal_handler(signum, frame):
                raise TimeoutError(f"操作超时 ({timeout_seconds}秒)")

            # 设置超时信号
            old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
            signal.alarm(int(timeout_seconds))

            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消超时
                return result
            except TimeoutError:
                logger.error(f"操作超时: {timeout_seconds}秒")
                raise
            finally:
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator
