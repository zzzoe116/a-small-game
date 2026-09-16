# -*- coding: utf-8 -*-
"""
一箭又一箭 (OneArrowAgain)
基于 Python + Pygame 开发的单格箭头益智解谜游戏

操作：鼠标点击箭头
规则：箭头前方无阻挡则飞出棋盘；有阻挡则碰撞并消耗一次失误机会
"""

import pygame
import sys
import math
import os

# ==================== 基础配置 ====================
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# 资源路径
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

# 颜色
BG_COLOR       = (28, 36, 52)
TOP_BAR_BG     = (20, 28, 42)
BOARD_BG       = (45, 58, 80)
CELL_BG        = (62, 80, 108)
CELL_BORDER    = (95, 125, 165)
ARROW_COLOR    = (245, 215, 100)
ARROW_FAIL     = (245, 95, 95)
TEXT_COLOR     = (235, 240, 250)
TEXT_DIM       = (150, 165, 185)
BUTTON_BG      = (75, 125, 190)
BUTTON_HOVER   = (105, 155, 220)
BUTTON_TEXT    = (255, 255, 255)
HEART_RED      = (230, 70, 90)
HEART_GRAY     = (75, 80, 92)
GOLD           = (255, 210, 70)
GREEN          = (95, 205, 135)
RED            = (235, 95, 95)

# 方向向量 (dr, dc)
DIRECTIONS = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1),
}

# 棋盘布局
CELL_SIZE       = 80
BOARD_TOP       = 130
BOARD_BOTTOM    = 620
BOARD_CENTER_Y  = (BOARD_TOP + BOARD_BOTTOM) // 2

# ==================== 关卡数据 ====================
# None 表示空格；'U'/'D'/'L'/'R' 表示四个方向的箭头
LEVELS = [
    # 关卡 1：3x3 满格，基础交错（非常简单）
    # 通关思路：先点最右侧的 R 飞出去，再依次点 L，最后点剩下的 R
    [
        ['R', 'R', 'R'],
        ['L', 'L', 'L'],
        ['R', 'R', 'R'],
    ],
    # 关卡 2：4x4 满格，按列交错（中等）
    # 通关思路：第 0 列全向上飞，第 1 列全向下飞，第 2 列全向上飞，第 3 列全向下飞
    [
        ['U', 'D', 'U', 'D'],
        ['U', 'D', 'U', 'D'],
        ['U', 'D', 'U', 'D'],
        ['U', 'D', 'U', 'D'],
    ],
    # 关卡 3：4x4 满格，按行交错（较难）
    # 通关思路：第 0 行全向上飞，第 1 行全向右飞，第 2 行全向左飞，第 3 行全向下飞
    [
        ['U', 'U', 'U', 'U'],
        ['R', 'R', 'R', 'R'],
        ['L', 'L', 'L', 'L'],
        ['D', 'D', 'D', 'D'],
    ],
    # 关卡 4：5x5 满格，行列混合（难）
    # 通关思路：与第 3 关类似，但增加了行数，需要依次清空每一行
    [
        ['U', 'U', 'U', 'U', 'U'],
        ['R', 'R', 'R', 'R', 'R'],
        ['L', 'L', 'L', 'L', 'L'],
        ['D', 'D', 'D', 'D', 'D'],
        ['R', 'R', 'R', 'R', 'R'],
    ],
    # 关卡 5：5x5 满格，螺旋矩阵（最难，非常巧妙）
    # 通关思路：从最外圈开始，按顺时针方向一层层往里清，最后清空中心点
    # 顺序：外圈 R -> D -> L -> U，内圈 R -> D -> L -> U，最后中间 R
    [
        ['R', 'R', 'R', 'R', 'R'],
        ['U', 'R', 'R', 'R', 'D'],
        ['U', 'U', 'R', 'D', 'D'],
        ['U', 'L', 'L', 'D', 'D'],
        ['L', 'L', 'L', 'L', 'D'],
    ],
]

# ==================== 资源加载工具 ====================
def load_audio(filename):
    """加载音频文件，若不存在则返回 None"""
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except pygame.error:
            print(f"无法加载音频: {path}")
    return None

# 修改 load_image 函数
def load_image(filename, size=None):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        print(f"✅ 成功找到图片: {path}")  # <--- 加这句
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except pygame.error as e:
            print(f"❌ 图片加载失败: {e}")  # <--- 加这句
    else:
        print(f"❌ 找不到图片: {path}")    # <--- 加这句
    return None

# 修改 play_bgm 函数
def play_bgm():
    bgm_path = os.path.join(ASSETS_DIR, 'bgm.mp3') # 如果转了wav，这里改成 'bgm.wav'
    if os.path.exists(bgm_path):
        print(f"✅ 成功找到BGM: {bgm_path}")  # <--- 加这句
        try:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(0.8)  # 调大音量到80%测试
            pygame.mixer.music.play(-1)
            print("✅ BGM 开始播放")  # <--- 加这句
        except pygame.error as e:
            print(f"❌ BGM播放失败: {e}")  # <--- 加这句
    else:
        print(f"❌ 找不到BGM: {bgm_path}")  # <--- 加这句

# ==================== 字体工具 ====================
_font_cache = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        font_path = None
        possible_fonts = [
            'C:/Windows/Fonts/msyh.ttc',   # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf', # 黑体
            'C:/Windows/Fonts/simsun.ttc'  # 宋体
        ]
        for p in possible_fonts:
            if os.path.exists(p):
                font_path = p
                break
        
        if font_path:
            _font_cache[key] = pygame.font.Font(font_path, size)
        else:
            _font_cache[key] = pygame.font.Font(None, size)
            
        if bold:
            _font_cache[key].set_bold(True)
            
    return _font_cache[key]

def draw_text(screen, text, size, x, y, color=TEXT_COLOR,
              center=True, bold=False, alpha=255):
    font = get_font(size, bold)
    surf = font.render(text, True, color)
    if alpha < 255:
        surf.set_alpha(alpha)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)
    return rect

def draw_button(screen, text, rect, mouse_pos, font_size=26):
    hovered = rect.collidepoint(mouse_pos)
    color = BUTTON_HOVER if hovered else BUTTON_BG
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, (255, 255, 255, 60), rect, 2, border_radius=12)
    draw_text(screen, text, font_size, rect.centerx, rect.centery, BUTTON_TEXT)

def draw_heart(screen, cx, cy, size, color):
    r = size / 2
    pygame.draw.circle(screen, color, (int(cx - r * 0.5), int(cy - r * 0.35)), int(r * 0.55))
    pygame.draw.circle(screen, color, (int(cx + r * 0.5), int(cy - r * 0.35)), int(r * 0.55))
    pygame.draw.polygon(screen, color, [
        (cx - r * 1.02, cy - r * 0.10),
        (cx + r * 1.02, cy - r * 0.10),
        (cx, cy + r * 1.15),
    ])

def draw_arrow(screen, cx, cy, direction, size, color=ARROW_COLOR, alpha=255):
    half = size / 2
    hl = half * 0.90
    wg = half * 0.85
    sh = half * 0.30

    if direction == 'R':
        pts = [(cx + half, cy), (cx + half - hl, cy - wg), (cx + half - hl, cy - sh),
               (cx - half, cy - sh), (cx - half, cy + sh), (cx + half - hl, cy + sh), (cx + half - hl, cy + wg)]
    elif direction == 'L':
        pts = [(cx - half, cy), (cx - half + hl, cy - wg), (cx - half + hl, cy - sh),
               (cx + half, cy - sh), (cx + half, cy + sh), (cx - half + hl, cy + sh), (cx - half + hl, cy + wg)]
    elif direction == 'U':
        pts = [(cx, cy - half), (cx - wg, cy - half + hl), (cx - sh, cy - half + hl),
               (cx - sh, cy + half), (cx + sh, cy + half), (cx + sh, cy - half + hl), (cx + wg, cy - half + hl)]
    elif direction == 'D':
        pts = [(cx, cy + half), (cx - wg, cy + half - hl), (cx - sh, cy + half - hl),
               (cx - sh, cy - half), (cx + sh, cy - half), (cx + sh, cy + half - hl), (cx + wg, cy + half - hl)]
    else:
        return

    if alpha >= 255:
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, (255, 255, 255, 90), pts, 2)
    else:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        minx, maxx = min(xs) - 2, max(xs) + 2
        miny, maxy = min(ys) - 2, max(ys) + 2
        w, h = int(maxx - minx), int(maxy - miny)
        if w <= 0 or h <= 0: return
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        local_pts = [(p[0] - minx, p[1] - miny) for p in pts]
        pygame.draw.polygon(surf, (*color, alpha), local_pts)
        screen.blit(surf, (minx, miny))

def draw_star(screen, cx, cy, size, color):
    pts = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = size if i % 2 == 0 else size * 0.42
        pts.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    pygame.draw.polygon(screen, color, pts)

# ==================== 游戏主类 ====================
class Game:
    def __init__(self):
        self.state = 'menu'
        self.level_index = 0
        self.board = []
        self.max_mistakes = 3
        self.mistakes_left = 3
        self.flying = []
        self.shaking = {}
        self.message = ''
        self.message_timer = 0.0
        self.time_elapsed = 0.0

        # 加载资源 (音效和图片)
        self.bg_menu_img = load_image('bg_menu.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.bg_game_img = load_image('bg_game.png', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.click_sound = load_audio('click.mp3')
        self.error_sound = load_audio('error.mp3')

        # 按钮矩形
        self.btn_start     = pygame.Rect(SCREEN_WIDTH // 2 - 130, 440, 260, 64)
        self.btn_restart   = pygame.Rect(SCREEN_WIDTH // 2 - 140, 635, 130, 44)
        self.btn_menu_game = pygame.Rect(SCREEN_WIDTH // 2 + 10, 635, 130, 44)
        self.btn_primary   = pygame.Rect(SCREEN_WIDTH // 2 - 120, 470, 240, 56)
        self.btn_secondary = pygame.Rect(SCREEN_WIDTH // 2 - 120, 545, 240, 56)

    # ---------- 状态管理 ----------
    def start_game(self):
        self.load_level(0)
        self.state = 'playing'

    def load_level(self, idx):
        self.level_index = idx
        self.board = [row[:] for row in LEVELS[idx]]
        self.mistakes_left = self.max_mistakes
        self.flying = []
        self.shaking = {}
        self.message = ''
        self.message_timer = 0.0
        self.time_elapsed = 0.0

    # ---------- 棋盘工具 ----------
    def count_arrows(self):
        return sum(1 for row in self.board for cell in row if cell is not None)

    def board_geometry(self):
        n = len(self.board)
        size = n * CELL_SIZE
        x0 = (SCREEN_WIDTH - size) // 2
        y0 = BOARD_CENTER_Y - size // 2
        return x0, y0, CELL_SIZE

    def cell_at(self, pos):
        if not self.board: return None
        x0, y0, cs = self.board_geometry()
        n = len(self.board)
        mx, my = pos
        if not (x0 <= mx < x0 + n * cs and y0 <= my < y0 + n * cs): return None
        col = (mx - x0) // cs
        row = (my - y0) // cs
        return int(row), int(col)

    def is_blocked(self, row, col):
        d = self.board[row][col]
        if d is None: return False
        dr, dc = DIRECTIONS[d]
        n = len(self.board)
        r, c = row + dr, col + dc
        while 0 <= r < n and 0 <= c < n:
            if self.board[r][c] is not None: return True
            r += dr; c += dc
        return False

    # ---------- 点击处理 ----------
    def handle_click(self, pos):
        if self.state == 'menu':
            if self.btn_start.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.start_game()

        elif self.state == 'playing':
            if self.btn_restart.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.load_level(self.level_index)
            elif self.btn_menu_game.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.state = 'menu'
            else:
                self.try_click_cell(pos)

        elif self.state == 'level_clear':
            if self.btn_primary.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.load_level(self.level_index + 1)
                self.state = 'playing'
            elif self.btn_secondary.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.state = 'menu'

        elif self.state == 'game_over':
            if self.btn_primary.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.load_level(self.level_index)
                self.state = 'playing'
            elif self.btn_secondary.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.state = 'menu'

        elif self.state == 'all_clear':
            if self.btn_secondary.collidepoint(pos):
                if self.click_sound: self.click_sound.play()
                self.level_index = 0
                self.state = 'menu'

    def try_click_cell(self, pos):
        cell = self.cell_at(pos)
        if cell is None: return
        r, c = cell
        if self.board[r][c] is None: return

        if self.is_blocked(r, c):
            # ---- 被阻挡 ----
            if self.error_sound: self.error_sound.play()  # 播放错误音效
            self.mistakes_left -= 1
            self.shaking[(r, c)] = 0.5
            self.message = '前方有阻挡！'
            self.message_timer = 1.0
            if self.mistakes_left <= 0:
                self.state = 'game_over'
        else:
            # ---- 无阻挡 ----
            if self.click_sound: self.click_sound.play()  # 播放点击音效
            x0, y0, cs = self.board_geometry()
            cx = x0 + c * cs + cs // 2
            cy = y0 + r * cs + cs // 2
            d = self.board[r][c]
            self.flying.append({'x': cx, 'y': cy, 'dir': d, 'alpha': 255})
            self.board[r][c] = None

            if self.count_arrows() == 0:
                if self.level_index + 1 >= len(LEVELS):
                    self.state = 'all_clear'
                else:
                    self.state = 'level_clear'

    # ---------- 每帧更新 ----------
    def update(self, dt):
        alive = []
        for f in self.flying:
            dr, dc = DIRECTIONS[f['dir']]
            speed = 800
            f['x'] += dc * speed * dt
            f['y'] += dr * speed * dt
            f['alpha'] -= 350 * dt
            if f['alpha'] > 0: alive.append(f)
        self.flying = alive

        for k in list(self.shaking.keys()):
            self.shaking[k] -= dt
            if self.shaking[k] <= 0: del self.shaking[k]

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0: self.message = ''

        if self.state == 'playing':
            self.time_elapsed += dt

    # ==================== 绘制 ====================
    def draw(self, screen, mouse_pos):
        if self.state == 'menu':
            self.draw_menu(screen, mouse_pos)
        elif self.state == 'playing':
            self.draw_playing(screen, mouse_pos)
        elif self.state == 'level_clear':
            self.draw_playing(screen, mouse_pos)
            self.draw_result_overlay(screen, mouse_pos, '关卡通关！', GREEN, '进入下一关', True)
        elif self.state == 'game_over':
            self.draw_playing(screen, mouse_pos)
            self.draw_result_overlay(screen, mouse_pos, '挑战失败', RED, '重新挑战', False)
        elif self.state == 'all_clear':
            self.draw_all_clear(screen, mouse_pos)

    # ---------- 开始界面 ----------
    def draw_menu(self, screen, mouse_pos):
        # 1. 渲染背景图
        if self.bg_menu_img:
            screen.blit(self.bg_menu_img, (0, 0))
            # 加一层半透明黑幕，防止背景太亮看不清文字
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 0))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(BG_COLOR)

        # 2. 绘制标题文字和按钮
        draw_text(screen, '一 箭 又 一 箭', 78, SCREEN_WIDTH // 2, 200, GOLD, bold=True)
        draw_text(screen, 'OneArrowAgain', 26, SCREEN_WIDTH // 2, 260, TEXT_DIM)

        draw_text(screen, '规则说明', 24, SCREEN_WIDTH // 2, 320, TEXT_COLOR, bold=True)
        draw_text(screen, '点击箭头，若前方无阻挡，它会飞出棋盘；', 20, SCREEN_WIDTH // 2, 358, TEXT_DIM)
        draw_text(screen, '若前方有阻挡，则会撞击并消耗一次失误机会。', 20, SCREEN_WIDTH // 2, 388, TEXT_DIM)
        draw_text(screen, '每关有 3 次失误机会，清空全部箭头即可通关。', 20, SCREEN_WIDTH // 2, 418, TEXT_DIM)

        draw_button(screen, '开 始 游 戏', self.btn_start, mouse_pos, font_size=30)

    # ---------- 游戏界面 ----------
    def draw_playing(self, screen, mouse_pos):
        if self.bg_game_img:
            screen.blit(self.bg_game_img, (0, 0))
        pygame.draw.rect(screen, TOP_BAR_BG, (0, 0, SCREEN_WIDTH, 112))
        pygame.draw.line(screen, (55, 75, 105), (0, 112), (SCREEN_WIDTH, 112), 2)

        draw_text(screen, f'关卡 {self.level_index + 1} / {len(LEVELS)}', 26, 40, 40, TEXT_COLOR, center=False, bold=True)
        draw_text(screen, f'时间: {int(self.time_elapsed)} s', 20, 40, 78, TEXT_DIM, center=False)
        draw_text(screen, f'剩余箭头: {self.count_arrows()}', 28, SCREEN_WIDTH // 2, 55, TEXT_COLOR, bold=True)

        draw_text(screen, '失误:', 22, 640, 45, TEXT_COLOR, center=False)
        for i in range(self.max_mistakes):
            color = HEART_RED if i < self.mistakes_left else HEART_GRAY
            draw_heart(screen, 715 + i * 42, 55, 30, color)

        self.draw_board(screen)

        for f in self.flying:
            draw_arrow(screen, f['x'], f['y'], f['dir'], CELL_SIZE * 0.72, alpha=int(f['alpha']))

        if self.message:
            alpha = max(0, min(255, int(255 * self.message_timer)))
            draw_text(screen, self.message, 30, SCREEN_WIDTH // 2, 165, RED, bold=True, alpha=alpha)

        draw_button(screen, '重新开始', self.btn_restart, mouse_pos, font_size=22)
        draw_button(screen, '返回主菜单', self.btn_menu_game, mouse_pos, font_size=22)

    def draw_board(self, screen):
        if not self.board: return
        n = len(self.board)
        x0, y0, cs = self.board_geometry()

        pygame.draw.rect(screen, BOARD_BG, (x0 - 12, y0 - 12, n * cs + 24, n * cs + 24), border_radius=18)

        for r in range(n):
            for c in range(n):
                x = x0 + c * cs
                y = y0 + r * cs
                rect = pygame.Rect(x + 3, y + 3, cs - 6, cs - 6)
                pygame.draw.rect(screen, CELL_BG, rect, border_radius=10)
                pygame.draw.rect(screen, CELL_BORDER, rect, 2, border_radius=10)

                if self.board[r][c]:
                    off = 0
                    is_shaking = (r, c) in self.shaking
                    if is_shaking:
                        rem = self.shaking[(r, c)]
                        prog = rem / 0.5
                        off = math.sin((0.5 - rem) * 60) * 9 * prog

                    color = ARROW_FAIL if is_shaking else ARROW_COLOR
                    draw_arrow(screen, x + cs // 2 + off, y + cs // 2, self.board[r][c], cs * 0.72, color=color)

    # ---------- 结算界面 ----------
    def draw_result_overlay(self, screen, mouse_pos, title, title_color, primary_text, is_next):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(SCREEN_WIDTH // 2 - 220, 230, 440, 400)
        pygame.draw.rect(screen, (40, 52, 74), panel, border_radius=20)
        pygame.draw.rect(screen, (90, 120, 160), panel, 3, border_radius=20)

        draw_text(screen, title, 54, SCREEN_WIDTH // 2, 310, title_color, bold=True)

        if is_next:
            draw_text(screen, f'关卡 {self.level_index + 1} 完成！', 22, SCREEN_WIDTH // 2, 375, TEXT_DIM)
        else:
            draw_text(screen, '失误次数已耗尽', 22, SCREEN_WIDTH // 2, 375, TEXT_DIM)

        draw_text(screen, f'用时: {int(self.time_elapsed)} 秒', 22, SCREEN_WIDTH // 2, 410, TEXT_COLOR)

        draw_button(screen, primary_text, self.btn_primary, mouse_pos)
        draw_button(screen, '返回主菜单', self.btn_secondary, mouse_pos, font_size=24)

    def draw_all_clear(self, screen, mouse_pos):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(SCREEN_WIDTH // 2 - 240, 200, 480, 430)
        pygame.draw.rect(screen, (40, 52, 74), panel, border_radius=20)
        pygame.draw.rect(screen, GOLD, panel, 3, border_radius=20)

        draw_text(screen, '全部通关！', 62, SCREEN_WIDTH // 2, 285, GOLD, bold=True)
        draw_text(screen, '恭喜你完成了所有关卡', 24, SCREEN_WIDTH // 2, 355, TEXT_COLOR)
        draw_text(screen, f'共 {len(LEVELS)} 关，总用时 {int(self.time_elapsed)} 秒', 20, SCREEN_WIDTH // 2, 400, TEXT_DIM)

        for i in range(3):
            cx = SCREEN_WIDTH // 2 - 70 + i * 70
            draw_star(screen, cx, 470, 26, GOLD)

        draw_button(screen, '返回主菜单', self.btn_secondary, mouse_pos, font_size=24)


# ==================== 程序入口 ====================
def main():
    pygame.init()
    
    # 初始化音频混合器（必须在 pygame.init() 之后）
    try:
        pygame.mixer.init()
        play_bgm()  # 开始播放背景音乐
    except pygame.error:
        print("音频设备初始化失败，将不播放声音。")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('一箭又一箭 - OneArrowAgain')
    clock = pygame.time.Clock()

    game = Game()
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        game.update(dt)

        screen.fill(BG_COLOR)
        game.draw(screen, mouse_pos)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()name__ == '__main__':
    main()
