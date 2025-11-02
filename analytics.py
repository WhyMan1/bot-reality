import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import redis.asyncio as redis
from collections import defaultdict, Counter
import logging

class AnalyticsCollector:
    """Collects and analyzes bot usage statistics"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def log_domain_check(
        self,
        user_id: int,
        domain: str,
        check_type: str,  # "short" or "full"
        result_status: str,  # "success", "failed", "cached"
        execution_time: Optional[float] = None
    ) -> None:
        """Logs a domain check"""
        timestamp = datetime.now().isoformat()
        
        # General statistics
        await self.redis.incr("analytics:total_checks")
        await self.redis.incr(f"analytics:daily:{datetime.now().strftime('%Y%m%d')}")
        await self.redis.incr(f"analytics:user:{user_id}:total")
        
        # Statistics by check types
        await self.redis.incr(f"analytics:check_type:{check_type}")
        await self.redis.incr(f"analytics:result_status:{result_status}")
        
        # Detailed log (keep 30 days)
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "domain": domain,
            "check_type": check_type,
            "result_status": result_status,
            "execution_time": execution_time
        }
        
        await self.redis.lpush(
            "analytics:detailed_logs",
            json.dumps(log_entry)
        )
        await self.redis.expire("analytics:detailed_logs", 86400 * 30)  # 30 days
        
        # Statistics by domains
        await self.redis.zincrby("analytics:popular_domains", 1, domain)
        
        # Performance
        if execution_time:
            await self.redis.lpush(f"analytics:performance:{check_type}", execution_time)
            await self.redis.ltrim(f"analytics:performance:{check_type}", 0, 999)  # Last 1000
    
    async def log_user_activity(self, user_id: int, action: str, details: Optional[str] = None) -> None:
        """Logs user activity"""
        timestamp = datetime.now().isoformat()
        
        # User activity
        await self.redis.incr(f"analytics:user:{user_id}:actions")
        await self.redis.incr(f"analytics:action:{action}")
        
        # Last activity
        activity_data = {
            "timestamp": timestamp,
            "action": action,
            "details": details
        }
        await self.redis.set(
            f"analytics:user:{user_id}:last_activity",
            json.dumps(activity_data),
            ex=86400 * 7  # Keep for 7 days
        )
    
    async def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Gets analytics summary for the specified period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Basic statistics
        total_checks = await self.redis.get("analytics:total_checks") or 0
        
        # Daily statistics
        daily_stats = {}
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime('%Y%m%d')
            count = await self.redis.get(f"analytics:daily:{date}") or 0
            daily_stats[date] = int(count)
        
        # Popular domains
        popular_domains = await self.redis.zrevrange("analytics:popular_domains", 0, 9, withscores=True)
        
        # Statistics by check types
        short_checks = await self.redis.get("analytics:check_type:short") or 0
        full_checks = await self.redis.get("analytics:check_type:full") or 0
        
        # Statistics by results
        success_count = await self.redis.get("analytics:result_status:success") or 0
        failed_count = await self.redis.get("analytics:result_status:failed") or 0
        cached_count = await self.redis.get("analytics:result_status:cached") or 0
        
        # Performance
        performance_stats = await self._get_performance_stats()
        
        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_checks": int(total_checks),
            "daily_stats": daily_stats,
            "popular_domains": [(domain.decode() if isinstance(domain, bytes) else domain, int(score)) 
                              for domain, score in popular_domains],
            "check_types": {
                "short": int(short_checks),
                "full": int(full_checks)
            },
            "results": {
                "success": int(success_count),
                "failed": int(failed_count),
                "cached": int(cached_count)
            },
            "performance": performance_stats
        }
    
    async def _get_performance_stats(self) -> Dict[str, Any]:
        """Gets performance statistics"""
        stats = {}
        
        for check_type in ["short", "full"]:
            times = await self.redis.lrange(f"analytics:performance:{check_type}", 0, -1)
            if times:
                times = [float(t) for t in times]
                stats[check_type] = {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "total_samples": len(times)
                }
            else:
                stats[check_type] = {
                    "avg_time": 0,
                    "min_time": 0,
                    "max_time": 0,
                    "total_samples": 0
                }
        
        return stats
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Gets statistics for a specific user"""
        total_checks = await self.redis.get(f"analytics:user:{user_id}:total") or 0
        total_actions = await self.redis.get(f"analytics:user:{user_id}:actions") or 0
        
        # Last activity
        last_activity_data = await self.redis.get(f"analytics:user:{user_id}:last_activity")
        last_activity = None
        if last_activity_data:
            try:
                last_activity = json.loads(last_activity_data)
            except json.JSONDecodeError:
                pass
        
        return {
            "user_id": user_id,
            "total_checks": int(total_checks),
            "total_actions": int(total_actions),
            "last_activity": last_activity
        }
    
    async def generate_analytics_report(self, admin_id: int) -> str:
        """Generates a text report for the administrator"""
        summary = await self.get_analytics_summary(days=7)
        
        report = "📊 <b>Bot analytics (7 days)</b>\n\n"
        
        # General statistics
        report += f"🔢 <b>General statistics:</b>\n"
        report += f"• Total checks: {summary['total_checks']}\n"
        report += f"• Successful: {summary['results']['success']}\n"
        report += f"• Failed: {summary['results']['failed']}\n"
        report += f"• From cache: {summary['results']['cached']}\n\n"
        
        # Types of checks
        total_type_checks = summary['check_types']['short'] + summary['check_types']['full']
        if total_type_checks > 0:
            short_pct = (summary['check_types']['short'] / total_type_checks) * 100
            full_pct = (summary['check_types']['full'] / total_type_checks) * 100
            report += f"📋 <b>Types of checks:</b>\n"
            report += f"• Short: {summary['check_types']['short']} ({short_pct:.1f}%)\n"
            report += f"• Full: {summary['check_types']['full']} ({full_pct:.1f}%)\n\n"
        
        # Popular domains
        if summary['popular_domains']:
            report += f"🌐 <b>Top 5 domains:</b>\n"
            for i, (domain, count) in enumerate(summary['popular_domains'][:5], 1):
                report += f"{i}. {domain} ({count} times)\n"
            report += "\n"
        
        # Performance
        perf = summary['performance']
        if perf['short']['total_samples'] > 0:
            report += f"⚡ <b>Performance:</b>\n"
            report += f"• Short: {perf['short']['avg_time']:.1f}s (average)\n"
            report += f"• Full: {perf['full']['avg_time']:.1f}s (average)\n\n"
        
        # Activity by day
        report += f"📅 <b>Activity by day:</b>\n"
        for date, count in sorted(summary['daily_stats'].items(), reverse=True)[:7]:
            date_formatted = datetime.strptime(date, '%Y%m%d').strftime('%d.%m')
            report += f"• {date_formatted}: {count} checks\n"
        
        return report

    async def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Cleans up old analytics data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Cleaning daily statistics
        for i in range(days_to_keep, days_to_keep + 30):  # Check an additional 30 days back
            old_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            await self.redis.delete(f"analytics:daily:{old_date}")
        
        logging.info(f"Cleaned up analytics data older than {days_to_keep} days")
