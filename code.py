import board
import displayio
import terminalio
from adafruit_display_text.label import Label

# Create a display group to hold our visual elements
main_group = displayio.Group()
board.DISPLAY.root_group = main_group

# Create a light background (White: 0xFFFFFF)
bg_palette = displayio.Palette(1)
bg_palette[0] = 0xFFFFFF
bg_bitmap = displayio.Bitmap(board.DISPLAY.width, board.DISPLAY.height, 1)
bg_tilegrid = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)
main_group.append(bg_tilegrid)

# Create the dark text label (Black: 0x000000)
text_label = Label(
    terminalio.FONT, text="Hello World", color=0x000000, scale=3, x=45, y=120
)
main_group.append(text_label)

# Keep the program running so the screen stays populated
while True:
  pass