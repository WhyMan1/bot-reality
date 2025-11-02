import asyncio
import logging
from typing import Callable, Any, Optional
import random

class RetryConfig:
    """Configuration for retry logic"""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

async def retry_with_backoff(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    Executes a function with exponential backoff retry logic
    
    Args:
        func: Function to execute
        config: Retry configuration
        *args, **kwargs: Function arguments
        
    Returns:
        Function execution result
        
    Raises:
        Exception: Last exception if all attempts fail
    """
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
                
        except Exception as e:
            last_exception = e
            
            if attempt == config.max_attempts - 1:
                # Last attempt - break
                logging.error(f"All {config.max_attempts} attempts failed. Last error: {str(e)}")
                break
                
            # Calculate delay
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Add jitter to avoid thundering herd
            if config.jitter:
                delay = delay * (0.5 + random.random() * 0.5)
                
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f}s")
            await asyncio.sleep(delay)
    
    # If we get here - all attempts failed
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError("All retry attempts failed with unknown error")

# Preset configurations
DOMAIN_CHECK_RETRY = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

REDIS_RETRY = RetryConfig(
    max_attempts=5,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=1.5,
    jitter=True
)

TELEGRAM_RETRY = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=15.0,
    exponential_base=2.0,
    jitter=True
)
