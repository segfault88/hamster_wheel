import threading
import time
from datetime import datetime
import schedule

from config import load_config
from printer import print_task


def print_recurring_task(title: str, description: str):
    """Print a recurring task (called by scheduler)"""
    try:
        print_task(title, description)
        print(
            f"✓ Printed recurring task: {title} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        print(f"✗ Failed to print recurring task '{title}': {e}")


def setup_recurring_tasks():
    """Setup recurring tasks from config"""
    try:
        config = load_config()
        recurring_tasks = config.get("recurring_tasks", {})

        for task_name, task_config in recurring_tasks.items():
            title = task_config["title"]
            description = task_config["description"]
            cron_schedule = task_config["schedule"]

            # Parse cron schedule (minute hour day month weekday)
            parts = cron_schedule.split()
            if len(parts) == 5:
                minute, hour, day, month, weekday = parts

                # Convert weekday from cron format (0=Sunday) to schedule format
                weekday_map = {
                    "0": "sunday",
                    "1": "monday",
                    "2": "tuesday",
                    "3": "wednesday",
                    "4": "thursday",
                    "5": "friday",
                    "6": "saturday",
                }

                if weekday != "*" and weekday in weekday_map:
                    day_name = weekday_map[weekday]
                    time_str = f"{int(hour):02d}:{int(minute):02d}"

                    # Schedule the task
                    getattr(schedule.every(), day_name).at(time_str).do(
                        print_recurring_task, title, description
                    )

                    print(
                        f"✓ Scheduled recurring task: {title} every {day_name} at {time_str}"
                    )

    except Exception as e:
        print(f"✗ Error setting up recurring tasks: {e}")


def run_scheduler():
    """Run the scheduler in a background thread"""
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_scheduler():
    """Start the scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("📅 Recurring task scheduler started")
