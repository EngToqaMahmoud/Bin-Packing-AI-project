import pygame
import sys
import time
from backtracking import backtracking_solver, get_bins_content as bt_bins
from genetic import genetic_solver, get_bins_content as ga_bins

# ── Colours ────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
DARK_GREY  = (40,  40,  40)
LIGHT_GREY = (200, 200, 200)
MID_GREY   = (120, 120, 120)
BG         = (245, 245, 250)

ACCENT     = (70,  130, 180)   # steel blue  – buttons / headers
ACCENT2    = (60,  179, 113)   # medium sea green – GA
SUCCESS    = (46,  139, 87)
ERROR      = (178, 34,  34)

BIN_COLOURS = [
    (255, 179, 102), (102, 204, 255), (153, 255, 153),
    (255, 153, 204), (204, 153, 255), (255, 255, 102),
    (255, 102, 102), (102, 255, 229), (255, 178, 102),
    (178, 255, 102),
]

# ── Layout ─────────────────────────────────────────────────────
W, H       = 960, 680
INPUT_W    = 320        # left panel width
PADDING    = 18
BTN_H      = 42
INPUT_H    = 36
FONT_SM    = 16
FONT_MD    = 18
FONT_LG    = 22


class InputBox:
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect      = pygame.Rect(x, y, w, h)
        self.text      = ""
        self.active    = False
        self.placeholder = placeholder

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isprintable():
                self.text += event.unicode

    def draw(self, surface, font):
        colour = ACCENT if self.active else LIGHT_GREY
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=6)
        pygame.draw.rect(surface, colour, self.rect, 2, border_radius=6)

        display = self.text if self.text else self.placeholder
        text_colour = BLACK if self.text else MID_GREY
        txt_surf = font.render(display, True, text_colour)
        surface.blit(txt_surf, (self.rect.x + 8, self.rect.y + (self.rect.h - txt_surf.get_height()) // 2))


class Button:
    def __init__(self, x, y, w, h, label, colour=ACCENT):
        self.rect   = pygame.Rect(x, y, w, h)
        self.label  = label
        self.colour = colour
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface, font):
        c = tuple(min(255, v + 20) for v in self.colour) if self.hovered else self.colour
        pygame.draw.rect(surface, c, self.rect, border_radius=8)
        label_surf = font.render(self.label, True, WHITE)
        surface.blit(label_surf, (
            self.rect.centerx - label_surf.get_width() // 2,
            self.rect.centery - label_surf.get_height() // 2
        ))


def draw_text(surface, text, x, y, font, colour=BLACK):
    surface.blit(font.render(text, True, colour), (x, y))


def draw_bins(surface, bins_content, bin_capacity, font_sm, font_md, start_x, start_y, area_w, area_h, title, title_colour):
    # Title
    draw_text(surface, title, start_x, start_y, font_md, title_colour)
    start_y += 30

    if not bins_content:
        draw_text(surface, "No result yet.", start_x, start_y, font_sm, MID_GREY)
        return

    num_bins   = len(bins_content)
    max_cols   = 5
    cols       = min(num_bins, max_cols)
    rows       = (num_bins + cols - 1) // cols
    gap        = 10
    bin_w      = (area_w - gap * (cols - 1)) // cols
    bin_h      = min(140, (area_h - 30 - gap * (rows - 1)) // rows)

    for i, content in enumerate(bins_content):
        col   = i % cols
        row   = i // cols
        bx    = start_x + col * (bin_w + gap)
        by    = start_y + row * (bin_h + gap)
        total = sum(content)
        fill  = total / bin_capacity

        # Bin background
        pygame.draw.rect(surface, LIGHT_GREY, (bx, by, bin_w, bin_h), border_radius=6)

        # Fill bar
        fill_h = int(bin_h * fill)
        fill_colour = BIN_COLOURS[i % len(BIN_COLOURS)]
        pygame.draw.rect(surface, fill_colour,
                         (bx, by + bin_h - fill_h, bin_w, fill_h),
                         border_radius=6)

        # Border
        pygame.draw.rect(surface, MID_GREY, (bx, by, bin_w, bin_h), 2, border_radius=6)

        # Bin label
        draw_text(surface, f"Bin {i+1}", bx + 4, by + 4, font_sm, DARK_GREY)

        # Items inside
        items_text = ", ".join(str(v) for v in content)
        if font_sm.size(items_text)[0] > bin_w - 8:
            items_text = items_text[:12] + "..."
        draw_text(surface, items_text, bx + 4, by + bin_h // 2 - 8, font_sm, DARK_GREY)

        # Total / capacity
        draw_text(surface, f"{total}/{bin_capacity}", bx + 4, by + bin_h - 20, font_sm, DARK_GREY)


def draw_metrics(surface, result, font_sm, x, y, colour):
    if not result:
        return
    draw_text(surface, f"Bins used   : {result['num_bins']}",   x, y,      font_sm, colour)
    draw_text(surface, f"Time taken  : {result['time']}s",      x, y + 22, font_sm, colour)
    if "iterations" in result:
        draw_text(surface, f"Iterations  : {result['iterations']}", x, y + 44, font_sm, colour)
    if "generations" in result:
        draw_text(surface, f"Generations : {result['generations']}", x, y + 44, font_sm, colour)


def main():
    pygame.init()
    screen  = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Bin Packing Problem Solver")
    clock   = pygame.time.Clock()

    font_sm = pygame.font.SysFont("Segoe UI", FONT_SM)
    font_md = pygame.font.SysFont("Segoe UI", FONT_MD)
    font_lg = pygame.font.SysFont("Segoe UI", FONT_LG, bold=True)

    # ── Input widgets ───────────────────────────────────────────
    lx = PADDING   # left panel x
    ly = 80

    items_box    = InputBox(lx, ly,        INPUT_W - 2*PADDING, INPUT_H, "e.g. 4, 3, 5, 4, 1, 2, 4")
    capacity_box = InputBox(lx, ly + 70,   INPUT_W - 2*PADDING, INPUT_H, "e.g. 8")

    btn_bt  = Button(lx,             ly + 140, (INPUT_W - 2*PADDING - 8) // 2, BTN_H, "Backtracking", ACCENT)
    btn_ga  = Button(lx + (INPUT_W - 2*PADDING - 8) // 2 + 8,
                     ly + 140, (INPUT_W - 2*PADDING - 8) // 2, BTN_H, "Genetic Algo", ACCENT2)
    btn_both = Button(lx,            ly + 194, INPUT_W - 2*PADDING, BTN_H, "Run Both & Compare", MID_GREY)
    btn_clear = Button(lx,           ly + 248, INPUT_W - 2*PADDING, BTN_H, "Clear", ERROR)

    widgets = [items_box, capacity_box]
    buttons = [btn_bt, btn_ga, btn_both, btn_clear]

    # ── State ───────────────────────────────────────────────────
    bt_result  = None
    ga_result  = None
    error_msg  = ""
    mode       = "none"   # "bt" | "ga" | "both"

    def parse_inputs():
        nonlocal error_msg
        try:
            items = [int(x.strip()) for x in items_box.text.split(",") if x.strip()]
            cap   = int(capacity_box.text.strip())
            if not items:
                error_msg = "Please enter at least one item."; return None, None
            if any(i <= 0 for i in items):
                error_msg = "Item sizes must be positive."; return None, None
            if cap <= 0:
                error_msg = "Bin capacity must be positive."; return None, None
            if any(i > cap for i in items):
                error_msg = "An item is larger than the bin capacity."; return None, None
            error_msg = ""
            return items, cap
        except ValueError:
            error_msg = "Invalid input. Use numbers separated by commas."
            return None, None

    running = True
    while running:
        screen.fill(BG)

        # ── Events ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            for w in widgets:
                w.handle_event(event)

            if btn_bt.handle_event(event):
                items, cap = parse_inputs()
                if items:
                    asgn, nb, t, iters = backtracking_solver(items, cap)
                    bt_result = {"assignment": asgn, "num_bins": nb,
                                 "time": t, "iterations": iters,
                                 "bins_content": bt_bins(items, asgn, nb),
                                 "items": items, "capacity": cap}
                    ga_result = None
                    mode = "bt"

            if btn_ga.handle_event(event):
                items, cap = parse_inputs()
                if items:
                    asgn, nb, t, hist = genetic_solver(items, cap)
                    ga_result = {"assignment": asgn, "num_bins": nb,
                                 "time": t, "generations": len(hist),
                                 "bins_content": ga_bins(items, asgn, nb),
                                 "items": items, "capacity": cap}
                    bt_result = None
                    mode = "ga"

            if btn_both.handle_event(event):
                items, cap = parse_inputs()
                if items:
                    asgn, nb, t, iters = backtracking_solver(items, cap)
                    bt_result = {"assignment": asgn, "num_bins": nb,
                                 "time": t, "iterations": iters,
                                 "bins_content": bt_bins(items, asgn, nb),
                                 "items": items, "capacity": cap}
                    asgn, nb, t, hist = genetic_solver(items, cap)
                    ga_result = {"assignment": asgn, "num_bins": nb,
                                 "time": t, "generations": len(hist),
                                 "bins_content": ga_bins(items, asgn, nb),
                                 "items": items, "capacity": cap}
                    mode = "both"

            if btn_clear.handle_event(event):
                items_box.text = ""
                capacity_box.text = ""
                bt_result = None
                ga_result = None
                error_msg = ""
                mode = "none"

        # ── Left Panel ──────────────────────────────────────────
        pygame.draw.rect(screen, WHITE, (0, 0, INPUT_W, H))
        pygame.draw.line(screen, LIGHT_GREY, (INPUT_W, 0), (INPUT_W, H), 2)

        draw_text(screen, "Bin Packing Solver", lx, 20, font_lg, ACCENT)

        draw_text(screen, "Item Sizes (comma separated):", lx, ly - 20, font_sm, DARK_GREY)
        items_box.draw(screen, font_sm)

        draw_text(screen, "Bin Capacity:", lx, ly + 50, font_sm, DARK_GREY)
        capacity_box.draw(screen, font_sm)

        for b in buttons:
            b.draw(screen, font_sm)

        if error_msg:
            # Word-wrap error over two lines if needed
            draw_text(screen, error_msg, lx, ly + 310, font_sm, ERROR)

        # Metrics
        my = ly + 350
        if bt_result:
            draw_text(screen, "Backtracking Result:", lx, my, font_sm, ACCENT)
            draw_metrics(screen, bt_result, font_sm, lx, my + 22, DARK_GREY)
            my += 100
        if ga_result:
            draw_text(screen, "Genetic Algorithm Result:", lx, my, font_sm, ACCENT2)
            draw_metrics(screen, ga_result, font_sm, lx, my + 22, DARK_GREY)

        # ── Right Panel (visualisation) ─────────────────────────
        rx      = INPUT_W + PADDING
        rw      = W - INPUT_W - PADDING * 2
        ry      = 20

        if mode == "none":
            draw_text(screen, "Enter items and capacity, then run an algorithm.",
                      rx, H // 2, font_sm, MID_GREY)

        elif mode == "bt" and bt_result:
            draw_bins(screen, bt_result["bins_content"], bt_result["capacity"],
                      font_sm, font_md, rx, ry, rw, H - 40,
                      f"Backtracking  —  {bt_result['num_bins']} bins", ACCENT)

        elif mode == "ga" and ga_result:
            draw_bins(screen, ga_result["bins_content"], ga_result["capacity"],
                      font_sm, font_md, rx, ry, rw, H - 40,
                      f"Genetic Algorithm  —  {ga_result['num_bins']} bins", ACCENT2)

        elif mode == "both":
            mid_y = H // 2 - 10
            if bt_result:
                draw_bins(screen, bt_result["bins_content"], bt_result["capacity"],
                          font_sm, font_md, rx, ry, rw, mid_y - ry,
                          f"Backtracking  —  {bt_result['num_bins']} bins  |  {bt_result['time']}s", ACCENT)
            pygame.draw.line(screen, LIGHT_GREY, (rx, mid_y), (W - PADDING, mid_y), 1)
            if ga_result:
                draw_bins(screen, ga_result["bins_content"], ga_result["capacity"],
                          font_sm, font_md, rx, mid_y + 10, rw, H - mid_y - 20,
                          f"Genetic Algo  —  {ga_result['num_bins']} bins  |  {ga_result['time']}s", ACCENT2)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
