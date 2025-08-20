import sys
from pathlib import Path
from io import BytesIO
import textwrap
from datetime import datetime
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError
from PIL import Image, ImageDraw, ImageFont


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


def create_task_image(title, description, config):
    image_config = config.get("image", {})
    width = image_config.get("width", 384)  # Common thermal printer width
    margin = image_config.get("margin", 20)
    line_spacing = image_config.get("line_spacing", 10)
    
    # Try to load a font, fall back to default if not available - doubled font sizes
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        datetime_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except (OSError, IOError):
        try:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            datetime_font = ImageFont.load_default()
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            datetime_font = ImageFont.load_default()
    
    # Create a temporary image to calculate height
    temp_img = Image.new('RGB', (width, 1000), 'white')
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Calculate text dimensions - adjusted for larger fonts
    chars_per_line = (width - 2 * margin) // 16  # Adjusted for larger font
    
    # Wrap title text
    title_lines = textwrap.wrap(title, width=chars_per_line)
    title_height = len(title_lines) * (32 + line_spacing)
    
    # Wrap description text
    description_lines = textwrap.wrap(description, width=chars_per_line)
    description_height = len(description_lines) * (24 + line_spacing)
    
    # Calculate total height - extra space for datetime at bottom
    total_height = margin * 3 + title_height + description_height + 120  # Extra space for decorations and datetime
    
    # Create the actual image
    img = Image.new('RGB', (width, total_height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw decorative border
    draw.rectangle([5, 5, width-5, total_height-5], outline='black', width=2)
    
    # Current y position
    y_pos = margin + 15
    
    # Draw header line
    draw.line([(margin, y_pos), (width - margin, y_pos)], fill='black', width=2)
    y_pos += 15
    
    # Draw "TASK" header
    task_text = "TASK"
    task_bbox = draw.textbbox((0, 0), task_text, font=title_font)
    task_width = task_bbox[2] - task_bbox[0]
    task_x = (width - task_width) // 2
    draw.text((task_x, y_pos), task_text, fill='black', font=title_font)
    y_pos += 25
    
    # Draw separator line
    draw.line([(margin, y_pos), (width - margin, y_pos)], fill='black', width=1)
    y_pos += 15
    
    # Draw title
    draw.text((margin, y_pos), "Title:", fill='black', font=title_font)
    y_pos += 20
    
    for line in title_lines:
        draw.text((margin + 10, y_pos), line, fill='black', font=text_font)
        y_pos += 24 + line_spacing
    
    y_pos += 15
    
    # Draw separator
    draw.line([(margin, y_pos), (width - margin, y_pos)], fill='gray', width=1)
    y_pos += 20
    
    # Draw description
    draw.text((margin, y_pos), "Description:", fill='black', font=title_font)
    y_pos += 35
    
    for line in description_lines:
        draw.text((margin + 10, y_pos), line, fill='black', font=text_font)
        y_pos += 24 + line_spacing
    
    y_pos += 20
    
    # Draw bottom border
    draw.line([(margin, y_pos), (width - margin, y_pos)], fill='black', width=2)
    y_pos += 15
    
    # Add date and time (right aligned)
    now = datetime.now()
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate text width for right alignment
    datetime_bbox = draw.textbbox((0, 0), datetime_str, font=datetime_font)
    datetime_width = datetime_bbox[2] - datetime_bbox[0]
    datetime_x = width - margin - datetime_width
    
    draw.text((datetime_x, y_pos), datetime_str, fill='black', font=datetime_font)
    
    return img


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
        printer, printer_config = get_printer()
        config = load_config()
        
        # Create the task image
        img = create_task_image(title, description, config)
        
        # Convert image to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Print the image
        printer.image(img)
        
        if printer_config.get("cut_after_print", True):
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
        printer, printer_config = get_printer()
        config = load_config()
        
        # Create the task image
        img = create_task_image(task.title, task.description, config)
        
        # Convert image to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Print the image
        printer.image(img)
        
        if printer_config.get("cut_after_print", True):
            printer.cut()
        
        printer.close()
        
        return {"status": "success", "message": "Task printed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
