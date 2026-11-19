import tkinter as tk
from tkinter import messagebox
import pygame
import random
import math
import os
import sys
import subprocess
import tempfile
import wave
import struct

# ============================================================
# BRICK BREAKER - MENU + PYGAME
# ============================================================

W, H = 1200, 800
PADDLE_W, PADDLE_H = 150, 18
BALL_R = 10

THEMES = {
    "SPACE": {
        "bg": (4, 7, 28),
        "bricks": [(55, 150, 255), (130, 75, 255), (235, 70, 190)],
        "paddle": (70, 210, 255),
    },
    "VOLCANO": {
        "bg": (35, 6, 5),
        "bricks": [(255, 65, 25), (255, 135, 25), (205, 35, 20)],
        "paddle": (255, 100, 35),
    },
    "FOREST": {
        "bg": (4, 25, 14),
        "bricks": [(45, 175, 85), (120, 210, 70), (30, 125, 80)],
        "paddle": (90, 225, 120),
    }
}


# -------------------- SOUND --------------------

def make_sound(path, frequency, duration=0.08):
    rate = 44100
    count = int(rate * duration)

    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)

        for i in range(count):
            value = int(
                32767 * 0.28 *
                math.sin(2 * math.pi * frequency * i / rate)
            )
            f.writeframes(struct.pack("<h", value))


def get_sounds():
    folder = os.path.join(tempfile.gettempdir(), "brick_breaker_sounds")
    os.makedirs(folder, exist_ok=True)

    names = {
        "wall": 180,
        "paddle": 280,
        "brick": 550,
        "coin": 900,
        "clear": 1000,
        "lose": 100
    }

    sounds = {}

    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        for name, freq in names.items():
            path = os.path.join(folder, name + ".wav")

            if not os.path.exists(path):
                make_sound(path, freq)

            sounds[name] = pygame.mixer.Sound(path)

    except Exception:
        class Silent:
            def play(self):
                pass

        for name in names:
            sounds[name] = Silent()

    return sounds


# -------------------- DRAW HELPERS --------------------

def text(screen, value, font, color, x, y, center=False):
    img = font.render(value, True, color)

    if center:
        screen.blit(img, (x - img.get_width() // 2,
                          y - img.get_height() // 2))
    else:
        screen.blit(img, (x, y))


def rounded(screen, rect, color, radius=10, border=None):
    pygame.draw.rect(screen, color, rect, border_radius=radius)

    if border:
        pygame.draw.rect(
            screen, border, rect, 2, border_radius=radius
        )


# -------------------- BACKGROUNDS --------------------

def make_stars():
    return [
        [
            random.randrange(W),
            random.randrange(100, H),
            random.choice([1, 1, 2, 2, 3]),
            random.uniform(.5, 1.8)
        ]
        for _ in range(190)
    ]


def draw_space(screen, stars, t):
    screen.fill(THEMES["SPACE"]["bg"])

    # soft nebula
    for i in range(8):
        x = 100 + i * 160
        y = 220 + int(math.sin(t * .001 + i) * 35)
        pygame.draw.circle(screen, (10, 12, 50), (x, y), 120)

    # stars
    for x, y, r, speed in stars:
        glow = int(170 + 70 * math.sin(t * .002 * speed + x))
        glow = max(100, min(255, glow))
        pygame.draw.circle(screen, (glow, glow, 255), (x, y), r)

    # large planet
    pygame.draw.circle(screen, (35, 75, 180), (1000, 180), 92)
    pygame.draw.circle(screen, (60, 120, 235), (970, 150), 38)
    pygame.draw.ellipse(screen, (130, 190, 255),
                        (885, 140, 1115, 220), 5)

    # small planet
    pygame.draw.circle(screen, (210, 70, 170), (150, 180), 43)

    # moving asteroids
    for i in range(9):
        x = int((i * 150 + t * (.025 + i * .002)) % (W + 100) - 50)
        y = 300 + int(math.sin(t * .001 + i) * 30)

        pygame.draw.polygon(
            screen, (75, 82, 105),
            [(x, y), (x+25, y-15), (x+48, y+3),
             (x+30, y+28), (x-8, y+18)]
        )


def draw_volcano(screen, t):
    # animated dark red sky
    for y in range(H):
        p = y / H
        color = (
            int(25 + p * 45),
            int(4 + p * 10),
            int(4 + p * 3)
        )
        pygame.draw.line(screen, color, (0, y), (W, y))

    # moon
    pygame.draw.circle(screen, (255, 165, 65), (990, 155), 75)
    pygame.draw.circle(screen, (55, 8, 5), (1020, 130), 75)

    # distant mountains
    pygame.draw.polygon(
        screen, (65, 12, 10),
        [(0, 590), (220, 350), (440, 590)]
    )
    pygame.draw.polygon(
        screen, (75, 10, 8),
        [(300, 590), (600, 300), (900, 590)]
    )

    # main volcano
    pygame.draw.polygon(
        screen, (70, 17, 12),
        [(405, 680), (600, 305), (805, 680)]
    )
    pygame.draw.polygon(
        screen, (110, 28, 10),
        [(510, 680), (600, 365), (705, 680)]
    )

    # lava
    pygame.draw.polygon(
        screen, (255, 65, 10),
        [(582, 355), (618, 355), (650, 680), (550, 680)]
    )

    # animated lava glow
    for i in range(24):
        x = (i * 83 + int(t * .05)) % W
        y = 450 + (i * 31) % 300

        if i % 2 == 0:
            pygame.draw.circle(
                screen, (255, random.randrange(60, 150), 10),
                (x, y), random.randrange(2, 5)
            )

    # erupting sparks
    for i in range(14):
        x = 600 + math.sin(t * .002 + i) * (25 + i * 5)
        y = 330 - ((t * (.05 + i * .003) + i * 25) % 190)

        pygame.draw.circle(
            screen, (255, 145, 30),
            (int(x), int(y)), 4
        )


def draw_forest(screen, t):
    screen.fill((4, 24, 13))

    # moon
    pygame.draw.circle(screen, (220, 235, 180), (990, 150), 70)
    pygame.draw.circle(screen, (4, 24, 13), (1020, 125), 70)

    # hills
    pygame.draw.polygon(
        screen, (8, 55, 28),
        [(0, 590), (260, 330), (520, 590)]
    )
    pygame.draw.polygon(
        screen, (7, 45, 23),
        [(350, 590), (650, 300), (980, 590)]
    )

    # trees
    for i in range(15):
        x = 25 + i * 85
        h = 110 + (i % 4) * 25

        pygame.draw.rect(
            screen, (75, 45, 20),
            (x, 610-h//3, 18, h)
        )

        pygame.draw.polygon(
            screen, (18, 105, 48),
            [(x-38, 590-h), (x+9, 500-h),
             (x+56, 590-h)]
        )

        pygame.draw.polygon(
            screen, (12, 75, 36),
            [(x-48, 630-h), (x+9, 535-h),
             (x+65, 630-h)]
        )

    # fireflies
    for i in range(30):
        x = int((i * 101 + t * .03) % W)
        y = 240 + (i * 43) % 400
        pygame.draw.circle(screen, (180, 255, 100), (x, y), 2)


# -------------------- BRICKS --------------------

def create_bricks(level, theme):
    bricks = []

    cols = 10
    rows = 6
    gap = 8
    left = 75
    top = 145

    bw = int((W - 2 * left - (cols - 1) * gap) / cols)
    bh = 32

    for row in range(rows):
        for col in range(cols):

            make = True

            if level % 4 == 2:
                make = not (row == 0 and col in (0, 1, 8, 9))

            elif level % 4 == 3:
                make = (row + col) % 2 == 0

            elif level % 4 == 0:
                make = not (2 <= col <= 7 and row in (1, 2))

            if make:
                rect = pygame.Rect(
                    left + col * (bw + gap),
                    top + row * (bh + gap),
                    bw,
                    bh
                )

                bricks.append({
                    "rect": rect,
                    "color": random.choice(THEMES[theme]["bricks"]),
                    "hp": 1 if level < 6 else 2
                })

    return bricks


def create_stones():
    stones = []

    # Only a small opening in the middle.
    gap = 220
    wall_width = (W - gap) // 2
    y = H - 120

    for x in range(0, wall_width, 36):
        stones.append(pygame.Rect(x+2, y, 32, 38))

    for x in range(wall_width + gap, W, 36):
        stones.append(pygame.Rect(x+2, y, 32, 38))

    return stones


# -------------------- GAME --------------------

def play_game(theme, mode, difficulty):
    pygame.init()

    try:
        pygame.mixer.init()
    except Exception:
        pass

    # Fullscreen Pygame window.
    screen = pygame.display.set_mode(
        (W, H),
        pygame.FULLSCREEN | pygame.SCALED
    )
    pygame.display.set_caption("Brick Breaker")

    clock = pygame.time.Clock()
    sounds = get_sounds()

    font20 = pygame.font.SysFont("Arial", 20, bold=True)
    font26 = pygame.font.SysFont("Arial", 26, bold=True)
    font48 = pygame.font.SysFont("Arial", 48, bold=True)
    font70 = pygame.font.SysFont("Arial", 70, bold=True)

    stars = make_stars()

    if difficulty == "EASY":
        speed = 5
        lives = 5
    elif difficulty == "HARD":
        speed = 8
        lives = 3
    else:
        speed = 6
        lives = 4

    level = 1
    score = 0

    paddle = pygame.Rect(
        W // 2 - PADDLE_W // 2,
        H - 70,
        PADDLE_W,
        PADDLE_H
    )

    ball_x = float(W // 2)
    ball_y = float(H - 105)
    dx = speed * .75
    dy = -speed

    bricks = create_bricks(level, theme)
    stones = create_stones() if mode == "BOUNDARY BREAKER" else []

    coins = []
    clear = False
    paused = False
    running = True

    while running:
        clock.tick(120)
        t = pygame.time.get_ticks()

        # ------------------------------------------------
        # EVENTS
        # ------------------------------------------------
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_p:
                    paused = not paused

                elif event.key == pygame.K_r and clear:
                    level += 1
                    bricks = create_bricks(level, theme)

                    if mode == "BOUNDARY BREAKER":
                        stones = create_stones()

                    ball_x = W // 2
                    ball_y = H - 105
                    dx = random.choice([-1, 1]) * speed * .75
                    dy = -speed
                    clear = False

        # ------------------------------------------------
        # BACKGROUND
        # ------------------------------------------------
        if theme == "SPACE":
            draw_space(screen, stars, t)
        elif theme == "VOLCANO":
            draw_volcano(screen, t)
        else:
            draw_forest(screen, t)

        # ------------------------------------------------
        # HUD
        # ------------------------------------------------
        rounded(
            screen,
            pygame.Rect(22, 18, W-44, 72),
            (8, 13, 38),
            18,
            (80, 120, 190)
        )

        text(screen, f"STAGE {level}", font26,
             (255,255,255), 42, 40)

        text(screen, f"TARGET {len(bricks)}", font26,
             (255,220,80), 225, 40)

        text(screen, f"SCORE {score}", font26,
             (90,220,255), 435, 40)

        text(screen, f"LIVES {lives}", font26,
             (255,100,110), 640, 40)

        text(screen, mode, font20,
             (180,215,255), 820, 43)

        text(screen, theme, font20,
             (255,190,90), 1040, 43)

        # ------------------------------------------------
        # UPDATE
        # ------------------------------------------------
        if not paused and not clear:

            # IMPORTANT FIX:
            # Do NOT wait for KEYDOWN.
            # get_pressed() reads the arrow key every frame.
            keys = pygame.key.get_pressed()

            move = 0

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                move -= 1

            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                move += 1

            paddle.x += move * 12

            paddle.x = max(0, min(W - PADDLE_W, paddle.x))

            # Ball movement
            ball_x += dx
            ball_y += dy

            ball = pygame.Rect(
                int(ball_x-BALL_R),
                int(ball_y-BALL_R),
                BALL_R*2,
                BALL_R*2
            )

            # walls
            if ball_x <= BALL_R:
                ball_x = BALL_R
                dx = abs(dx)
                sounds["wall"].play()

            if ball_x >= W-BALL_R:
                ball_x = W-BALL_R
                dx = -abs(dx)
                sounds["wall"].play()

            if ball_y <= 105:
                ball_y = 105 + BALL_R
                dy = abs(dy)
                sounds["wall"].play()

            # paddle
            if ball.colliderect(paddle) and dy > 0:
                ball_y = paddle.top - BALL_R

                relative = (
                    ball_x - paddle.centerx
                ) / (paddle.width / 2)

                dx = relative * speed
                dy = -abs(speed)

                sounds["paddle"].play()

            # boundary stones
            if mode == "BOUNDARY BREAKER":

                for stone in stones:

                    if ball.colliderect(stone):

                        if dy > 0 and ball.bottom - stone.top < 18:
                            ball_y = stone.top - BALL_R
                            dy = -abs(dy)

                        elif dy < 0 and stone.bottom - ball.top < 18:
                            ball_y = stone.bottom + BALL_R
                            dy = abs(dy)

                        elif dx > 0:
                            ball_x = stone.left - BALL_R
                            dx = -abs(dx)

                        else:
                            ball_x = stone.right + BALL_R
                            dx = abs(dx)

                        sounds["wall"].play()
                        break

            # bricks
            for brick in bricks[:]:

                if ball.colliderect(brick["rect"]):

                    brick["hp"] -= 1

                    if dy > 0:
                        ball_y = brick["rect"].top - BALL_R
                        dy = -abs(dy)
                    else:
                        ball_y = brick["rect"].bottom + BALL_R
                        dy = abs(dy)

                    sounds["brick"].play()

                    if brick["hp"] <= 0:
                        bricks.remove(brick)

                        # Coin goes to SCORE.
                        coins.append({
                            "x": float(brick["rect"].centerx),
                            "y": float(brick["rect"].centery),
                            "p": 0.0
                        })

                    break

            # lose life
            if ball_y > H + 30:

                lives -= 1
                sounds["lose"].play()

                if lives <= 0:
                    running = False
                    continue

                ball_x = W // 2
                ball_y = H - 105
                dx = random.choice([-1,1]) * speed * .75
                dy = -speed

            # clear
            if len(bricks) == 0 and not clear:
                clear = True
                sounds["clear"].play()

        # ------------------------------------------------
        # COINS
        # ------------------------------------------------
        for coin in coins[:]:

            coin["p"] += .045

            p = min(coin["p"], 1)

            coin["x"] = (
                coin["x"] +
                (280 - coin["x"]) * p
            )

            coin["y"] = (
                coin["y"] +
                (52 - coin["y"]) * p
            )

            if coin["p"] >= 1:
                score += 10
                sounds["coin"].play()
                coins.remove(coin)

        # ------------------------------------------------
        # STONES
        # ------------------------------------------------
        for stone in stones:
            rounded(
                screen, stone,
                (85, 92, 110),
                6,
                (175, 180, 190)
            )
            pygame.draw.line(
                screen, (45, 48, 60),
                stone.topleft, stone.bottomright, 2
            )

        # ------------------------------------------------
        # BRICKS
        # ------------------------------------------------
        for brick in bricks:
            r = brick["rect"]

            rounded(
                screen, r, brick["color"],
                8, (240,245,255)
            )

            pygame.draw.line(
                screen, (255,255,255),
                (r.left+8, r.top+7),
                (r.right-8, r.top+7), 2
            )

            if brick["hp"] == 2:
                pygame.draw.circle(
                    screen, (255,255,255),
                    r.center, 5
                )

        # ------------------------------------------------
        # PADDLE
        # ------------------------------------------------
        rounded(
            screen, paddle,
            THEMES[theme]["paddle"],
            10, (245,250,255)
        )

        pygame.draw.line(
            screen, (255,255,255),
            (paddle.left+15, paddle.top+5),
            (paddle.right-15, paddle.top+5), 3
        )

        # ------------------------------------------------
        # BALL
        # ------------------------------------------------
        pygame.draw.circle(
            screen, (255,255,255),
            (int(ball_x), int(ball_y)), BALL_R
        )

        pygame.draw.circle(
            screen, (120,220,255),
            (int(ball_x), int(ball_y)),
            BALL_R+5, 2
        )

        # ------------------------------------------------
        # COINS
        # ------------------------------------------------
        for coin in coins:
            pygame.draw.circle(
                screen, (255,205,40),
                (int(coin["x"]), int(coin["y"])), 11
            )
            pygame.draw.circle(
                screen, (255,245,130),
                (int(coin["x"]), int(coin["y"])), 7
            )

        # ------------------------------------------------
        # PAUSE
        # ------------------------------------------------
        if paused:
            overlay = pygame.Surface((W,H), pygame.SRCALPHA)
            overlay.fill((0,0,0,160))
            screen.blit(overlay, (0,0))

            text(screen, "PAUSED", font70,
                 (255,255,255), W//2, H//2-35, True)

            text(screen, "Press P to continue", font26,
                 (170,215,255), W//2, H//2+45, True)

        # ------------------------------------------------
        # STAGE CLEAR
        # ------------------------------------------------
        if clear:
            overlay = pygame.Surface((W,H), pygame.SRCALPHA)
            overlay.fill((0,0,0,170))
            screen.blit(overlay, (0,0))

            rounded(
                screen,
                pygame.Rect(300,205,600,360),
                (10,16,45),
                30,
                (100,190,255)
            )

            text(screen, "STAGE CLEAR!",
                 font48, (255,225,80),
                 W//2, 285, True)

            text(screen, "★   ★   ★",
                 font70, (255,215,70),
                 W//2, 385, True)

            text(screen, f"SCORE {score}",
                 font26, (255,255,255),
                 W//2, 465, True)

            text(screen, "Press R for next stage",
                 font20, (170,215,255),
                 W//2, 515, True)

        pygame.display.flip()

    pygame.quit()


# ============================================================
# TKINTER MENU
# ============================================================

class Menu:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Brick Breaker")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#07111f")

        self.theme = "SPACE"
        self.mode = "CLASSIC"
        self.difficulty = "NORMAL"

        self.main_screen()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def title(self, heading, sub):
        tk.Label(
            self.root,
            text=heading,
            font=("Arial", 40, "bold"),
            fg="#78d8ff",
            bg="#07111f"
        ).pack(pady=(65, 8))

        tk.Label(
            self.root,
            text=sub,
            font=("Arial", 16),
            fg="#94a8c0",
            bg="#07111f"
        ).pack(pady=(0, 35))

    def button(self, value, command):
        return tk.Button(
            self.root,
            text=value,
            command=command,
            font=("Arial", 19, "bold"),
            width=28,
            height=2,
            fg="white",
            bg="#132640",
            activebackground="#28527d",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2"
        )

    # ---------------- MAIN ----------------

    def main_screen(self):
        self.clear()

        self.title(
            "BRICK BREAKER",
            "Select each setting separately"
        )

        self.button(
            f"MODE       >       {self.mode}",
            self.mode_screen
        ).pack(pady=9)

        self.button(
            f"DIFFICULTY       >       {self.difficulty}",
            self.difficulty_screen
        ).pack(pady=9)

        self.button(
            f"THEME       >       {self.theme}",
            self.theme_screen
        ).pack(pady=9)

        tk.Button(
            self.root,
            text="START GAME",
            command=self.start,
            font=("Arial", 22, "bold"),
            width=28,
            height=2,
            fg="#06111f",
            bg="#62d8ff",
            activebackground="#91e5ff",
            relief="flat",
            bd=0,
            cursor="hand2"
        ).pack(pady=35)

        tk.Button(
            self.root,
            text="EXIT",
            command=self.root.destroy,
            font=("Arial", 13),
            fg="#91a4ba",
            bg="#07111f",
            activebackground="#07111f",
            activeforeground="white",
            relief="flat",
            bd=0
        ).pack()

        tk.Label(
            self.root,
            text="Pygame controls: LEFT / RIGHT or A / D     P = Pause     ESC = Exit",
            font=("Arial", 12),
            fg="#60728a",
            bg="#07111f"
        ).pack(side="bottom", pady=25)

    # ---------------- MODE ----------------

    def mode_screen(self):
        self.clear()

        self.title(
            "SELECT MODE",
            "Choose your Brick Breaker mode"
        )

        self.button(
            "CLASSIC BRICK BREAKER",
            lambda: self.select_mode("CLASSIC")
        ).pack(pady=12)

        self.button(
            "BOUNDARY BREAKER",
            lambda: self.select_mode("BOUNDARY BREAKER")
        ).pack(pady=12)

        self.button(
            "BACK",
            self.main_screen
        ).pack(pady=35)

    def select_mode(self, value):
        self.mode = value
        self.main_screen()

    # ---------------- DIFFICULTY ----------------

    def difficulty_screen(self):
        self.clear()

        self.title(
            "SELECT DIFFICULTY",
            "Choose the ball speed and number of lives"
        )

        self.button(
            "EASY",
            lambda: self.select_difficulty("EASY")
        ).pack(pady=10)

        self.button(
            "NORMAL",
            lambda: self.select_difficulty("NORMAL")
        ).pack(pady=10)

        self.button(
            "HARD",
            lambda: self.select_difficulty("HARD")
        ).pack(pady=10)

        self.button(
            "BACK",
            self.main_screen
        ).pack(pady=35)

    def select_difficulty(self, value):
        self.difficulty = value
        self.main_screen()

    # ---------------- THEME ----------------

    def theme_screen(self):
        self.clear()

        self.title(
            "SELECT THEME",
            "Choose your game world"
        )

        self.button(
            "SPACE",
            lambda: self.select_theme("SPACE")
        ).pack(pady=9)

        self.button(
            "VOLCANO",
            lambda: self.select_theme("VOLCANO")
        ).pack(pady=9)

        self.button(
            "FOREST",
            lambda: self.select_theme("FOREST")
        ).pack(pady=9)

        self.button(
            "BACK",
            self.main_screen
        ).pack(pady=30)

    def select_theme(self, value):
        self.theme = value
        self.main_screen()

    # ---------------- START ----------------

    def start(self):
        self.root.withdraw()

        try:
            process = subprocess.Popen([
                sys.executable,
                os.path.abspath(__file__),
                "--game",
                self.theme,
                self.mode,
                self.difficulty
            ])

            self.check_process(process)

        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("Error", str(e))

    def check_process(self, process):
        if process.poll() is None:
            self.root.after(
                250,
                lambda: self.check_process(process)
            )
        else:
            self.root.deiconify()
            self.main_screen()

    def run(self):
        self.root.mainloop()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) >= 5 and sys.argv[1] == "--game":
        play_game(
            sys.argv[2],
            sys.argv[3],
            sys.argv[4]
        )
    else:
        Menu().run()
