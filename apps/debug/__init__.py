import sys
import os

sys.path.insert(0, "/system/apps/debug")
os.chdir("/system/apps/debug")

from badgeware import io, brushes, shapes, PixelFont, screen, run
import network
import machine
import gc
import time

small_font = PixelFont.load("/system/assets/fonts/ark.ppf")
large_font = PixelFont.load("/system/assets/fonts/absolute.ppf")

# Colors
white = brushes.color(235, 245, 255)
phosphor = brushes.color(211, 250, 55)
faded = brushes.color(235, 245, 255, 100)
green = brushes.color(46, 160, 67)
red = brushes.color(220, 50, 47)

# Pages
current_page = 0
total_pages = 4

# WiFi credentials
WIFI_SSID = None
WIFI_PASSWORD = None

# Get WiFi credentials if available
try:
    sys.path.insert(0, "/")
    from secrets import WIFI_PASSWORD, WIFI_SSID
    sys.path.pop(0)
except ImportError:
    WIFI_SSID = None
    WIFI_PASSWORD = None

# Network setup
wlan = None
connection_attempted = False

def init_network():
    global wlan, connection_attempted

    if not WIFI_SSID or connection_attempted:
        return

    connection_attempted = True
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        try:
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        except:
            pass

def format_bytes(bytes):
    """Convert bytes to human readable format"""
    if bytes < 1024:
        return f"{bytes}B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f}KB"
    else:
        return f"{bytes / 1024 / 1024:.1f}MB"

def get_uptime():
    """Get system uptime in human readable format"""
    ms = io.ticks
    seconds = ms // 1000
    minutes = seconds // 60
    hours = minutes // 60

    if hours > 0:
        return f"{hours}h {minutes % 60}m"
    elif minutes > 0:
        return f"{minutes}m {seconds % 60}s"
    else:
        return f"{seconds}s"

def draw_header(title):
    """Draw page header"""
    screen.font = large_font
    screen.brush = white
    w, _ = screen.measure_text(title)
    screen.text(title, 80 - (w / 2), 2)

    # Draw separator line
    screen.brush = phosphor
    screen.draw(shapes.rectangle(5, 18, 150, 1))

def draw_label_value(label, value, x, y, value_color=white):
    """Draw a label: value pair"""
    screen.font = small_font
    screen.brush = phosphor
    screen.text(label, x, y)

    screen.brush = value_color
    label_width, _ = screen.measure_text(label)
    screen.text(str(value), x + label_width + 3, y)

def draw_page_indicator():
    """Draw page navigation indicator at bottom"""
    screen.font = small_font
    screen.brush = faded
    text = f"Page {current_page + 1}/{total_pages}  A/C: Nav"
    w, _ = screen.measure_text(text)
    screen.text(text, 80 - (w / 2), 110)

def draw_network_page():
    """Page 0: Network information"""
    draw_header("Network Info")

    if not wlan:
        init_network()

    y = 25
    line_height = 12

    if wlan and wlan.active():
        is_connected = wlan.isconnected()

        # Connection status
        status_color = green if is_connected else red
        status_text = "Connected" if is_connected else "Disconnected"
        draw_label_value("Status:", status_text, 5, y, status_color)
        y += line_height

        if WIFI_SSID:
            draw_label_value("SSID:", WIFI_SSID[:15], 5, y)
            y += line_height

        if is_connected:
            config = wlan.ifconfig()

            # IP Address
            draw_label_value("IP:", config[0], 5, y)
            y += line_height

            # Netmask
            draw_label_value("Netmask:", config[1], 5, y)
            y += line_height

            # Gateway
            draw_label_value("Gateway:", config[2], 5, y)
            y += line_height

            # DNS
            draw_label_value("DNS:", config[3], 5, y)
            y += line_height

            # MAC Address
            mac = wlan.config('mac')
            mac_str = ':'.join(['%02x' % b for b in mac])
            draw_label_value("MAC:", mac_str[:17], 5, y)
            y += line_height

            # Signal strength (RSSI)
            try:
                rssi = wlan.status('rssi')
                draw_label_value("Signal:", f"{rssi} dBm", 5, y)
            except:
                pass
        else:
            screen.font = small_font
            screen.brush = faded
            screen.text("Not connected to WiFi", 5, y)
    else:
        screen.font = small_font
        screen.brush = faded
        screen.text("WiFi not configured", 5, y)
        y += line_height + 5
        screen.text("Edit secrets.py to", 5, y)
        y += line_height
        screen.text("configure WiFi", 5, y)

def draw_memory_page():
    """Page 1: Memory information"""
    draw_header("Memory Info")

    y = 25
    line_height = 12

    # Run garbage collection to get accurate numbers
    gc.collect()

    # Memory info
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    mem_total = mem_free + mem_alloc

    draw_label_value("Free:", format_bytes(mem_free), 5, y)
    y += line_height

    draw_label_value("Used:", format_bytes(mem_alloc), 5, y)
    y += line_height

    draw_label_value("Total:", format_bytes(mem_total), 5, y)
    y += line_height

    # Usage percentage
    usage_pct = (mem_alloc / mem_total) * 100
    draw_label_value("Usage:", f"{usage_pct:.1f}%", 5, y)
    y += line_height + 5

    # Memory bar graph
    bar_width = 150
    bar_height = 12
    bar_x = 5
    bar_y = y

    # Background
    screen.brush = brushes.color(50, 50, 50)
    screen.draw(shapes.rounded_rectangle(bar_x, bar_y, bar_width, bar_height, 2))

    # Used portion
    used_width = int((mem_alloc / mem_total) * bar_width)
    if usage_pct > 80:
        bar_color = red
    elif usage_pct > 60:
        bar_color = brushes.color(255, 165, 0)  # Orange
    else:
        bar_color = green

    screen.brush = bar_color
    screen.draw(shapes.rounded_rectangle(bar_x, bar_y, used_width, bar_height, 2))

    y += bar_height + 10

    # GC info
    screen.font = small_font
    screen.brush = phosphor
    screen.text("Press B to run GC", 5, y)

def draw_system_page():
    """Page 2: System information"""
    draw_header("System Info")

    y = 25
    line_height = 12

    # Platform
    draw_label_value("Platform:", sys.platform, 5, y)
    y += line_height

    # Implementation
    impl = sys.implementation
    version = f"{impl.version[0]}.{impl.version[1]}.{impl.version[2]}"
    draw_label_value("Python:", version, 5, y)
    y += line_height

    # Frequency
    freq_mhz = machine.freq() // 1_000_000
    draw_label_value("CPU Freq:", f"{freq_mhz} MHz", 5, y)
    y += line_height

    # Screen dimensions
    draw_label_value("Screen:", f"{screen.width}x{screen.height}", 5, y)
    y += line_height

    # Uptime
    draw_label_value("Uptime:", get_uptime(), 5, y)
    y += line_height

    # Unique ID
    unique_id = machine.unique_id()
    uid_hex = ''.join(['%02x' % b for b in unique_id])
    draw_label_value("ID:", uid_hex[:16], 5, y)
    y += line_height
    if len(uid_hex) > 16:
        screen.brush = white
        screen.text(uid_hex[16:], 25, y)
        y += line_height

def draw_storage_page():
    """Page 3: Storage information"""
    draw_header("Storage Info")

    y = 25
    line_height = 12

    try:
        # Get filesystem stats
        stat = os.statvfs('/')

        block_size = stat[0]
        total_blocks = stat[2]
        free_blocks = stat[3]

        total_bytes = total_blocks * block_size
        free_bytes = free_blocks * block_size
        used_bytes = total_bytes - free_bytes

        draw_label_value("Total:", format_bytes(total_bytes), 5, y)
        y += line_height

        draw_label_value("Used:", format_bytes(used_bytes), 5, y)
        y += line_height

        draw_label_value("Free:", format_bytes(free_bytes), 5, y)
        y += line_height

        # Usage percentage
        usage_pct = (used_bytes / total_bytes) * 100
        draw_label_value("Usage:", f"{usage_pct:.1f}%", 5, y)
        y += line_height + 5

        # Storage bar graph
        bar_width = 150
        bar_height = 12
        bar_x = 5
        bar_y = y

        # Background
        screen.brush = brushes.color(50, 50, 50)
        screen.draw(shapes.rounded_rectangle(bar_x, bar_y, bar_width, bar_height, 2))

        # Used portion
        used_width = int((used_bytes / total_bytes) * bar_width)
        if usage_pct > 90:
            bar_color = red
        elif usage_pct > 75:
            bar_color = brushes.color(255, 165, 0)  # Orange
        else:
            bar_color = green

        screen.brush = bar_color
        screen.draw(shapes.rounded_rectangle(bar_x, bar_y, used_width, bar_height, 2))

        y += bar_height + 10

        # Current directory
        screen.font = small_font
        screen.brush = phosphor
        cwd = os.getcwd()
        draw_label_value("CWD:", cwd[:20], 5, y)

    except Exception as e:
        screen.font = small_font
        screen.brush = red
        screen.text(f"Error: {str(e)[:30]}", 5, y)

def update():
    global current_page

    # Handle page navigation
    if io.BUTTON_C in io.pressed:
        current_page = (current_page + 1) % total_pages
    if io.BUTTON_A in io.pressed:
        current_page = (current_page - 1) % total_pages

    # Handle GC on memory page
    if current_page == 1 and io.BUTTON_B in io.pressed:
        gc.collect()

    # Clear screen
    screen.brush = brushes.color(0, 0, 0)
    screen.draw(shapes.rectangle(0, 0, 160, 120))

    # Draw current page
    if current_page == 0:
        draw_network_page()
    elif current_page == 1:
        draw_memory_page()
    elif current_page == 2:
        draw_system_page()
    elif current_page == 3:
        draw_storage_page()

    # Draw navigation
    draw_page_indicator()

if __name__ == "__main__":
    run(update)
