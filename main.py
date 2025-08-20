import sys
from pathlib import Path
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError


app = FastAPI(title="Receipt Printer Task Manager", version="0.1.0")


class TaskRequest(BaseModel):
    title: str
    description: str


def load_config():
    config_path = Path("config.toml")
    if not config_path.exists():
        raise FileNotFoundError("config.toml not found. Copy config.example.toml to config.toml and configure your printer.")
    
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def get_printer():
    config = load_config()
    printer_config = config["printer"]
    
    try:
        printer = Usb(
            idVendor=printer_config["vendor_id"],
            idProduct=printer_config["product_id"]
        )
        return printer, printer_config
    except USBNotFoundError:
        raise HTTPException(status_code=500, detail="Printer not found. Check USB connection and config.toml settings.")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Task Printer</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .success { color: green; margin-top: 10px; }
            .error { color: red; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h1>Receipt Printer Task Manager</h1>
        <p>Print tasks to your attached receipt printer for on-board management.</p>
        
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
        
        <script>
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('success') === 'true') {
                document.body.innerHTML += '<div class="success">Task printed successfully!</div>';
            } else if (urlParams.get('error')) {
                document.body.innerHTML += '<div class="error">Error: ' + urlParams.get('error') + '</div>';
            }
        </script>
    </body>
    </html>
    """


@app.post("/print-task")
async def print_task(title: str = Form(...), description: str = Form(...)):
    try:
        printer, config = get_printer()
        
        printer.text("=" * config.get("text_width", 32) + "\n")
        printer.text("TASK\n")
        printer.text("=" * config.get("text_width", 32) + "\n")
        printer.text(f"Title: {title}\n")
        printer.text("-" * config.get("text_width", 32) + "\n")
        printer.text(f"Description:\n{description}\n")
        printer.text("=" * config.get("text_width", 32) + "\n")
        
        if config.get("cut_after_print", True):
            printer.cut()
        
        printer.close()
        
        return HTMLResponse(
            content="""
            <script>
                window.location.href = '/?success=true';
            </script>
            """,
            status_code=200
        )
        
    except Exception as e:
        error_msg = str(e)
        return HTMLResponse(
            content=f"""
            <script>
                window.location.href = '/?error={error_msg}';
            </script>
            """,
            status_code=200
        )


@app.post("/api/print-task")
async def api_print_task(task: TaskRequest):
    try:
        printer, config = get_printer()
        
        printer.text("=" * config.get("text_width", 32) + "\n")
        printer.text("TASK\n")
        printer.text("=" * config.get("text_width", 32) + "\n")
        printer.text(f"Title: {task.title}\n")
        printer.text("-" * config.get("text_width", 32) + "\n")
        printer.text(f"Description:\n{task.description}\n")
        printer.text("=" * config.get("text_width", 32) + "\n")
        
        if config.get("cut_after_print", True):
            printer.cut()
        
        printer.close()
        
        return {"status": "success", "message": "Task printed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
