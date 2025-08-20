from fastapi import Form, HTTPException
from fastapi.responses import HTMLResponse

from config import get_recurring_tasks
from printer import print_task


def generate_main_page_html() -> str:
    """Generate the main page HTML with recurring tasks"""
    # Get recurring tasks for display
    recurring_tasks = get_recurring_tasks()

    # Generate recurring tasks HTML
    recurring_html = ""
    for task_name, task_config in recurring_tasks.items():
        title = task_config["title"]
        description = task_config["description"]
        schedule = task_config["schedule"]

        # Parse schedule for display
        parts = schedule.split()
        if len(parts) == 5:
            minute, hour, day, month, weekday = parts
            weekday_names = {
                "0": "Sunday",
                "1": "Monday",
                "2": "Tuesday",
                "3": "Wednesday",
                "4": "Thursday",
                "5": "Friday",
                "6": "Saturday",
            }
            day_name = weekday_names.get(weekday, "Unknown")
            time_str = f"{int(hour):02d}:{int(minute):02d}"
            schedule_display = f"Every {day_name} at {time_str}"
        else:
            schedule_display = schedule

        recurring_html += f"""
            <div class="recurring-task">
                <h4>{title}</h4>
                <p><strong>Schedule:</strong> {schedule_display}</p>
                <p><strong>Description:</strong> {description}</p>
                <button class="print-now-btn" onclick="printRecurringTask('{task_name}')">Print Now</button>
            </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hamster Wheel Task Manager</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input, textarea {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }}
            button:hover {{ background-color: #0056b3; }}
            .print-now-btn {{ background-color: #28a745; }}
            .print-now-btn:hover {{ background-color: #218838; }}
            .success {{ color: green; margin-top: 10px; }}
            .error {{ color: red; margin-top: 10px; }}
            .section {{ margin-bottom: 40px; padding: 20px; border: 1px solid #eee; border-radius: 8px; }}
            .recurring-task {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 6px; background-color: #f8f9fa; }}
            .recurring-task h4 {{ margin-top: 0; color: #333; }}
        </style>
    </head>
    <body>
        <h1>Hamster Wheel Task Manager</h1>
        <p>A simple HTTP UI for printing formatted tasks to an attached receipt printer, designed for on-board task management.</p>
        
        <div class="section">
            <h2>Print One-Time Task</h2>
            <form action="/print-task" method="post">
                <div class="form-group">
                    <label for="title">Task Title:</label>
                    <input type="text" id="title" name="title" required>
                </div>
                <div class="form-group">
                    <label for="description">Task Description:</label>
                    <textarea id="description" name="description" rows="4" required></textarea>
                </div>
                <button type="submit">Print Task</button>
            </form>
        </div>
        
        <div class="section">
            <h2>Recurring Tasks</h2>
            <p>These tasks are automatically printed based on their schedules. You can also print them manually.</p>
            {recurring_html}
            {"" if recurring_html else "<p>No recurring tasks configured. Edit config.toml to add recurring tasks.</p>"}
        </div>
        
        <script>
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('success') === 'true') {{
                document.body.innerHTML += '<div class="success">Task printed successfully!</div>';
            }} else if (urlParams.get('error')) {{
                document.body.innerHTML += '<div class="error">Error: ' + urlParams.get('error') + '</div>';
            }}
            
            async function printRecurringTask(taskName) {{
                try {{
                    const response = await fetch(`/api/print-recurring-task/${{taskName}}`, {{
                        method: 'POST'
                    }});
                    
                    if (response.ok) {{
                        const result = await response.json();
                        alert('✓ ' + result.message);
                    }} else {{
                        const error = await response.json();
                        alert('✗ Error: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('✗ Network error: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """


def handle_print_task_form(title: str = Form(...), description: str = Form(...)):
    """Handle the print task form submission"""
    try:
        print_task(title, description)
        return HTMLResponse(
            content="""
            <script>
                window.location.href = '/?success=true';
            </script>
            """,
            status_code=200,
        )
    except Exception as e:
        error_msg = str(e)
        return HTMLResponse(
            content=f"""
            <script>
                window.location.href = '/?error={error_msg}';
            </script>
            """,
            status_code=200,
        )


def handle_print_recurring_task_now(task_name: str):
    """Handle manual printing of recurring tasks"""
    try:
        recurring_tasks = get_recurring_tasks()
        if task_name not in recurring_tasks:
            raise HTTPException(
                status_code=404, detail=f"Recurring task '{task_name}' not found"
            )

        task_config = recurring_tasks[task_name]
        title = task_config["title"]
        description = task_config["description"]

        print_task(title, description)

        return {
            "status": "success",
            "message": f"Recurring task '{title}' printed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
