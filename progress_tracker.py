import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from aiogram import Bot
from aiogram.types import Message
import logging

class ProgressTracker:
    """Tracks progress for multiple domain checks"""
    
    def __init__(self, bot: Bot, message: Message, total_domains: int, update_delay: float = 0.8):
        self.bot = bot
        self.message = message
        self.total_domains = total_domains
        self.completed = 0
        self.failed = 0
        self.start_time = datetime.now()
        self.progress_message: Optional[Message] = None
        self.domain_results: Dict[str, str] = {}
        self.update_delay = update_delay  # Pause between progress updates
        self.last_update_time = 0.0  # Time of last update
        
    async def start(self, domains: List[str]) -> None:
        """Initializes the progress bar"""
        progress_text = self._generate_progress_text(domains)
        try:
            self.progress_message = await self.message.answer(progress_text)
        except Exception as e:
            logging.error(f"Failed to send initial progress message: {e}")
    
    async def update_domain_status(self, domain: str, status: str, result: Optional[str] = None) -> None:
        """Updates the status of a specific domain"""
        if status == "completed":
            self.completed += 1
            if result:
                self.domain_results[domain] = result
        elif status == "failed":
            self.failed += 1
            
        await self._update_progress_message()
    
    async def finish(self) -> None:
        """Finishes progress tracking"""
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        final_text = (
            f"✅ <b>Check completed!</b>\n\n"
            f"📊 <b>Statistics:</b>\n"
            f"• Total domains: {self.total_domains}\n"
            f"• Successful: {self.completed}\n"
            f"• Failed: {self.failed}\n"
            f"• Elapsed time: {elapsed_time:.1f}s\n"
        )
        
        if self.progress_message:
            try:
                await self.progress_message.edit_text(final_text)
            except Exception as e:
                logging.error(f"Failed to update final progress message: {e}")
    
    async def _force_update_progress_message(self) -> None:
        """Force-updates the progress message without delay"""
        if not self.progress_message:
            return
            
        try:
            new_text = self._generate_progress_text()
            await self.progress_message.edit_text(new_text)
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                logging.warning(f"Failed to force update progress message: {e}")
    def _generate_progress_text(self, domains: Optional[List[str]] = None) -> str:
        """Generates progress bar text"""
        progress_percentage = (self.completed / self.total_domains) * 100 if self.total_domains > 0 else 0
        
        # Visual progress bar
        bar_length = 20
        filled_length = int(bar_length * progress_percentage / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        # Estimate remaining time
        if self.completed > 0:
            avg_time_per_domain = elapsed_time / self.completed
            remaining_domains = self.total_domains - self.completed - self.failed
            eta = avg_time_per_domain * remaining_domains
            eta_text = f" | ETA: {eta:.0f}s"
        else:
            eta_text = ""
        
        text = (
            f"🔄 <b>Checking domains...</b>\n\n"
            f"[{bar}] {progress_percentage:.1f}%\n\n"
            f"📊 <b>Progress:</b> {self.completed + self.failed}/{self.total_domains}\n"
            f"✅ Completed: {self.completed}\n"
            f"❌ Failed: {self.failed}\n"
            f"⏱ Time: {elapsed_time:.1f}s{eta_text}"
        )
        
        return text
    
    async def _update_progress_message(self) -> None:
        """Updates the progress message with a delay for readability"""
        if not self.progress_message:
            return
        
    # Check whether enough time has passed since the last update
        current_time = (datetime.now() - self.start_time).total_seconds()
        if current_time - self.last_update_time < self.update_delay:
            return
            
        try:
            new_text = self._generate_progress_text()
            await self.progress_message.edit_text(new_text)
            self.last_update_time = current_time
            
            # Add a pause for readability
            await asyncio.sleep(self.update_delay)
            
        except Exception as e:
            # Telegram may throttle update frequency
            if "message is not modified" not in str(e).lower():
                logging.warning(f"Failed to update progress message: {e}")

class BatchProcessor:
    """Processes domains in batches with progress tracking"""
    
    def __init__(self, bot: Bot, batch_size: int = 3, delay_between_batches: float = 1.0, progress_update_delay: float = 0.8):
        self.bot = bot
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.progress_update_delay = progress_update_delay  # Delay for progress bar updates
    
    async def process_domains(
        self,
        domains: List[str],
        user_id: int,
        message: Message,
        check_function,
        short_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Processes domains in batches and displays progress

        Args:
            domains: List of domains to check
            user_id: User ID
            message: Message used for showing progress
            check_function: Domain check function
            short_mode: Short report mode

        Returns:
            Dictionary with results
        """
        total_domains = len(domains)
        tracker = ProgressTracker(self.bot, message, total_domains, update_delay=self.progress_update_delay)
        
        await tracker.start(domains)
        
        results = {
            "successful": [],
            "failed": [],
            "cached": [],
            "errors": []
        }
        
    # Process domains in batches
        for i in range(0, len(domains), self.batch_size):
            batch = domains[i:i + self.batch_size]
            
            # Create tasks for the current batch
            tasks = []
            for domain in batch:
                task = self._process_single_domain(
                    domain, user_id, check_function, short_mode, tracker, results
                )
                tasks.append(task)
            
            # Execute the batch in parallel
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Pause between batches (except after the last)
            if i + self.batch_size < len(domains):
                await asyncio.sleep(self.delay_between_batches)
        
        await tracker.finish()
        return results
    
    async def _process_single_domain(
        self,
        domain: str,
        user_id: int,
        check_function,
        short_mode: bool,
        tracker: ProgressTracker,
        results: Dict[str, Any]
    ) -> None:
        """Processes a single domain"""
        try:
            result = await check_function(domain, user_id, short_mode)
            
            # Detect cached-result markers (use English 'cache' going forward)
            if result and "cached" in result:
                results["cached"].append(domain)
            
            else:
                results["successful"].append(domain)
                
            await tracker.update_domain_status(domain, "completed", result)
            
        except Exception as e:
            logging.error(f"Error processing domain {domain}: {e}")
            results["failed"].append(domain)
            results["errors"].append(f"{domain}: {str(e)}")
            await tracker.update_domain_status(domain, "failed")
