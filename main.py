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
import os   # <--- 新增这一行

# ==================== 基础配置 ====================
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

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
    # 关卡 1：3x3 简单
    [
        [None, None, 'R'],
        [None, 'U', None],
        ['L', None, None],
    ],
    # 关卡 2：4x4 中等
    [
        [None, 'R', None, None],
        ['L', None, 'R', None],
        [None, None, 'U', 'U'],
        [None, None, None, 'D'],
    ],
    # 关卡 3：5x5 较难
    [
        ['R', None, None, None, None],
        [None, 'U', None, None, 'L'],
        [None, None, 'U', 'D', None],
        ['R', None, None, None, None],
        [None, 'U', None, None, 'L'],
    ],
]

# ==================== 字体工具 ====================
_font_cache = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        # 直接加载 Windows 系统中的中文字体文件，绕过 SysFont 的兼容性问题
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
            # 如果系统缺少上述中文字体，则回退到默认字体
            _font_cache[key] = pygame.font.Font(None, size)
            
        if bold:
            _font_cache[key].set_bold(True)
            
    return _font_cache[key]
def draw_text(screen, text, size, x, y, color=TEXT_COLOR,
              center=True, bold=False, alpha=255):
    """在屏幕上绘制文字，返回文字矩形"""
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
    """绘制按钮，鼠标悬停时变色"""
    hovered = rect.collidepoint(mouse_pos)
    color = BUTTON_HOVER if hovered else BUTTON_BG
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, (255, 255, 255, 60), rect, 2, border_radius=12)
    draw_text(screen, text, font_size, rect.centerx, rect.centery, BUTTON_TEXT)


def draw_heart(screen, cx, cy, size, color):
    """绘制心形（用两个圆 + 一个三角形拼成）"""
    r = size / 2
    pygame.draw.circle(screen, color,
                       (int(cx - r * 0.5), int(cy - r * 0.35)), int(r * 0.55))
    pygame.draw.circle(screen, color,
                       (int(cx + r * 0.5), int(cy - r * 0.35)), int(r * 0.55))
    pygame.draw.polygon(screen, color, [
        (cx - r * 1.02, cy - r * 0.10),
        (cx + r * 1.02, cy - r * 0.10),
        (cx, cy + r * 1.15),
    ])


def draw_arrow(screen, cx, cy, direction, size,
               color=ARROW_COLOR, alpha=255):
    """绘制一个箭头（多边形），支持透明度"""
    half = size / 2
    hl = half * 0.90   # 箭头头部长度
    wg = half * 0.85   # 箭头翼展
    sh = half * 0.30   # 箭杆半宽

    if direction == 'R':
        pts = [(cx + half, cy),
               (cx + half - hl, cy - wg),
               (cx + half - hl, cy - sh),
               (cx - half, cy - sh),
               (cx - half, cy + sh),
               (cx + half - hl, cy + sh),
               (cx + half - hl, cy + wg)]
    elif direction == 'L':
        pts = [(cx - half, cy),
               (cx - half + hl, cy - wg),
               (cx - half + hl, cy - sh),
               (cx + half, cy - sh),
               (cx + half, cy + sh),
               (cx - half + hl, cy + sh),
               (cx - half + hl, cy + wg)]
    elif direction == 'U':
        pts = [(cx, cy - half),
               (cx - wg, cy - half + hl),
               (cx - sh, cy - half + hl),
               (cx - sh, cy + half),
               (cx + sh, cy + half),
               (cx + sh, cy - half + hl),
               (cx + wg, cy - half + hl)]
    elif direction == 'D':
        pts = [(cx, cy + half),
               (cx - wg, cy + half - hl),
               (cx - sh, cy + half - hl),
               (cx - sh, cy - half),
               (cx + sh, cy - half),
               (cx + sh, cy + half - hl),
               (cx + wg, cy + half - hl)]
    else:
        return

    if alpha >= 255:
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, (255, 255, 255, 90), pts, 2)
    else:
        # 局部 Surface 实现透明绘制
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        minx, maxx = min(xs) - 2, max(xs) + 2
        miny, maxy = min(ys) - 2, max(ys) + 2
        w, h = int(maxx - minx), int(maxy - miny)
        if w <= 0 or h <= 0:
            return
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        local_pts = [(p[0] - minx, p[1] - miny) for p in pts]
        pygame.draw.polygon(surf, (*color, alpha), local_pts)
        screen.blit(surf, (minx, miny))


# ==================== 游戏主类 ====================
class Game:
    def __init__(self):
        self.state = 'menu'          # menu / playing / level_clear / game_over / all_clear
        self.level_index = 0
        self.board = []
        self.max_mistakes = 3
        self.mistakes_left = 3
        self.flying = []             # 飞行动画列表
        self.shaking = {}            # (r, c) -> 剩余抖动时间
        self.message = ''
        self.message_timer = 0.0
        self.time_elapsed = 0.0

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
        src = LEVELS[idx]
        self.board = [row[:] for row in src]
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
        if not self.board:
            return None
        x0, y0, cs = self.board_geometry()
        n = len(self.board)
        mx, my = pos
        if not (x0 <= mx < x0 + n * cs and y0 <= my < y0 + n * cs):
            return None
        col = (mx - x0) // cs
        row = (my - y0) // cs
        return int(row), int(col)

    def is_blocked(self, row, col):
        """判断 (row, col) 处的箭头前方是否有阻挡"""
        d = self.board[row][col]
        if d is None:
            return False
        dr, dc = DIRECTIONS[d]
        n = len(self.board)
        r, c = row + dr, col + dc
        while 0 <= r < n and 0 <= c < n:
            if self.board[r][c] is not None:
                return True
            r += dr
            c += dc
        return False

    # ---------- 点击处理 ----------
    def handle_click(self, pos):
        if self.state == 'menu':
            if self.btn_start.collidepoint(pos):
                self.start_game()

        elif self.state == 'playing':
            if self.btn_restart.collidepoint(pos):
                self.load_level(self.level_index)
            elif self.btn_menu_game.collidepoint(pos):
                self.state = 'menu'
            else:
                self.try_click_cell(pos)

        elif self.state == 'level_clear':
            if self.btn_primary.collidepoint(pos):
                self.load_level(self.level_index + 1)
                self.state = 'playing'
            elif self.btn_secondary.collidepoint(pos):
                self.state = 'menu'

        elif self.state == 'game_over':
            if self.btn_primary.collidepoint(pos):
                self.load_level(self.level_index)
                self.state = 'playing'
            elif self.btn_secondary.collidepoint(pos):
                self.state = 'menu'

        elif self.state == 'all_clear':
            if self.btn_secondary.collidepoint(pos):
                self.level_index = 0
                self.state = 'menu'

    def try_click_cell(self, pos):
        cell = self.cell_at(pos)
        if cell is None:
            return
        r, c = cell
        if self.board[r][c] is None:
            return

        if self.is_blocked(r, c):
            # ---- 被阻挡：扣失误、抖动、提示 ----
            self.mistakes_left -= 1
            self.shaking[(r, c)] = 0.5
            self.message = '前方有阻挡！'
            self.message_timer = 1.0
            if self.mistakes_left <= 0:
                self.state = 'game_over'
        else:
            # ---- 无阻挡：飞出棋盘 ----
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
        # 飞行动画
        alive = []
        for f in self.flying:
            dr, dc = DIRECTIONS[f['dir']]
            speed = 800
            f['x'] += dc * speed * dt
            f['y'] += dr * speed * dt
            f['alpha'] -= 350 * dt
            if f['alpha'] > 0:
                alive.append(f)
        self.flying = alive

        # 抖动动画
        for k in list(self.shaking.keys()):
            self.shaking[k] -= dt
            if self.shaking[k] <= 0:
                del self.shaking[k]

        # 文字提示
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ''

        # 计时
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
            self.draw_result_overlay(screen, mouse_pos,
                                     '关卡通关！', GREEN,
                                     '进入下一关', True)
        elif self.state == 'game_over':
            self.draw_playing(screen, mouse_pos)
            self.draw_result_overlay(screen, mouse_pos,
                                     '挑战失败', RED,
                                     '重新挑战', False)
        elif self.state == 'all_clear':
            self.draw_all_clear(screen, mouse_pos)

    # ---------- 开始界面 ----------
    def draw_menu(self, screen, mouse_pos):
        # 装饰性箭头
        draw_arrow(screen, 180, 560, 'R', 70, (60, 80, 110))
        draw_arrow(screen, 720, 560, 'L', 70, (60, 80, 110))
        draw_arrow(screen, 180, 130, 'U', 70, (60, 80, 110))
        draw_arrow(screen, 720, 130, 'D', 70, (60, 80, 110))

        draw_text(screen, '一 箭 又 一 箭', 78, SCREEN_WIDTH // 2, 200, GOLD, bold=True)
        draw_text(screen, 'OneArrowAgain', 26, SCREEN_WIDTH // 2, 260, TEXT_DIM)

        draw_text(screen, '规则说明', 24, SCREEN_WIDTH // 2, 320, TEXT_COLOR, bold=True)
        draw_text(screen, '点击箭头，若前方无阻挡，它会飞出棋盘；', 20,
                  SCREEN_WIDTH // 2, 358, TEXT_DIM)
        draw_text(screen, '若前方有阻挡，则会撞击并消耗一次失误机会。', 20,
                  SCREEN_WIDTH // 2, 388, TEXT_DIM)
        draw_text(screen, '每关有 3 次失误机会，清空全部箭头即可通关。', 20,
                  SCREEN_WIDTH // 2, 418, TEXT_DIM)

        draw_button(screen, '开 始 游 戏', self.btn_start, mouse_pos, font_size=30)

    # ---------- 游戏界面 ----------
    def draw_playing(self, screen, mouse_pos):
        # 顶部信息栏
        pygame.draw.rect(screen, TOP_BAR_BG, (0, 0, SCREEN_WIDTH, 112))
        pygame.draw.line(screen, (55, 75, 105),
                         (0, 112), (SCREEN_WIDTH, 112), 2)

        draw_text(screen, f'关卡 {self.level_index + 1} / {len(LEVELS)}',
                  26, 40, 40, TEXT_COLOR, center=False, bold=True)
        draw_text(screen, f'时间: {int(self.time_elapsed)} s',
                  20, 40, 78, TEXT_DIM, center=False)

        draw_text(screen, f'剩余箭头: {self.count_arrows()}',
                  28, SCREEN_WIDTH // 2, 55, TEXT_COLOR, bold=True)

        # 失误次数（心形）
        draw_text(screen, '失误:', 22, 640, 45, TEXT_COLOR, center=False)
        for i in range(self.max_mistakes):
            color = HEART_RED if i < self.mistakes_left else HEART_GRAY
            draw_heart(screen, 715 + i * 42, 55, 30, color)

        # 棋盘
        self.draw_board(screen)

        # 飞行动画
        for f in self.flying:
            draw_arrow(screen, f['x'], f['y'], f['dir'],
                       CELL_SIZE * 0.72, alpha=int(f['alpha']))

        # 文字提示
        if self.message:
            alpha = max(0, min(255, int(255 * self.message_timer)))
            draw_text(screen, self.message, 30, SCREEN_WIDTH // 2, 165,
                      RED, bold=True, alpha=alpha)

        # 底部按钮
        draw_button(screen, '重新开始', self.btn_restart, mouse_pos, font_size=22)
        draw_button(screen, '返回主菜单', self.btn_menu_game, mouse_pos, font_size=22)

    def draw_board(self, screen):
        if not self.board:
            return
        n = len(self.board)
        x0, y0, cs = self.board_geometry()

        # 棋盘底板
        pygame.draw.rect(screen, BOARD_BG,
                         (x0 - 12, y0 - 12, n * cs + 24, n * cs + 24),
                         border_radius=18)

        for r in range(n):
            for c in range(n):
                x = x0 + c * cs
                y = y0 + r * cs
                rect = pygame.Rect(x + 3, y + 3, cs - 6, cs - 6)
                pygame.draw.rect(screen, CELL_BG, rect, border_radius=10)
                pygame.draw.rect(screen, CELL_BORDER, rect, 2, border_radius=10)

                if self.board[r][c]:
                    # 抖动偏移
                    off = 0
                    is_shaking = (r, c) in self.shaking
                    if is_shaking:
                        rem = self.shaking[(r, c)]
                        prog = rem / 0.5
                        off = math.sin((0.5 - rem) * 60) * 9 * prog

                    color = ARROW_FAIL if is_shaking else ARROW_COLOR
                    draw_arrow(screen, x + cs // 2 + off, y + cs // 2,
                               self.board[r][c], cs * 0.72, color=color)

    # ---------- 结算界面 ----------
    def draw_result_overlay(self, screen, mouse_pos,
                            title, title_color, primary_text, is_next):
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 面板
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 220, 230, 440, 400)
        pygame.draw.rect(screen, (40, 52, 74), panel, border_radius=20)
        pygame.draw.rect(screen, (90, 120, 160), panel, 3, border_radius=20)

        draw_text(screen, title, 54, SCREEN_WIDTH // 2, 310,
                  title_color, bold=True)

        if is_next:
            draw_text(screen, f'关卡 {self.level_index + 1} 完成！', 22,
                      SCREEN_WIDTH // 2, 375, TEXT_DIM)
        else:
            draw_text(screen, '失误次数已耗尽', 22,
                      SCREEN_WIDTH // 2, 375, TEXT_DIM)

        draw_text(screen, f'用时: {int(self.time_elapsed)} 秒', 22,
                  SCREEN_WIDTH // 2, 410, TEXT_COLOR)

        # 按钮
        draw_button(screen, primary_text, self.btn_primary, mouse_pos)
        draw_button(screen, '返回主菜单', self.btn_secondary, mouse_pos, font_size=24)

    def draw_all_clear(self, screen, mouse_pos):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(SCREEN_WIDTH // 2 - 240, 200, 480, 430)
        pygame.draw.rect(screen, (40, 52, 74), panel, border_radius=20)
        pygame.draw.rect(screen, GOLD, panel, 3, border_radius=20)

        draw_text(screen, '全部通关！', 62, SCREEN_WIDTH // 2, 285,
                  GOLD, bold=True)
        draw_text(screen, '恭喜你完成了所有关卡', 24,
                  SCREEN_WIDTH // 2, 355, TEXT_COLOR)
        draw_text(screen, f'共 {len(LEVELS)} 关，总用时 {int(self.time_elapsed)} 秒',
                  20, SCREEN_WIDTH // 2, 400, TEXT_DIM)

        # 三颗星
        for i in range(3):
            cx = SCREEN_WIDTH // 2 - 70 + i * 70
            draw_star(screen, cx, 470, 26, GOLD)

        draw_button(screen, '返回主菜单', self.btn_secondary, mouse_pos, font_size=24)


def draw_star(screen, cx, cy, size, color):
    """画五角星"""
    pts = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = size if i % 2 == 0 else size * 0.42
        pts.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    pygame.draw.polygon(screen, color, pts)


# ==================== 程序入口 ====================
def main():
    pygame.init()
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
    main()
