from datetime import datetime
from io import BytesIO
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from escpos.exceptions import USBNotFoundError
from escpos.printer import Usb
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

app = FastAPI(title="Hamster Wheel Task Manager", version="0.1.0")


class TaskRequest(BaseModel):
    title: str
    description: str


def load_config():
    config_path = Path("config.toml")
    if not config_path.exists():
        raise FileNotFoundError(
            "config.toml not found. Copy config.example.toml to config.toml and configure your printer."
        )

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def _load_fonts():
    """Load fonts with fallback to default."""
    try:
        title_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42
        )
        text_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32
        )
        datetime_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
    except (OSError, IOError):
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        datetime_font = ImageFont.load_default()
    
    return title_font, text_font, datetime_font


def _wrap_text_to_width(text, font, max_width, draw):
    """Wrap text to fit within specified width using actual font measurements."""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = test_bbox[2] - test_bbox[0]
        
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines


def _print_task_to_printer(printer, printer_config, img):
    """Handle the actual printing process."""
    printer.image(img)
    
    if printer_config.get("cut_after_print", True):
        printer.cut()
    
    printer.close()


def create_task_image(title, description, config):
    """Create a formatted task image for printing."""
    image_config = config.get("image", {})
    width = image_config.get("width", 576)
    margin = image_config.get("margin", 20)
    line_spacing = image_config.get("line_spacing", 10)

    title_font, text_font, datetime_font = _load_fonts()

    # Create a temporary image to calculate height
    temp_img = Image.new("RGB", (width, 1000), "white")
    temp_draw = ImageDraw.Draw(temp_img)

    # Calculate available width for text
    available_width = width - 2 * margin

    # Wrap text using actual font measurements
    title_lines = _wrap_text_to_width(title, title_font, available_width, temp_draw)
    title_height = len(title_lines) * (42 + line_spacing)

    description_lines = _wrap_text_to_width(description, text_font, available_width, temp_draw)
    description_height = len(description_lines) * (32 + line_spacing)

    # Calculate total height - extra space for datetime at bottom
    total_height = (
        margin * 3 + title_height + description_height + 120
    )  # Extra space for decorations and datetime

    # Create the actual image
    img = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(img)

    # Draw decorative border
    draw.rectangle([5, 5, width - 5, total_height - 5], outline="black", width=2)

    # Current y position
    y_pos = margin + 20

    # Draw title as header (centered)
    for i, line in enumerate(title_lines):
        title_bbox = draw.textbbox((0, 0), line, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, y_pos), line, fill="black", font=title_font)
        y_pos += 42 + line_spacing

    y_pos += 15

    # Draw separator line
    draw.line([(margin, y_pos), (width - margin, y_pos)], fill="black", width=2)
    y_pos += 25

    # Draw description directly
    for line in description_lines:
        draw.text((margin, y_pos), line, fill="black", font=text_font)
        y_pos += 32 + line_spacing

    y_pos += 20

    # Draw bottom border
    draw.line([(margin, y_pos), (width - margin, y_pos)], fill="black", width=2)
    y_pos += 15

    # Add date and time (right aligned)
    now = datetime.now()
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # Calculate text width for right alignment
    datetime_bbox = draw.textbbox((0, 0), datetime_str, font=datetime_font)
    datetime_width = datetime_bbox[2] - datetime_bbox[0]
    datetime_x = width - margin - datetime_width

    draw.text((datetime_x, y_pos), datetime_str, fill="black", font=datetime_font)

    return img


def get_printer():
    config = load_config()
    printer_config = config["printer"]

    try:
        printer = Usb(
            idVendor=printer_config["vendor_id"], idProduct=printer_config["product_id"]
        )
        return printer, printer_config
    except USBNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Printer not found. Check USB connection and config.toml settings.",
        )


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
        printer, printer_config = get_printer()
        config = load_config()

        # Create and print the task image
        img = create_task_image(title, description, config)
        _print_task_to_printer(printer, printer_config, img)

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


@app.post("/api/print-task")
async def api_print_task(task: TaskRequest):
    try:
        printer, printer_config = get_printer()
        config = load_config()

        # Create and print the task image
        img = create_task_image(task.title, task.description, config)
        _print_task_to_printer(printer, printer_config, img)

        return {"status": "success", "message": "Task printed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
