import asyncio
from agents.scheduler import weekly_brief_job

async def main():
    print("Scheduler started. Press Ctrl+C to stop.")
    while True:
        await weekly_brief_job()
        print("Waiting 30 seconds...")
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())