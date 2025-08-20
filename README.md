# Hamster Wheel Task Manager

A simple HTTP ui for printing formatted tasks to an attached receipt printer, designed for on-board task management.

## Overview

This project provides a web interface and API endpoint that allows you to:
- Enter task titles and descriptions through a simple web form
- Generate professionally formatted task images with proper typography
- Print high-quality task receipts to a USB-connected receipt printer
- Automatically cut receipts after printing with timestamps

Perfect for procrastinators and ADHD types. Turn your todo list into something in the real world you cannot ignore.

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Your Printer

1. Copy the example configuration file:
   ```bash
   cp config.example.toml config.toml
   ```

2. Find your printer's USB vendor and product IDs:
   ```bash
   lsusb
   ```
   Look for your receipt printer in the output and note the vendor:product IDs.

3. Edit `config.toml` with your printer's settings:
   ```toml
   [printer]
   vendor_id = 0x04b8  # Your printer's vendor ID
   product_id = 0x0202  # Your printer's product ID
   cut_after_print = true

   [image]
   width = 576          # Image width in pixels (576 works well for most thermal printers)
   margin = 20          # Margin around text in pixels
   line_spacing = 10    # Extra spacing between lines in pixels
   ```

### 3. Run the Application

```bash
uv run main.py
```

The web interface will be available at http://localhost:8000

## Usage

### Web Interface

Navigate to http://localhost:8000 in your browser to access the simple task entry form.

### API Endpoint

You can also submit tasks programmatically:

```bash
curl -X POST "http://localhost:8000/api/print-task" \
     -H "Content-Type: application/json" \
     -d '{"title": "Check engine oil", "description": "Check and top up engine oil before departure"}'
```

## Receipt Format

Tasks are printed as professionally formatted images with:
- **Bordered layout** with clean lines and proper spacing
- **Centered task title** in large, bold font (42pt)
- **Separator line** dividing title and description
- **Description text** in readable font (32pt) with intelligent text wrapping
- **Right-aligned timestamp** showing when the task was printed
- **Automatic text wrapping** that optimally uses the full width of the receipt

Example layout:
```
┌─────────────────────────────────┐
│                                 │
│        Check Engine Oil         │
│─────────────────────────────────│
│ Check and top up engine oil     │
│ before departure. Also inspect  │
│ for any leaks or unusual wear.  │
│─────────────────────────────────│
│                  2024-01-15 14:30:25 │
└─────────────────────────────────┘
```

## Supported Printers

This project uses python-escpos which supports a wide range of ESC/POS compatible receipt printers. I'm using a cheap clone called an HZ-8360 from Aliexpress and 80x80 Thermal paper.

## Troubleshooting

### Printer Not Found
- Ensure your printer is connected via USB and powered on
- Verify the vendor_id and product_id in config.toml match your printer
- On Linux, you may need to add your user to the `lp` group: `sudo usermod -a -G lp $USER`

### Permission Issues
- The printer may require root access. Try running with `sudo` if needed
- Alternatively, set up udev rules for your printer device

## Configuration Options

### Image Settings
The `[image]` section in `config.toml` allows you to customize the receipt appearance:
- **width**: Image width in pixels (default: 576, good for most thermal printers)
- **margin**: Space around text in pixels (default: 20)
- **line_spacing**: Extra spacing between text lines (default: 10)

### Font Handling
The application automatically tries to load system fonts:
1. **Primary**: DejaVu Sans fonts (Bold for titles, Regular for text)
2. **Fallback**: System default fonts if DejaVu is unavailable

## Development

The application is built with:
- **FastAPI** for the web framework and API endpoints
- **python-escpos** for thermal printer communication
- **Pillow (PIL)** for image generation and text rendering
- **uvicorn** as the ASGI server

To run in development mode with auto-reload:
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```