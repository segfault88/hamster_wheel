# Receipt Printer Task Manager

A simple HTTP endpoint for printing tasks to an attached receipt printer, designed for on-board task management.

## Overview

This project provides a web interface and API endpoint that allows you to:
- Enter task titles and descriptions through a simple web form
- Print tasks directly to a USB-connected receipt printer
- Automatically cut the receipt after printing

Perfect for boats, RVs, workshops, or any environment where you need physical task reminders that won't rely on digital devices.

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
   text_width = 32
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

Tasks are printed with the following format:
```
================================
TASK
================================
Title: [Your task title]
--------------------------------
Description:
[Your task description]
================================
```

## Supported Printers

This project uses python-escpos which supports a wide range of ESC/POS compatible receipt printers including:
- Epson TM series
- Star Micronics
- Citizen
- And many generic thermal receipt printers

## Troubleshooting

### Printer Not Found
- Ensure your printer is connected via USB and powered on
- Verify the vendor_id and product_id in config.toml match your printer
- On Linux, you may need to add your user to the `lp` group: `sudo usermod -a -G lp $USER`

### Permission Issues
- The printer may require root access. Try running with `sudo` if needed
- Alternatively, set up udev rules for your printer device

## Development

The application is built with:
- FastAPI for the web framework
- python-escpos for printer communication
- uvicorn as the ASGI server

To run in development mode with auto-reload:
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```