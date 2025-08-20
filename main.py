from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from config import get_recurring_tasks
from printer import print_task
from scheduler import setup_recurring_tasks, start_scheduler
from web import (
    generate_main_page_html,
    handle_print_task_form,
    handle_print_recurring_task_now,
)

app = FastAPI(title="Hamster Wheel Task Manager", version="0.1.0")


class TaskRequest(BaseModel):
    title: str
    description: str


class RecurringTask(BaseModel):
    title: str
    description: str
    schedule: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Main page with task forms and recurring tasks"""
    return generate_main_page_html()


@app.post("/print-task")
async def print_task_route(title: str = Form(...), description: str = Form(...)):
    """Print a one-time task"""
    return handle_print_task_form(title, description)


@app.post("/api/print-task")
async def api_print_task(task: TaskRequest):
    """API endpoint to print a task"""
    try:
        print_task(task.title, task.description)
        return {"status": "success", "message": "Task printed successfully"}
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recurring-tasks")
async def get_recurring_tasks_api():
    """Get all recurring tasks"""
    return get_recurring_tasks()


@app.post("/api/print-recurring-task/{task_name}")
async def print_recurring_task_now(task_name: str):
    """Manually trigger a recurring task to print now"""
    return handle_print_recurring_task_now(task_name)


@app.on_event("startup")
async def startup_event():
    """Initialize recurring tasks and start scheduler"""
    print("🚀 Starting Hamster Wheel Task Manager...")
    setup_recurring_tasks()
    start_scheduler()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
