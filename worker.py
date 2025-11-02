import asyncio
import redis.asyncio as redis
import logging
import os
import json
from logging.handlers import RotatingFileHandler
from redis_queue import get_redis
from aiogram import Bot
from checker import run_check  # Import function from checker.py
from datetime import datetime
from typing import Optional

# Import optional modules (if available)
try:
    from retry_logic import retry_with_backoff, DOMAIN_CHECK_RETRY, REDIS_RETRY
    RETRY_AVAILABLE = True
except ImportError:
    RETRY_AVAILABLE = False
    
try:
    from analytics import AnalyticsCollector
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

# Logging setup
log_file = "/app/worker.log"
# Reduce log file size and number of backups
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler, logging.StreamHandler()]
)

# Telegram Bot initialization
TOKEN = os.getenv("BOT_TOKEN")
SAVE_APPROVED_DOMAINS = os.getenv("SAVE_APPROVED_DOMAINS", "false").lower() == "true"
GROUP_OUTPUT_MODE = os.getenv("GROUP_OUTPUT_MODE", "short").lower()  # "short" or "full"
if not TOKEN:
    logging.error("BOT_TOKEN environment variable is not set")
    raise ValueError("BOT_TOKEN environment variable is not set")
bot = Bot(token=TOKEN, parse_mode="HTML")

# Initialize analytics
analytics_collector = None

async def init_analytics():
    """Initializes analytics"""
    global analytics_collector
    if ANALYTICS_AVAILABLE:
        try:
            redis_client = await get_redis()
            analytics_collector = AnalyticsCollector(redis_client)
            logging.info("Worker analytics initialized successfully")
        except Exception as e:
            logging.warning(f"Failed to initialize worker analytics: {e}")

async def log_analytics(action: str, user_id: int, **kwargs):
    """Logs an event to analytics"""
    if analytics_collector:
        try:
            if action == "domain_check":
                await analytics_collector.log_domain_check(
                    user_id=user_id,
                    domain=kwargs.get("domain", ""),
                    check_type=kwargs.get("check_type", "short"),
                    result_status=kwargs.get("result_status", "unknown"),
                    execution_time=kwargs.get("execution_time")
                )
        except Exception as e:
            logging.warning(f"Failed to log worker analytics: {e}")

async def check_domain(domain: str, user_id: int, short_mode: bool) -> str:
    """Check a domain with optional retry logic and analytics logging"""
    start_time = datetime.now()

    async def perform_check():
        """Inner function to run the blocking run_check in a thread with a timeout."""
        try:
            async with asyncio.timeout(300):
                loop = asyncio.get_event_loop()
                report = await loop.run_in_executor(None, lambda: run_check(domain, full_report=not short_mode))
                return report
        except asyncio.TimeoutError:
            logging.error(f"Timeout while checking {domain} for user {user_id}")
            raise asyncio.TimeoutError("Check {domain} aborted: timeout exceeded (5 minutes).")

    try:
        # Use retry logic if available
        if RETRY_AVAILABLE:
            report = await retry_with_backoff(perform_check, DOMAIN_CHECK_RETRY)
        else:
            report = await perform_check()

        execution_time = (datetime.now() - start_time).total_seconds()

        # Log successful check
        await log_analytics("domain_check", user_id,
                           domain=domain, 
                           check_type="short" if short_mode else "full",
                           result_status="success",
                           execution_time=execution_time)

    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()

        # Log failed check
        await log_analytics("domain_check", user_id,
                           domain=domain,
                           check_type="short" if short_mode else "full", 
                           result_status="failed",
                           execution_time=execution_time)

        logging.error(f"Failed to check {domain} for user {user_id}: {str(e)}")

        # Remove pending key
        r = await get_redis()
        try:
            await r.delete(f"pending:{domain}:{user_id}")
        finally:
            await r.aclose()
            
        return f"❌ Error checking {domain}: {str(e)}"

                    # In group chat use GROUP_OUTPUT_MODE
    r = await get_redis()
    try:
        # Store full report in cache for 7 days (instead of 24 hours)
        await r.set(f"result:{domain}", report, ex=604800)

                       # Full report in group
        if SAVE_APPROVED_DOMAINS and "✅ Suitable for Reality" in report:
            await r.sadd("approved_domains", domain)
                    # Send as usual in DM
        output = report  # Use the report directly from run_check

        await r.lpush(f"history:{user_id}", f"{datetime.now().strftime('%H:%M')} - {domain}")
        await r.ltrim(f"history:{user_id}", 0, 9)
        await r.delete(f"pending:{domain}:{user_id}")
        return output

    except Exception as e:
        logging.error(f"Failed to save result for {domain}: {str(e)}")
        output = f"❌ Error checking {domain}: {str(e)}"
        return output

    finally:
        await r.aclose()

async def clear_cache(r: redis.Redis):
    try:
        keys = await r.keys("result:*")
        if keys:
            await r.delete(*keys)
    except Exception as e:
        logging.error(f"Failed to clear cache: {str(e)}")

async def cache_cleanup_task(r: redis.Redis):
    while True:
        await clear_cache(r)
        await asyncio.sleep(86400)

async def send_group_reply(chat_id: int, message_id: Optional[int], thread_id: Optional[int], text: str, reply_markup=None):
    """Sends a reply to a group with topic and reply support"""
    try:
        if thread_id:
            # Send to a specific topic
            if message_id:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    message_thread_id=thread_id,
                    reply_to_message_id=message_id,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    message_thread_id=thread_id,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
        else:
            # Regular group send
            if message_id:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_to_message_id=message_id,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logging.error(f"Failed to send group reply to {chat_id}: {e}")
        # Fallback: send without reply/thread
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def worker():
    r = await get_redis()
    try:
        await r.ping()
        asyncio.create_task(cache_cleanup_task(r))
        while True:
            try:
                result = await r.brpop("queue:domains", timeout=5)
                if result is None:
                    continue
                _, task = result
                
                # Try parsing as JSON (new format)
                try:
                    task_data = json.loads(task)
                    domain = task_data['domain']
                    user_id = int(task_data['user_id'])
                    short_mode = task_data['short_mode']
                    chat_id = task_data.get('chat_id', user_id)
                    message_id = task_data.get('message_id')
                    thread_id = task_data.get('thread_id')
                except (json.JSONDecodeError, KeyError):
                    # Fallback to old format
                    domain, user_id, short_mode = task.split(":")
                    user_id = int(user_id)
                    short_mode = short_mode == "True"
                    chat_id = user_id
                    message_id = None
                    thread_id = None
                
                result = await check_domain(domain, user_id, short_mode)
                
                try:
                    # Determine if this is a group chat or DM
                    is_group = chat_id != user_id
                    
                    if is_group:
                        # In group chat use GROUP_OUTPUT_MODE
                        if GROUP_OUTPUT_MODE == "short":
                            # Brief report with DM instruction
                            group_message = result + "\n\n💡 <i>For a full report, request it in the bot's DM.</i>"
                            await send_group_reply(chat_id, message_id, thread_id, group_message)
                        else:
                            # Full report in group
                            await send_group_reply(chat_id, message_id, thread_id, result)
                    else:
                        # Send as usual in DM
                        final_message = result
                        if short_mode:
                            final_message += "\n\n💡 <i>For a full report, send the request again with the 'full' parameter.</i>"
                        await bot.send_message(user_id, final_message)
                except Exception as e:
                    logging.error(f"Failed to send message to chat {chat_id} for {domain}: {str(e)}")
            except Exception as e:
                logging.error(f"Worker error: {str(e)}")
                await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"Failed to initialize worker: {str(e)}")
    finally:
        await r.aclose()

if __name__ == "__main__":
    asyncio.run(worker())
