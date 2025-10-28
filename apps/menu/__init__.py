import sys
import os

sys.path.insert(0, "/system/apps/menu")
os.chdir("/system/apps/menu")

import math
from badgeware import screen, PixelFont, Image, SpriteSheet, is_dir, file_exists, shapes, brushes, io, run
from icon import Icon
import ui

# define the list of installed apps
#
# - hack them!
# - replace them with your own
# - reorder them
# - what would mona do...?
apps = [
    ("mona's quest", "quest"),
    ("mona pet", "monapet"),
    ("monasketch", "sketch"),
    ("flappy mona", "flappy"),
    ("gallery", "gallery"),
    ("badge", "badge"),
    ("debug info", "debug"),
]

mona = SpriteSheet("/system/assets/mona-sprites/mona-default.png", 11, 1)
screen.font = PixelFont.load("/system/assets/fonts/ark.ppf")
# screen.antialias = Image.X2

# find installed apps and create icons
icons = []
for app in apps:
    name, path = app[0], app[1]

    if is_dir(f"/system/apps/{path}"):
        if file_exists(f"/system/apps/{path}/icon.png"):
            x = len(icons) % 3
            y = math.floor(len(icons) / 3)
            pos = (x * 48 + 33, y * 48 + 42)
            sprite = Image.load(f"/system/apps/{path}/icon.png")
            icons.append(Icon(pos, name, len(icons), sprite))

active = 0

MAX_ALPHA = 255
alpha = 30


def update():
    global active, icons, alpha

    # process button inputs to switch between icons
    if io.BUTTON_C in io.pressed:
        active += 1
    if io.BUTTON_A in io.pressed:
        active -= 1
    if io.BUTTON_UP in io.pressed:
        active -= 3
    if io.BUTTON_DOWN in io.pressed:
        active += 3
    if io.BUTTON_B in io.pressed:
        return f"/system/apps/{apps[active][1]}"
    active %= len(icons)

    # calculate scroll offset based on active icon row
    # 3 icons per row, 48 pixels per row
    active_row = math.floor(active / 3)
    scroll_offset = 0
    if active_row >= 2:
        # scroll up by 48 pixels when on row 2 or higher
        scroll_offset = -48 * (active_row - 1)

    ui.draw_background()
    ui.draw_header()

    # draw menu icons with scroll offset
    for i in range(len(icons)):
        icons[i].activate(active == i)
        icons[i].draw(scroll_offset)

    # draw label for active menu icon with scroll offset
    if Icon.active_icon:
        label = f"{Icon.active_icon.name}"
        w, _ = screen.measure_text(label)
        label_y = 100 + scroll_offset
        screen.brush = brushes.color(211, 250, 55)
        screen.draw(shapes.rounded_rectangle(80 - (w / 2) - 4, label_y, w + 8, 15, 4))
        screen.brush = brushes.color(0, 0, 0, 150)
        screen.text(label, 80 - (w / 2), label_y + 1)

    if alpha <= MAX_ALPHA:
        screen.brush = brushes.color(0, 0, 0, 255 - alpha)
        screen.clear()
        alpha += 30

    return None

if __name__ == "__main__":
    run(update)
