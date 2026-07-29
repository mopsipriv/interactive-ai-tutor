import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from agents.scheduler import weekly_brief_job

async def main():
    scheduler = AsyncIOScheduler()
    
    # every monday at 8:00
    scheduler.add_job(weekly_brief_job, trigger="cron", day_of_week="mon", hour=8, minute=0)
    
    # for testing every 30 sec
    # scheduler.add_job(weekly_brief_job, trigger="interval", seconds=30)
    
    scheduler.start()
    print("✅ Scheduler started. Running every Monday at 08:00.")
    print("Press Ctrl+C to stop.")
    
    try:
        await asyncio.Event().wait() 
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped.")

if __name__ == "__main__":
    asyncio.run(main())