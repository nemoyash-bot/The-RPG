"""
Oakhaven — The Tale of the Corrupted Root (Pygame Edition)
============================================================
Single-file v1.6 build. Pygame core designed for easy web packaging/access.
Same core mechanics/numbers/save-code format as the v1.5 text RPG, with graphical presentation.

Run:
    pip install pygame
    python oakhaven_rpg.py
"""
import base64
import json
import math
import random
import sys
import asyncio
import os
import urllib.request
import urllib.error

import pygame



# ==========================================================================
# THEME — colors, fonts, panels, bars
# ==========================================================================

import pygame

WIDTH, HEIGHT = 1280, 760
FPS = 60

# Palette — deep forest / corrupted fantasy
BG_TOP = (14, 20, 24)
BG_BOTTOM = (26, 38, 30)
PANEL = (24, 30, 34)
PANEL_LIGHT = (34, 42, 46)
PANEL_BORDER = (70, 110, 90)
ACCENT = (120, 200, 140)
ACCENT_DARK = (60, 120, 90)
GOLD = (230, 190, 90)
DANGER = (220, 80, 80)
DANGER_DARK = (140, 40, 40)
POISON = (140, 100, 220)
TEXT = (230, 235, 230)
TEXT_DIM = (150, 165, 155)
TEXT_FAINT = (95, 108, 100)
WHITE = (255, 255, 255)
BLACK = (8, 10, 8)
HP_GREEN = (90, 200, 110)
HP_YELLOW = (220, 190, 80)
HP_RED = (210, 70, 70)
EXP_BLUE = (100, 170, 220)
BOSS_RED = (180, 30, 40)

_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        f = pygame.font.SysFont("georgia,garamond,timesnewroman,serif", size, bold=bold)
        _fonts[key] = f
    return _fonts[key]


def title_font(size):
    key = ("title", size)
    if key not in _fonts:
        f = pygame.font.SysFont("papyrus,georgia,serif", size, bold=True)
        _fonts[key] = f
    return _fonts[key]


def draw_vertical_gradient(surf, rect, top_color, bottom_color):
    x, y, w, h = rect
    if h <= 0:
        return
    for i in range(h):
        t = i / max(1, h - 1)
        color = tuple(int(top_color[c] + (bottom_color[c] - top_color[c]) * t) for c in range(3))
        pygame.draw.line(surf, color, (x, y + i), (x + w, y + i))


def draw_text(surf, text, pos, size=20, color=TEXT, bold=False, center=False, shadow=True, align=None):
    f = font(size, bold)
    if shadow:
        sh = f.render(text, True, (0, 0, 0))
        sh_rect = sh.get_rect()
        if center:
            sh_rect.center = (pos[0] + 2, pos[1] + 2)
        else:
            sh_rect.topleft = (pos[0] + 2, pos[1] + 2)
        surf.blit(sh, sh_rect)
    img = f.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    elif align == "right":
        rect.topright = pos
    else:
        rect.topleft = pos
    surf.blit(img, rect)
    return rect


def rounded_panel(surf, rect, color=PANEL, border=PANEL_BORDER, radius=14, border_w=2, alpha=None):
    x, y, w, h = rect
    if alpha is not None:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, w, h), border_radius=radius)
        if border:
            pygame.draw.rect(s, (*border, min(255, alpha + 60)), (0, 0, w, h), width=border_w, border_radius=radius)
        surf.blit(s, (x, y))
    else:
        pygame.draw.rect(surf, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(surf, border, rect, width=border_w, border_radius=radius)


def bar(surf, rect, ratio, fg, bg=(40, 40, 40), border=BLACK, radius=6):
    x, y, w, h = rect
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surf, bg, rect, border_radius=radius)
    if ratio > 0:
        fill_w = max(radius * 2 if w > radius * 2 else w, int(w * ratio))
        fill_w = min(w, int(w * ratio))
        if fill_w > 2:
            pygame.draw.rect(surf, fg, (x, y, fill_w, h), border_radius=radius)
    pygame.draw.rect(surf, border, rect, width=2, border_radius=radius)




# ==========================================================================
# DATA — enemy stats, spawn tables, shop/bounty tables, XP curve
# ==========================================================================

"""
Static game data ported directly from the original text-RPG numbers so that
balance stays identical: enemy stats, spawn tables, shop prices, bounties,
and the XP curve.
"""

MAX_POTIONS = 5
MAX_BANDAGES = 5
MAX_ANTIDOTES = 3
MAX_SPEED_POTIONS = 3
MAX_DAMAGE_POTIONS = 3

CONSUMABLES = ("Health potion", "Bandage", "Antidote", "Speed Potion", "Damage Potion")

CAPS = {
    "Health potion": MAX_POTIONS,
    "Bandage": MAX_BANDAGES,
    "Antidote": MAX_ANTIDOTES,
    "Speed Potion": MAX_SPEED_POTIONS,
    "Damage Potion": MAX_DAMAGE_POTIONS,
}


def get_exp_needed(level):
    level = max(1, min(int(level), 200))
    if level >= 200:
        return 0
    if level < 50:
        return int(20 * (level ** 1.45))
    elif level < 120:
        return int(1500 * ((level / 50) ** 2.0))
    else:
        return int(7000 * ((level / 120) ** 2.3))


# ---------------------------------------------------------------------------
# Regular forest enemies (Forest + Deep Forest Edge zones)
# key -> hp, dmg range, gold range, exp range, shape/color hint, zone tier
# ---------------------------------------------------------------------------
REGULAR_ENEMIES = {
    "Goblin":                {"hp": 28,  "dmg": (5, 9),   "gold": (10, 20),  "exp": (15, 25),  "color": (110, 200, 90),  "shape": "goblin"},
    "Bandit":                {"hp": 40,  "dmg": (8, 14),  "gold": (20, 30),  "exp": (25, 40),  "color": (170, 140, 90),  "shape": "bandit"},
    "Wolf":                  {"hp": 50,  "dmg": (10, 16), "gold": (30, 50),  "exp": (35, 50),  "color": (140, 140, 150), "shape": "wolf"},
    "Bear":                  {"hp": 90,  "dmg": (14, 22), "gold": (50, 70),  "exp": (50, 75),  "color": (120, 80, 50),   "shape": "bear"},
    "Hobgoblin Warlord":     {"hp": 140, "dmg": (18, 26), "gold": (40, 55),  "exp": (45, 60),  "color": (90, 170, 70),   "shape": "warlord", "enrage": True},
    "Alpha Dire Wolf":       {"hp": 175, "dmg": (22, 30), "gold": (50, 65),  "exp": (55, 70),  "color": (200, 200, 210), "shape": "wolf", "enrage": True},
    "Bandit Chieftain":      {"hp": 210, "dmg": (25, 35), "gold": (60, 80),  "exp": (65, 80),  "color": (200, 160, 60),  "shape": "bandit", "enrage": True},
    "Corrupted Treant":      {"hp": 280, "dmg": (30, 42), "gold": (60, 90),  "exp": (70, 100), "color": (80, 60, 40),    "shape": "treant"},
    "Venomous Stalker":      {"hp": 340, "dmg": (28, 38), "gold": (70, 110), "exp": (80, 115), "color": (110, 40, 160),  "shape": "spider"},
    "Corrupted Drake":       {"hp": 400, "dmg": (42, 58), "gold": (120, 170),"exp": (130, 180),"color": (180, 40, 40),   "shape": "drake"},
    "Shadow Specter":        {"hp": 600, "dmg": (60, 75), "gold": (140, 200),"exp": (160, 220),"color": (60, 20, 90),    "shape": "specter", "dodge": 0.25},
    "Blighted Beast":        {"hp": 680, "dmg": (80, 100),"gold": (160, 220),"exp": (180, 250),"color": (60, 90, 40),    "shape": "beast"},
    "Corrupted Knight":      {"hp": 800, "dmg": (50, 68), "gold": (180, 250),"exp": (210, 300),"color": (90, 90, 100),   "shape": "knight", "dodge": 0.20},
}

FOREST_TABLE_LOW = (
    ["Goblin", "Bandit", "Wolf", "Bear", "Hobgoblin Warlord", "Alpha Dire Wolf", "Bandit Chieftain", "Treasure"],
    [39, 30, 20, 3, 1, 1, 1, 5],
)
FOREST_TABLE_MID = (
    ["Goblin", "Bandit", "Wolf", "Bear", "Hobgoblin Warlord", "Alpha Dire Wolf", "Bandit Chieftain", "Treasure"],
    [10, 15, 20, 15, 10, 5, 5, 10],
)
FOREST_TABLE_HIGH = (
    ["Hobgoblin Warlord", "Alpha Dire Wolf", "Bandit Chieftain", "Treasure"],
    [25, 25, 25, 25],
)
DEEP_FOREST_TABLE = (
    ["Corrupted Treant", "Venomous Stalker", "Corrupted Drake", "Treasure"],
    [40, 35, 20, 5],
)


def forest_spawn_table(level):
    if level >= 16:
        return FOREST_TABLE_HIGH
    elif level >= 6:
        return FOREST_TABLE_MID
    return FOREST_TABLE_LOW


# ---------------------------------------------------------------------------
# Death Forest — complete v1.6 encounter roster
# ---------------------------------------------------------------------------
# Normal progression is deliberately distinct from the Forest Heart apex
# encounters.  The five normal enemies were accidentally lost in an earlier
# Pygame conversion; v1.6 restores them as real combat encounters.
DEATH_FOREST_ENEMIES = {
    "Death Crawler":            {"hp": 2000,  "damage": (75, 100),  "exp": 3000, "gold": 2400, "color": (70, 110, 55),  "shape": "crawler"},
    "Crypt Stalker":            {"hp": 2700,  "damage": (70, 100),  "exp": 3600, "gold": 2800, "color": (95, 100, 125), "shape": "stalker"},
    "Necromancer":              {"hp": 3200,  "damage": (85, 110), "exp": 5000, "gold": 3200, "color": (105, 55, 150), "shape": "necromancer"},
    "Bone Golem":               {"hp": 4500,  "damage": (105, 140), "exp": 9000, "gold": 7000, "color": (175, 165, 135), "shape": "golem"},
    "Grave Warden":             {"hp": 4500,  "damage": (110, 145), "exp": 1500, "gold": 1200, "color": (80, 85, 95),   "shape": "warden"},
    "Rotfang":                  {"hp": 8000,  "damage": (220, 310), "exp": 2200, "gold": 1800, "color": (90, 40, 30),  "shape": "rotfang"},
    "Bloodroot Ravager":        {"hp": 10000, "damage": (300, 300), "exp": 2800, "gold": 2200, "color": (120, 10, 10), "shape": "ravager"},
    "Thornbound Executioner":   {"hp": 12500, "damage": (300, 300), "exp": 3500, "gold": 2800, "color": (40, 20, 10),  "shape": "executioner"},
}

# Normal enemies are the common Death Forest threats; Forest Heart enemies
# remain rarer apex encounters. Treasure remains possible.
DEATH_FOREST_TABLE = (
    ["Death Crawler", "Crypt Stalker", "Necromancer", "Bone Golem", "Grave Warden",
     "Rotfang", "Bloodroot Ravager", "Thornbound Executioner", "Treasure"],
    [18, 15, 12, 10, 8, 12, 10, 8, 7],
)

LAST_WITNESS_MAX_HP = 30000

# ---------------------------------------------------------------------------
# Shops
# ---------------------------------------------------------------------------
VILLAGE_WEAPONS = [
    {"name": "Old sword", "upgrade_of": None, "cost": 250, "dmg_add": 15, "desc": "+15 damage"},
    {"name": "Steel Longsword", "upgrade_of": "Old sword", "cost": 750, "dmg_add": 25, "desc": "+25 additional damage (+40 total)"},
]
VILLAGE_ARMOR = [
    {"name": "Leather Tunic", "upgrade_of": None, "cost": 300, "armor": 5, "desc": "Reduces incoming damage by 5"},
    {"name": "Iron Plate Armor", "upgrade_of": "Leather Tunic", "cost": 950, "armor": 12, "desc": "Reduces incoming damage by 12"},
]

VALORIA_WEAPONS = [
    {"name": "Diamond Sword", "cost": 5000, "dmg_add": 50, "desc": "+50 damage, Armor Break proc"},
    {"name": "Mythril Sword", "cost": 15000, "dmg_add": 150, "desc": "+150 damage, Poison proc"},
    {"name": "Absolute Adamantium Hellfire", "cost": 50000, "dmg_add": 300, "desc": "+300 damage, Life Steal proc"},
]
VALORIA_ARMOR = [
    {"name": "Diamond Armor", "cost": 7500, "armor": 50, "desc": "+50 damage reduction"},
    {"name": "Mythrillic Armor", "cost": 20000, "armor": 100, "poison_res": 25, "desc": "+100 reduction, 25% Poison Resistance"},
    {"name": "Adamantium Hellfire", "cost": 75000, "armor": 200, "life_steal_res": 50, "desc": "+200 reduction, 50% Life Steal Resistance"},
]

WEAPON_ORDER = ["Old sword", "Steel Longsword", "Diamond Sword", "Mythril Sword", "Absolute Adamantium Hellfire"]
ARMOR_ORDER = ["Leather Tunic", "Iron Plate Armor", "Diamond Armor", "Mythrillic Armor", "Adamantium Hellfire"]

BOUNTIES = [
    {"id": 1, "target": "Goblin", "required": 3, "gold_reward": 45, "exp_reward": 35, "min_level": 1},
    {"id": 2, "target": "Wolf", "required": 2, "gold_reward": 70, "exp_reward": 60, "min_level": 1},
    {"id": 3, "target": "Hobgoblin Warlord", "required": 1, "gold_reward": 140, "exp_reward": 150, "min_level": 1},
    {"id": 4, "target": "Corrupted Treant", "required": 2, "gold_reward": 220, "exp_reward": 280, "min_level": 20},
    {"id": 5, "target": "Venomous Stalker", "required": 2, "gold_reward": 260, "exp_reward": 320, "min_level": 20},
    {"id": 6, "target": "Corrupted Drake", "required": 1, "gold_reward": 380, "exp_reward": 450, "min_level": 20},
    {"id": 7, "target": "Shadow Specter", "required": 2, "gold_reward": 420, "exp_reward": 520, "min_level": 50},
    {"id": 8, "target": "Blighted Beast", "required": 2, "gold_reward": 480, "exp_reward": 620, "min_level": 50},
    {"id": 9, "target": "Corrupted Knight", "required": 1, "gold_reward": 540, "exp_reward": 750, "min_level": 50},
    {"id": 10, "target": "Rotfang", "required": 1, "gold_reward": 5000, "exp_reward": 5000, "min_level": 90},
    {"id": 11, "target": "Bloodroot Ravager", "required": 1, "gold_reward": 7500, "exp_reward": 7500, "min_level": 90},
    {"id": 12, "target": "Thornbound Executioner", "required": 1, "gold_reward": 10000, "exp_reward": 10000, "min_level": 90},
]

CLARK_QUESTS = [
    {"target": "Shadow Specter", "required": 3, "gold_reward": 500, "exp_reward": 800},
    {"target": "Blighted Beast", "required": 3, "gold_reward": 600, "exp_reward": 900},
    {"target": "Corrupted Knight", "required": 2, "gold_reward": 700, "exp_reward": 1000},
]

def treasure_reward(level):
    import random
    if level > 20:
        return random.randint(100, 500), random.randint(100, 200)
    elif level > 10:
        return random.randint(50, 250), random.randint(50, 100)
    elif level > 5:
        return random.randint(25, 125), random.randint(25, 50)
    else:
        return random.randint(10, 75), random.randint(12, 25)




# ==========================================================================
# SAVE — save-code encode/decode (base64 JSON)
# ==========================================================================

import base64
import json


def generate_save_code(data: dict) -> str:
    json_str = json.dumps(data)
    encoded_bytes = base64.b64encode(json_str.encode("utf-8"))
    return encoded_bytes.decode("utf-8")


def load_from_save_code(code: str):
    try:
        decoded_bytes = base64.b64decode(code.strip().encode("utf-8"))
        json_str = decoded_bytes.decode("utf-8")
        return json.loads(json_str)
    except Exception:
        return None




# ==========================================================================
# PLAYER — player state, inventory, leveling
# ==========================================================================

class PlayerState:
    def __init__(self, name="Hero"):
        self.name = name
        self.is_admin = name.lower() == "debugger pro"
        self.player_hp = 25
        self.max_hp = 25
        self.gold = 0
        self.level = 1
        self.damage = 5
        self.exp = 0
        self.exp_needed = get_exp_needed(1)
        self.inventory = []
        self.armor_reduction = 0
        self.active_quest = None
        self.story_lvl20_seen = False
        self.story_lvl50_seen = False
        self.poison_resistance = 0
        self.life_steal_resistance = 0
        self.valoria_unlocked = False
        self.valoria_quests_completed = 0
        self.visited_valoria = False

    # ---- items -------------------------------------------------------
    def item_count(self, name):
        return self.inventory.count(name)

    def has_item(self, name):
        return name in self.inventory

    def add_item(self, name, qty=1):
        cap = CAPS.get(name)
        added = 0
        for _ in range(qty):
            if cap is not None and self.item_count(name) >= cap:
                break
            self.inventory.append(name)
            added += 1
        return added

    def remove_item(self, name, qty=1):
        removed = 0
        for _ in range(qty):
            if name in self.inventory:
                self.inventory.remove(name)
                removed += 1
        return removed

    def equipped_weapon(self):
        for w in reversed(WEAPON_ORDER):
            if w in self.inventory:
                return w
        return None

    def equipped_armor(self):
        for a in reversed(ARMOR_ORDER):
            if a in self.inventory:
                return a
        return None

    # ---- leveling ------------------------------------------------------
    def gain_exp(self, amount):
        """Add EXP, return list of levels gained (levels are applied by caller
        which must prompt for the stat point each time)."""
        self.exp += amount

    def ready_to_level(self):
        return self.exp >= self.exp_needed and self.level < 200

    def apply_level_up(self, stat_choice):
        """stat_choice: 'hp' or 'dmg'"""
        self.level += 1
        self.exp -= self.exp_needed
        self.exp_needed = get_exp_needed(self.level)
        if stat_choice == "hp":
            self.max_hp += 15
        else:
            self.damage += 3
        self.player_hp = self.max_hp

    # ---- persistence -----------------------------------------------------
    def to_dict(self):
        return {
            "name": self.name, "player_hp": self.player_hp, "max_hp": self.max_hp,
            "gold": self.gold, "Level": self.level, "damage": self.damage,
            "exp": self.exp, "exp_needed": self.exp_needed, "inventory": self.inventory,
            "armor_reduction": self.armor_reduction, "active_quest": self.active_quest,
            "story_lvl20_seen": self.story_lvl20_seen, "story_lvl50_seen": self.story_lvl50_seen,
            "poison_resistance": self.poison_resistance,
            "life_steal_resistance": self.life_steal_resistance,
            "valoria_unlocked": self.valoria_unlocked,
            "valoria_quests_completed": self.valoria_quests_completed,
            "visited_valoria": self.visited_valoria,
        }

    @classmethod
    def from_dict(cls, d):
        p = cls(d.get("name", "Hero"))
        p.player_hp = d.get("player_hp", 25)
        p.max_hp = d.get("max_hp", 25)
        p.gold = d.get("gold", 0)
        p.level = d.get("Level", 1)
        p.damage = d.get("damage", 5)
        p.exp = d.get("exp", 0)
        p.exp_needed = get_exp_needed(p.level)
        p.inventory = d.get("inventory", [])
        p.armor_reduction = d.get("armor_reduction", 0)
        p.active_quest = d.get("active_quest", None)
        p.story_lvl20_seen = d.get("story_lvl20_seen", False)
        p.story_lvl50_seen = d.get("story_lvl50_seen", False)
        p.poison_resistance = d.get("poison_resistance", 0)
        p.life_steal_resistance = d.get("life_steal_resistance", 0)
        p.valoria_unlocked = d.get("valoria_unlocked", False)
        p.valoria_quests_completed = d.get("valoria_quests_completed", 0)
        p.visited_valoria = d.get("visited_valoria", False)
        p.is_admin = p.name.lower() == "debugger pro"
        return p




# ==========================================================================
# SPRITES — procedural vector art for hero + every enemy
# ==========================================================================

import math
import pygame


def _bob(t, amp=6, speed=2.4):
    return math.sin(t * speed) * amp


def _flash_color(base, flash):
    if flash <= 0:
        return base
    return tuple(int(base[i] + (255 - base[i]) * flash) for i in range(3))


def _poly(surf, points, color):
    pygame.draw.polygon(surf, color, points)
    pygame.draw.polygon(surf, tuple(max(0, c - 40) for c in color), points, width=2)


# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
WEAPON_COLORS = {
    None: (150, 150, 150),
    "Old sword": (170, 170, 175),
    "Steel Longsword": (200, 205, 215),
    "Diamond Sword": (130, 220, 235),
    "Mythril Sword": (170, 110, 230),
    "Absolute Adamantium Hellfire": (255, 110, 40),
}
ARMOR_COLORS = {
    None: (90, 75, 60),
    "Leather Tunic": (120, 90, 55),
    "Iron Plate Armor": (140, 145, 150),
    "Diamond Armor": (110, 200, 220),
    "Mythrillic Armor": (150, 110, 210),
    "Adamantium Hellfire": (230, 100, 50),
}


def draw_hero(surf, cx, cy, t, weapon=None, armor=None, scale=1.0, flash=0.0, attack=0.0, hurt=0.0):
    bob = _bob(t)
    lean = attack * 26
    shake = hurt * 8 * math.sin(t * 40)
    cx += shake
    cy += bob
    s = scale

    body_color = _flash_color(ARMOR_COLORS.get(armor, ARMOR_COLORS[None]), flash)
    skin = _flash_color((225, 185, 150), flash)
    cloak = _flash_color((40, 70, 55), flash)

    # cloak
    _poly(surf, [(cx - 30 * s, cy + 10 * s), (cx - 4 * s, cy - 30 * s), (cx - 44 * s, cy + 55 * s)], cloak)
    # legs
    pygame.draw.rect(surf, (35, 35, 40), (cx - 16 * s, cy + 28 * s, 12 * s, 30 * s), border_radius=4)
    pygame.draw.rect(surf, (35, 35, 40), (cx + 4 * s, cy + 28 * s, 12 * s, 30 * s), border_radius=4)
    # torso
    pygame.draw.rect(surf, body_color, (cx - 20 * s, cy - 10 * s, 40 * s, 42 * s), border_radius=8)
    pygame.draw.rect(surf, tuple(max(0, c - 40) for c in body_color), (cx - 20 * s, cy - 10 * s, 40 * s, 42 * s), 2, border_radius=8)
    # head
    pygame.draw.circle(surf, skin, (int(cx), int(cy - 26 * s)), int(13 * s))
    pygame.draw.circle(surf, (30, 25, 20), (int(cx), int(cy - 34 * s)), int(14 * s), 0)  # hair/hood shadow band
    pygame.draw.circle(surf, skin, (int(cx), int(cy - 24 * s)), int(12 * s))
    # arm + weapon (leans forward when attacking)
    hand = (cx + 22 * s + lean, cy + 4 * s - lean * 0.3)
    pygame.draw.line(surf, skin, (cx + 14 * s, cy + 2 * s), hand, int(7 * s))
    wcolor = _flash_color(WEAPON_COLORS.get(weapon, WEAPON_COLORS[None]), flash)
    blade_tip = (hand[0] + 30 * s, hand[1] - 34 * s - lean * 0.4)
    pygame.draw.line(surf, (90, 65, 40), hand, (hand[0] + 8 * s, hand[1] - 6 * s), int(6 * s))
    pygame.draw.line(surf, wcolor, (hand[0] + 6 * s, hand[1] - 4 * s), blade_tip, int(5 * s))
    # off-arm / shield hint
    pygame.draw.line(surf, skin, (cx - 14 * s, cy + 2 * s), (cx - 26 * s, cy + 16 * s), int(7 * s))
    if armor:
        pygame.draw.circle(surf, ARMOR_COLORS.get(armor), (int(cx - 26 * s), int(cy + 16 * s)), int(9 * s))


# ---------------------------------------------------------------------------
# ENEMIES — each "shape" gets a distinct silhouette
# ---------------------------------------------------------------------------
def draw_enemy(surf, shape, color, cx, cy, t, scale=1.0, flash=0.0, attack=0.0, hurt=0.0, enraged=False):
    bob = _bob(t, amp=8, speed=1.8)
    lean = attack * 22
    shake = hurt * 10 * math.sin(t * 45)
    cx += shake + lean
    cy += bob
    s = scale
    c = _flash_color(color, flash)
    if enraged:
        c = tuple(min(255, int(c[i] * 1.0 + (255 if i == 0 else 0) * 0.25)) for i in range(3))
    dark = tuple(max(0, ch - 50) for ch in c)
    eye = (255, 60, 60) if enraged else (250, 230, 120)

    fn = _SHAPES.get(shape, _shape_blob)
    fn(surf, cx, cy, s, c, dark, eye, t)


def _eyes(surf, cx, cy, s, eye, gap=10, y=0, r=3):
    pygame.draw.circle(surf, eye, (int(cx - gap * s), int(cy + y)), int(r * s))
    pygame.draw.circle(surf, eye, (int(cx + gap * s), int(cy + y)), int(r * s))


def _shape_blob(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.circle(surf, c, (int(cx), int(cy)), int(30 * s))
    pygame.draw.circle(surf, dark, (int(cx), int(cy)), int(30 * s), 3)
    _eyes(surf, cx, cy, s, eye, y=-4)


def _shape_goblin(surf, cx, cy, s, c, dark, eye, t):
    _poly(surf, [(cx - 18 * s, cy + 26 * s), (cx - 24 * s, cy - 6 * s), (cx, cy - 30 * s),
                 (cx + 24 * s, cy - 6 * s), (cx + 18 * s, cy + 26 * s)], c)
    pygame.draw.circle(surf, c, (int(cx), int(cy - 30 * s)), int(14 * s))
    _poly(surf, [(cx - 12 * s, cy - 40 * s), (cx - 4 * s, cy - 52 * s), (cx - 2 * s, cy - 36 * s)], dark)
    _poly(surf, [(cx + 12 * s, cy - 40 * s), (cx + 4 * s, cy - 52 * s), (cx + 2 * s, cy - 36 * s)], dark)
    _eyes(surf, cx, cy - 30 * s, s, eye)


def _shape_bandit(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.rect(surf, c, (cx - 20 * s, cy - 22 * s, 40 * s, 46 * s), border_radius=6)
    pygame.draw.circle(surf, (210, 180, 150), (int(cx), int(cy - 30 * s)), int(13 * s))
    pygame.draw.rect(surf, dark, (cx - 15 * s, cy - 40 * s, 30 * s, 10 * s), border_radius=4)
    _eyes(surf, cx, cy - 30 * s, s, eye)
    pygame.draw.line(surf, dark, (cx - 22 * s, cy - 6 * s), (cx + 22 * s, cy + 4 * s), int(4 * s))


def _shape_wolf(surf, cx, cy, s, c, dark, eye, t):
    _poly(surf, [(cx - 34 * s, cy + 14 * s), (cx - 20 * s, cy - 14 * s), (cx + 20 * s, cy - 10 * s), (cx + 34 * s, cy + 10 * s), (cx + 10 * s, cy + 22 * s), (cx - 14 * s, cy + 22 * s)], c)
    _poly(surf, [(cx + 24 * s, cy - 12 * s), (cx + 44 * s, cy - 6 * s), (cx + 30 * s, cy + 4 * s)], c)
    _poly(surf, [(cx + 34 * s, cy - 14 * s), (cx + 40 * s, cy - 24 * s), (cx + 38 * s, cy - 10 * s)], dark)
    _eyes(surf, cx + 34 * s, cy - 6 * s, s, eye, gap=5, y=0, r=2.5)


def _shape_bear(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.ellipse(surf, c, (cx - 34 * s, cy - 16 * s, 68 * s, 46 * s))
    pygame.draw.circle(surf, c, (int(cx + 30 * s), int(cy - 14 * s)), int(18 * s))
    pygame.draw.circle(surf, dark, (int(cx + 20 * s), int(cy - 26 * s)), int(6 * s))
    pygame.draw.circle(surf, dark, (int(cx + 40 * s), int(cy - 26 * s)), int(6 * s))
    _eyes(surf, cx + 30 * s, cy - 16 * s, s, eye, gap=6)


def _shape_warlord(surf, cx, cy, s, c, dark, eye, t):
    _shape_goblin(surf, cx, cy, s * 1.25, c, dark, eye, t)
    pygame.draw.rect(surf, (150, 60, 40), (cx - 30 * s, cy - 4 * s, 60 * s, 10 * s), border_radius=3)


def _shape_treant(surf, cx, cy, s, c, dark, eye, t):
    sway = math.sin(t * 1.2) * 4 * s
    pygame.draw.rect(surf, c, (cx - 12 * s, cy - 10 * s, 24 * s, 50 * s), border_radius=6)
    pygame.draw.circle(surf, c, (int(cx), int(cy - 30 * s)), int(26 * s))
    for dx, dy in [(-22, -20), (22, -20), (-30, 0), (30, 0), (0, -46)]:
        pygame.draw.line(surf, dark, (cx, cy - 20 * s), (cx + (dx + sway) * s, cy + dy * s), int(5 * s))
    _eyes(surf, cx, cy - 30 * s, s, eye)


def _shape_spider(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.circle(surf, c, (int(cx), int(cy)), int(20 * s))
    pygame.draw.circle(surf, c, (int(cx - 18 * s), int(cy - 10 * s)), int(12 * s))
    for i in range(3):
        ang = (i - 1) * 0.5
        wob = math.sin(t * 6 + i) * 4
        for side in (-1, 1):
            pygame.draw.line(surf, dark,
                              (cx + side * 8 * s, cy),
                              (cx + side * (34 * s + wob) * math.cos(ang), cy + (18 + i * 8) * s * math.sin(ang + 1)),
                              int(3 * s))
    _eyes(surf, cx - 18 * s, cy - 10 * s, s, eye, gap=5, r=2)


def _shape_drake(surf, cx, cy, s, c, dark, eye, t):
    flap = math.sin(t * 5) * 10
    _poly(surf, [(cx - 10 * s, cy), (cx - 40 * s, cy - 20 * s - flap), (cx - 12 * s, cy - 4 * s)], c)
    _poly(surf, [(cx + 10 * s, cy), (cx + 40 * s, cy - 20 * s + flap), (cx + 12 * s, cy - 4 * s)], c)
    pygame.draw.ellipse(surf, c, (cx - 22 * s, cy - 14 * s, 44 * s, 30 * s))
    pygame.draw.circle(surf, c, (int(cx + 24 * s), int(cy - 8 * s)), int(12 * s))
    _poly(surf, [(cx + 34 * s, cy - 10 * s), (cx + 44 * s, cy - 6 * s), (cx + 34 * s, cy - 2 * s)], dark)
    _eyes(surf, cx + 26 * s, cy - 10 * s, s, eye, gap=6, r=2.5)


def _shape_specter(surf, cx, cy, s, c, dark, eye, t):
    wob = math.sin(t * 3) * 6
    pts = [(cx - 26 * s, cy - 10 * s), (cx - 26 * s + wob, cy + 22 * s), (cx - 10 * s, cy + 10 * s),
           (cx, cy + 26 * s), (cx + 10 * s, cy + 10 * s), (cx + 26 * s - wob, cy + 22 * s), (cx + 26 * s, cy - 10 * s)]
    s2 = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(s2, (*c, 190), pts)
    pygame.draw.circle(s2, (*c, 190), (int(cx), int(cy - 16 * s)), int(26 * s))
    surf.blit(s2, (0, 0))
    _eyes(surf, cx, cy - 16 * s, s, (240, 60, 200), gap=8, r=3)


def _shape_beast(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.ellipse(surf, c, (cx - 30 * s, cy - 12 * s, 60 * s, 40 * s))
    pygame.draw.circle(surf, c, (int(cx + 26 * s), int(cy - 6 * s)), int(16 * s))
    for i in range(3):
        pygame.draw.line(surf, dark, (cx - 20 * s + i * 18 * s, cy + 18 * s), (cx - 20 * s + i * 18 * s, cy + 34 * s), int(6 * s))
    _poly(surf, [(cx + 34 * s, cy - 16 * s), (cx + 40 * s, cy - 28 * s), (cx + 40 * s, cy - 12 * s)], dark)
    _eyes(surf, cx + 26 * s, cy - 8 * s, s, eye, gap=6)


def _shape_knight(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.rect(surf, c, (cx - 20 * s, cy - 14 * s, 40 * s, 46 * s), border_radius=6)
    pygame.draw.rect(surf, dark, (cx - 20 * s, cy - 14 * s, 40 * s, 46 * s), 3, border_radius=6)
    pygame.draw.circle(surf, c, (int(cx), int(cy - 30 * s)), int(15 * s))
    pygame.draw.rect(surf, dark, (cx - 8 * s, cy - 34 * s, 16 * s, 8 * s))
    _eyes(surf, cx, cy - 30 * s, s, eye, gap=5, r=2.5)
    pygame.draw.line(surf, (200, 200, 210), (cx + 24 * s, cy - 20 * s), (cx + 40 * s, cy + 20 * s), int(5 * s))


def _shape_rotfang(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.ellipse(surf, c, (cx - 40 * s, cy - 16 * s, 80 * s, 40 * s))
    pygame.draw.circle(surf, c, (int(cx + 36 * s), int(cy - 6 * s)), int(18 * s))
    for i in range(4):
        pygame.draw.line(surf, (230, 230, 220), (cx + 22 * s + i * 8 * s, cy + 2 * s), (cx + 24 * s + i * 8 * s, cy + 16 * s), 3)
    _eyes(surf, cx + 36 * s, cy - 8 * s, s, (255, 40, 40), gap=6)


def _shape_ravager(surf, cx, cy, s, c, dark, eye, t):
    pulse = 1 + 0.05 * math.sin(t * 4)
    pygame.draw.circle(surf, c, (int(cx), int(cy)), int(38 * s * pulse))
    pygame.draw.circle(surf, dark, (int(cx), int(cy)), int(38 * s * pulse), 4)
    for i in range(6):
        ang = i / 6 * 2 * math.pi + t
        pygame.draw.line(surf, dark, (cx, cy), (cx + math.cos(ang) * 44 * s, cy + math.sin(ang) * 44 * s), int(4 * s))
    _eyes(surf, cx, cy, s, (255, 30, 30), gap=10)


def _shape_executioner(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.rect(surf, c, (cx - 24 * s, cy - 30 * s, 48 * s, 66 * s), border_radius=8)
    for dx in (-30, -10, 10, 30):
        pygame.draw.line(surf, dark, (cx + dx * s, cy - 30 * s), (cx + dx * s, cy - 46 * s), int(5 * s))
    _eyes(surf, cx, cy - 8 * s, s, (255, 200, 50), gap=9)
    pygame.draw.line(surf, (210, 210, 220), (cx - 34 * s, cy + 10 * s), (cx - 50 * s, cy + 50 * s), int(6 * s))


def _shape_witness(surf, cx, cy, s, c, dark, eye, t):
    sway = math.sin(t * 0.8) * 8 * s
    pygame.draw.rect(surf, c, (cx - 30 * s, cy - 10 * s, 60 * s, 90 * s), border_radius=10)
    for i, dx in enumerate([-46, -26, 0, 26, 46]):
        wob = math.sin(t * 1.3 + i) * 8
        pygame.draw.line(surf, dark, (cx, cy - 10 * s), (cx + (dx + wob + sway) * s, cy - 70 * s - abs(dx) * 0.3 * s), int(7 * s))
    pygame.draw.circle(surf, c, (int(cx), int(cy - 40 * s)), int(30 * s))
    _eyes(surf, cx, cy - 40 * s, s, (255, 220, 60), gap=12, r=5)
    pygame.draw.circle(surf, (255, 220, 60), (int(cx), int(cy - 40 * s)), int(5 * s))


def _shape_crawler(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.ellipse(surf, c, (cx - 38*s, cy - 20*s, 76*s, 44*s))
    for dx in (-28, -12, 12, 28):
        pygame.draw.line(surf, dark, (cx + dx*s, cy + 12*s), (cx + (dx-8)*s, cy + 32*s), int(5*s))
        pygame.draw.line(surf, dark, (cx + dx*s, cy + 12*s), (cx + (dx+8)*s, cy + 32*s), int(5*s))
    _eyes(surf, cx, cy-8*s, s, eye, gap=9, r=3)

def _shape_stalker(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.polygon(surf, c, [(cx-30*s,cy+28*s),(cx-22*s,cy-18*s),(cx,cy-36*s),(cx+22*s,cy-18*s),(cx+30*s,cy+28*s)])
    pygame.draw.line(surf, dark, (cx-28*s,cy+4*s), (cx+28*s,cy+4*s), int(5*s))
    _eyes(surf, cx, cy-10*s, s, eye, gap=8, r=3)

def _shape_necromancer(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.polygon(surf, c, [(cx-25*s,cy+38*s),(cx-18*s,cy-18*s),(cx,cy-42*s),(cx+18*s,cy-18*s),(cx+25*s,cy+38*s)])
    pygame.draw.circle(surf, dark, (int(cx),int(cy-40*s)), int(14*s))
    _eyes(surf, cx, cy-40*s, s, (180,80,255), gap=5, r=3)
    pygame.draw.line(surf, dark, (cx+28*s,cy-35*s), (cx+38*s,cy+42*s), int(4*s))
    pygame.draw.circle(surf, eye, (int(cx+38*s),int(cy+42*s)), int(7*s))

def _shape_golem(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.rect(surf, c, (cx-34*s,cy-32*s,68*s,70*s), border_radius=10)
    pygame.draw.circle(surf, c, (int(cx),int(cy-38*s)), int(25*s))
    for dx in (-44,44): pygame.draw.line(surf,dark,(cx+dx*s,cy-12*s),(cx+dx*s,cy+28*s),int(12*s))
    pygame.draw.line(surf,dark,(cx-20*s,cy+2*s),(cx+20*s,cy+2*s),int(6*s))
    _eyes(surf,cx,cy-38*s,s,eye,gap=8,r=4)

def _shape_warden(surf, cx, cy, s, c, dark, eye, t):
    pygame.draw.polygon(surf,c,[(cx-32*s,cy+38*s),(cx-26*s,cy-25*s),(cx,cy-48*s),(cx+26*s,cy-25*s),(cx+32*s,cy+38*s)])
    pygame.draw.circle(surf,dark,(int(cx),int(cy-46*s)),int(22*s),4)
    pygame.draw.line(surf,dark,(cx-20*s,cy-5*s),(cx+20*s,cy-5*s),int(5*s))
    _eyes(surf,cx,cy-15*s,s,eye,gap=10,r=4)
    pygame.draw.line(surf,dark,(cx+34*s,cy-30*s),(cx+48*s,cy+42*s),int(6*s))


_SHAPES = {
    "goblin": _shape_goblin, "bandit": _shape_bandit, "wolf": _shape_wolf, "bear": _shape_bear,
    "warlord": _shape_warlord, "treant": _shape_treant, "spider": _shape_spider, "drake": _shape_drake,
    "specter": _shape_specter, "beast": _shape_beast, "knight": _shape_knight,
    "crawler": _shape_crawler, "stalker": _shape_stalker, "necromancer": _shape_necromancer,
    "golem": _shape_golem, "warden": _shape_warden,
    "rotfang": _shape_rotfang, "ravager": _shape_ravager, "executioner": _shape_executioner,
    "witness": _shape_witness,
}




# ==========================================================================
# VFX — floating damage numbers, particles, screen shake
# ==========================================================================

import random
import pygame


class FloatingText:
    def __init__(self, text, pos, color=DANGER, size=26, vy=-60, life=1.0):
        self.text = text
        self.x, self.y = pos
        self.color = color
        self.size = size
        self.vy = vy
        self.life = life
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        self.y += self.vy * dt
        self.vy *= 0.9

    @property
    def dead(self):
        return self.age >= self.life

    def draw(self, surf):
        a = max(0, 1 - self.age / self.life)
        f = font(self.size, True)
        img = f.render(self.text, True, self.color)
        img.set_alpha(int(255 * a))
        rect = img.get_rect(center=(self.x, self.y))
        surf.blit(img, rect)


class Particle:
    def __init__(self, pos, vel, color, life=0.6, radius=3):
        self.x, self.y = pos
        self.vx, self.vy = vel
        self.color = color
        self.life = life
        self.age = 0.0
        self.radius = radius

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 260 * dt

    @property
    def dead(self):
        return self.age >= self.life

    def draw(self, surf):
        a = max(0, 1 - self.age / self.life)
        r = max(1, int(self.radius * a))
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(200 * a)), (r + 1, r + 1), r)
        surf.blit(s, (self.x - r, self.y - r))


class EffectLayer:
    def __init__(self):
        self.floats = []
        self.particles = []
        self.shake_t = 0.0
        self.shake_mag = 0.0

    def damage_number(self, pos, amount, crit=False, kind="dmg"):
        color = DANGER if kind == "dmg" else (HP_GREEN if kind == "heal" else POISON)
        size = 34 if crit else 24
        text = f"-{amount}" if kind == "dmg" else f"+{amount}"
        self.floats.append(FloatingText(text, pos, color=color, size=size))
        if crit:
            self.floats.append(FloatingText("CRIT!", (pos[0], pos[1] - 24), color=GOLD, size=18))

    def burst(self, pos, color, n=14, speed=140):
        for _ in range(n):
            ang = random.uniform(0, 6.283)
            spd = random.uniform(speed * 0.3, speed)
            vel = (spd * __import__("math").cos(ang), spd * __import__("math").sin(ang) - 40)
            self.particles.append(Particle(pos, vel, color, life=random.uniform(0.4, 0.8), radius=random.randint(2, 5)))

    def shake(self, magnitude=8, duration=0.25):
        self.shake_mag = max(self.shake_mag, magnitude)
        self.shake_t = max(self.shake_t, duration)

    def update(self, dt):
        for f in self.floats:
            f.update(dt)
        self.floats = [f for f in self.floats if not f.dead]
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.dead]
        if self.shake_t > 0:
            self.shake_t -= dt
        else:
            self.shake_mag = 0

    def offset(self):
        if self.shake_mag <= 0:
            return (0, 0)
        return (random.uniform(-1, 1) * self.shake_mag, random.uniform(-1, 1) * self.shake_mag)

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)
        for f in self.floats:
            f.draw(surf)




# ==========================================================================
# AMBIENT — animated background
# ==========================================================================

import math
import random
import pygame

_fireflies = None


def _init_fireflies(n=26):
    global _fireflies
    _fireflies = [
        [random.uniform(0, WIDTH), random.uniform(150, HEIGHT), random.uniform(0, 6.28), random.uniform(0.5, 1.5)]
        for _ in range(n)
    ]


def draw_background(surf, t, mood="forest"):
    global _fireflies
    if _fireflies is None:
        _init_fireflies()

    top = BG_TOP
    bottom = BG_BOTTOM
    if mood == "death":
        top = (10, 8, 10)
        bottom = (30, 18, 20)
    elif mood == "boss":
        top = (18, 6, 8)
        bottom = (40, 12, 16)
    elif mood == "town":
        top = (16, 20, 28)
        bottom = (34, 34, 40)

    draw_vertical_gradient(surf, (0, 0, WIDTH, HEIGHT), top, bottom)

    # distant hills
    for layer, (color, amp, speed, base) in enumerate([
        ((20, 30, 24) if mood != "death" else (24, 16, 18), 40, 0.15, 0.62),
        ((15, 24, 18) if mood != "death" else (18, 12, 14), 60, 0.1, 0.75),
    ]):
        pts = [(0, HEIGHT)]
        for x in range(0, WIDTH + 40, 40):
            y = HEIGHT * base + math.sin(x * 0.01 + t * speed + layer) * amp
            pts.append((x, y))
        pts.append((WIDTH, HEIGHT))
        pygame.draw.polygon(surf, color, pts)

    # tree silhouettes
    rng = random.Random(7)
    for i in range(14):
        x = (i * 97 + 30) % WIDTH
        sway = math.sin(t * 0.6 + i) * 3
        h = 90 + (i * 37) % 70
        base_y = HEIGHT - 10
        trunk_col = (12, 16, 12) if mood != "death" else (22, 14, 14)
        pygame.draw.line(surf, trunk_col, (x, base_y), (x + sway, base_y - h), 8)
        pygame.draw.circle(surf, trunk_col, (int(x + sway), int(base_y - h)), 34)

    if mood != "boss":
        for f in _fireflies:
            f[2] += 0.01
            fx = f[0] + math.sin(f[2] * 2) * 20
            fy = f[1] + math.cos(f[2] * 1.3) * 10
            glow = (140, 220, 120) if mood != "death" else (170, 120, 220)
            alpha = int(120 + 100 * math.sin(t * f[3] + f[2]))
            s = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(s, (*glow, max(0, min(255, alpha))), (4, 4), 3)
            surf.blit(s, (fx, fy))

    # vignette
    vg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(vg, (0, 0, 0, 90), (0, 0, WIDTH, 60))
    pygame.draw.rect(vg, (0, 0, 0, 110), (0, HEIGHT - 40, WIDTH, 40))
    surf.blit(vg, (0, 0))




# ==========================================================================
# UI — buttons, text inputs, scrolling log, toasts
# ==========================================================================

import pygame


class Button:
    def __init__(self, rect, text, callback=None, size=22, enabled=True, tooltip=None,
                 base_color=PANEL_LIGHT, hover_color=None, text_color=TEXT, accent=ACCENT):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.size = size
        self.enabled = enabled
        self.tooltip = tooltip
        self.base_color = base_color
        self.hover_color = hover_color or tuple(min(255, c + 18) for c in base_color)
        self.text_color = text_color
        self.accent = accent
        self.hovered = False
        self._press_anim = 0.0

    def update(self, mouse_pos, dt):
        self.hovered = self.enabled and self.rect.collidepoint(mouse_pos)
        target = 1.0 if self.hovered else 0.0
        self._press_anim += (target - self._press_anim) * min(1.0, dt * 10)

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surf):
        col = self.base_color if self.enabled else (30, 30, 32)
        if self.enabled and self.hovered:
            col = self.hover_color
        grow = int(2 * self._press_anim)
        r = self.rect.inflate(grow, grow)
        border = self.accent if self.enabled else (55, 55, 58)
        rounded_panel(surf, r, color=col, border=border, radius=10, border_w=2)
        color = self.text_color if self.enabled else TEXT_FAINT
        draw_text(surf, self.text, r.center, size=self.size, color=color, center=True, shadow=self.enabled)


class TextInput:
    def __init__(self, rect, placeholder="", max_len=18, password=False):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.placeholder = placeholder
        self.max_len = max_len
        self.password = password
        self.active = False
        self._cursor_t = 0.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                pass
            elif len(self.text) < self.max_len and event.unicode and event.unicode.isprintable():
                self.text += event.unicode

    def update(self, dt):
        self._cursor_t += dt

    def draw(self, surf):
        col = PANEL_LIGHT
        border = ACCENT if self.active else PANEL_BORDER
        rounded_panel(surf, self.rect, color=col, border=border, radius=8, border_w=2)
        shown = "•" * len(self.text) if self.password else self.text
        if shown:
            draw_text(surf, shown, (self.rect.x + 12, self.rect.centery), size=20,
                         color=TEXT, center=False, shadow=False)
            draw_text(surf, shown, (self.rect.x + 12, self.rect.centery - 12), size=20, color=TEXT, shadow=False)
        else:
            draw_text(surf, self.placeholder, (self.rect.x + 12, self.rect.centery - 12), size=18,
                         color=TEXT_FAINT, shadow=False)
        if self.active and int(self._cursor_t * 2) % 2 == 0:
            fw = font(20).size(shown)[0]
            cx = self.rect.x + 14 + fw
            pygame.draw.line(surf, ACCENT, (cx, self.rect.y + 8), (cx, self.rect.bottom - 8), 2)


class ScrollLog:
    """Bottom-anchored auto-scrolling combat log panel."""

    def __init__(self, rect, size=18, max_lines=200):
        self.rect = pygame.Rect(rect)
        self.size = size
        self.lines = []
        self.max_lines = max_lines
        self.scroll = 0

    def add(self, text):
        for wrapped in _wrap_text(text, self.rect.w - 24, self.size):
            self.lines.append(wrapped)
        self.lines = self.lines[-self.max_lines:]
        self.scroll = 0

    def clear(self):
        self.lines = []

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
            self.scroll = max(0, self.scroll - event.y * 3)

    def draw(self, surf):
        rounded_panel(surf, self.rect, color=(16, 20, 20), border=PANEL_BORDER, radius=10, alpha=210)
        line_h = self.size + 6
        visible = self.rect.h // line_h
        total = len(self.lines)
        start = max(0, total - visible - self.scroll)
        end = max(0, total - self.scroll)
        shown = self.lines[start:end]
        y = self.rect.bottom - 10 - len(shown) * line_h
        clip = surf.get_clip()
        surf.set_clip(self.rect.inflate(-4, -4))
        for line in shown:
            draw_text(surf, line, (self.rect.x + 12, y), size=self.size, color=TEXT_DIM, shadow=False)
            y += line_h
        surf.set_clip(clip)


def _wrap_text(text, max_w, size):
    f = font(size)
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if f.size(trial)[0] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Toast:
    def __init__(self):
        self.items = []  # (text, timer, color)

    def push(self, text, color=GOLD, duration=2.2):
        self.items.append([text, duration, color])

    def update(self, dt):
        for item in self.items:
            item[1] -= dt
        self.items = [i for i in self.items if i[1] > 0]

    def draw(self, surf):
        y = 20
        for text, timer, color in self.items:
            alpha = min(255, int(255 * min(1.0, timer)))
            w = font(22, True).size(text)[0] + 40
            rect = pygame.Rect(WIDTH // 2 - w // 2, y, w, 40)
            rounded_panel(surf, rect, color=(20, 24, 22), border=color, radius=10, alpha=min(230, alpha))
            draw_text(surf, text, rect.center, size=20, color=color, bold=True, center=True)
            y += 46




# ==========================================================================
# COMBAT — turn-based battle engines
# ==========================================================================

import random


def tick_damage_potion_timers(timers):
    return [t - 1 for t in timers if t - 1 > 0]


class LogMixin:
    def log(self, msg):
        self.messages.append(msg)


class Battle(LogMixin):
    """Generic battle for regular forest / deep forest enemies (12 types)."""

    CATEGORY = "regular"

    def __init__(self, encounter, player):
        self.encounter = encounter
        self.player = player
        info = REGULAR_ENEMIES[encounter]
        self.enemy_max_hp = info["hp"]
        self.enemy_hp = info["hp"]
        self.dmg_lo, self.dmg_hi = info["dmg"]
        self.gold_lo, self.gold_hi = info["gold"]
        self.exp_lo, self.exp_hi = info["exp"]
        self.enrage_capable = info.get("enrage", False)
        self.dodge_chance = info.get("dodge", 0.0)
        self.is_enraged = False

        self.bleed_turns = 0
        self.poison_turns = 0
        self.armor_broken_turns = 0
        self.enemy_armor_broken_turns = 0
        self.enemy_poison_turns = 0
        self.defend_cooldown = 0
        self.feint_cooldown = 0
        self.feint_buff = False
        self.damage_potion_timers = []
        self.speed_potion_active = False
        self.stunned = False

        self.messages = []
        self.over = False
        self.victory = False
        self.fled = False
        self.rewards = {"gold": 0, "exp": 0}

        if player.has_item("Speed Potion"):
            player.remove_item("Speed Potion")
            self.speed_potion_active = True
            self.log("⚡ Speed Potion activated! Enemy dodge is reduced by 30% for this battle.")
            self.dodge_chance = max(0.0, self.dodge_chance - 0.075) if self.dodge_chance else 0.0
            # match original: -30% relative dodge (25 -> 17.5%, 20 -> 14%)
            self.dodge_chance = info.get("dodge", 0.0) * 0.70 if info.get("dodge") else 0.0

        self.start_of_round()

    # ------------------------------------------------------------------
    def start_of_round(self):
        p = self.player
        if self.enrage_capable and not self.is_enraged and self.enemy_hp <= self.enemy_max_hp * 0.20 and self.enemy_hp > 0:
            self.is_enraged = True
            self.log(f"🔥 THE {self.encounter} IS ENRAGED! Deals +5 bonus damage and takes reduced damage!")

        if self.bleed_turns > 0:
            bleed_dmg = 8 if self.encounter == "Alpha Dire Wolf" else 4
            p.player_hp -= bleed_dmg
            self.bleed_turns -= 1
            self.log(f"🩸 You are bleeding! Took {bleed_dmg} damage. ({self.bleed_turns} left)")
        if self.poison_turns > 0:
            poison_dmg = 12 if self.encounter == "Corrupted Drake" else 10
            p.player_hp -= poison_dmg
            self.poison_turns -= 1
            self.log(f"🧪 Poison burns you! Took {poison_dmg} damage. ({self.poison_turns} left)")

        if p.player_hp <= 0:
            self.log("You succumbed to status effects! You woke up in the village with half your gold.")
            p.gold = max(0, p.gold // 2)
            p.player_hp = p.max_hp
            self.over = True
            self.victory = False
            return

        if self.armor_broken_turns > 0:
            self.armor_broken_turns -= 1
            self.log(f"🛡️ Your armor is cracked! ({self.armor_broken_turns} left)")

    # ------------------------------------------------------------------
    def _weapon_procs(self, dealt):
        p = self.player
        if dealt <= 0:
            return
        if "Diamond Sword" in p.inventory and random.random() < 0.25:
            self.enemy_armor_broken_turns = 3
            self.log("💎 Diamond Sword triggered ARMOR BREAK! +25% damage for 3 turns!")
        elif "Mythril Sword" in p.inventory and random.random() < 0.25:
            self.enemy_poison_turns = 3
            self.log("🟣 Mythril Sword triggered POISON! Enemy poisoned for 3 turns!")
        elif "Absolute Adamantium Hellfire" in p.inventory and random.random() < 0.25:
            steal = max(1, int(dealt * 0.50))
            old = p.player_hp
            p.player_hp = min(p.max_hp, p.player_hp + steal)
            self.log(f"🔥 Adamantium Hellfire LIFE STEAL! Restored {p.player_hp - old} HP!")

    def _mult(self, val):
        val = int(val)
        if self.is_enraged:
            val = int(val * 0.90)
        if self.enemy_armor_broken_turns > 0:
            val = int(val * 1.25)
        val = int(val * (2 ** len(self.damage_potion_timers)))
        return val

    def do_attack(self, kind):
        """kind: light / heavy / quick / feint / wild"""
        if self.over:
            return
        p = self.player
        dealt = 0
        acted = True
        daze = False

        dodged = self.dodge_chance and random.random() < self.dodge_chance
        if dodged:
            self.log(f"👻 The {self.encounter} dodged your attack!")
        elif kind == "light":
            crit = random.random() < 0.15
            dealt = self._mult(random.randint(p.damage, p.damage + 2) * (1.5 if crit else 1.0))
            self.enemy_hp -= dealt
            self.log(f"{'💥 CRITICAL! ' if crit else ''}Light Attack dealt {dealt} damage!")
        elif kind == "heavy":
            miss = 0.30 if self.feint_buff else 0.50
            if random.random() < miss:
                self.log("You swung a Heavy Attack and MISSED!")
                self.feint_buff = False
            else:
                if self.feint_buff:
                    self.log("🎯 Feint Buff consumed! Heavy Attack lands with precision!")
                    self.feint_buff = False
                crit = random.random() < 0.10
                raw = random.randint(int(p.damage * 1.5), max(int(p.damage * 1.5), int(p.damage * 1.75)))
                dealt = self._mult(raw * (1.5 if crit else 1.0))
                self.enemy_hp -= dealt
                self.log(f"{'💥 CRITICAL HEAVY! ' if crit else '💥 HEAVY ATTACK! '}Dealt {dealt} damage!")
        elif kind == "quick":
            crit = random.random() < 0.10
            low = max(1, p.damage - 2)
            dealt = self._mult(random.randint(low, p.damage) * (1.5 if crit else 1.0))
            self.enemy_hp -= dealt
            self.log(f"Quick Strike dealt {dealt} damage!")
            if random.random() < 0.50 and self.enemy_hp > 0:
                daze = True
                self.log(f"💫 The {self.encounter} was DAZED and loses its turn!")
        elif kind == "feint":
            if self.feint_cooldown > 0:
                return
            dealt = self._mult(max(1, p.damage // 2))
            self.enemy_hp -= dealt
            self.feint_buff = True
            self.feint_cooldown = 4
            self.log(f"🤺 Feint & Strike dealt {dealt} damage! Next Heavy Attack +40% accuracy!")
        elif kind == "wild":
            supercrit = random.random() < 0.15
            raw = random.randint(1, max(1, p.damage * 2))
            dealt = self._mult(raw * (2.5 if supercrit else 1.0))
            self.enemy_hp -= dealt
            self.log(f"{'⚡ SUPER CRITICAL! ' if supercrit else '🌀 '}Wild Swing dealt {dealt} damage!")

        self._weapon_procs(dealt)
        self._end_player_action(daze_enemy=daze)

    def do_defend(self):
        if self.over or self.defend_cooldown > 0:
            return
        p = self.player
        self.defend_cooldown = 4
        heal = int(p.max_hp * 0.10)
        p.player_hp = min(p.max_hp, p.player_hp + heal)
        counter = self._mult(max(1, p.damage // 2))
        self.enemy_hp -= counter
        self.log(f"🛡️ PERFECT PARRY! +{heal} HP and {counter} counter damage!")
        self._end_player_action(defended=True)

    def do_run(self):
        if self.over:
            return
        if random.random() < 0.20:
            self.log(f"You escaped from the {self.encounter}!")
            self.over = True
            self.fled = True
        else:
            self.log("Escape failed! The enemy attacks!")
            self._end_player_action()

    def do_item(self, item):
        if self.over:
            return
        p = self.player
        if item == "Health potion":
            if not p.has_item(item):
                self.log("You don't have any Health Potions!"); return
            p.remove_item(item)
            heal = int(p.max_hp * 0.20)
            p.player_hp = min(p.max_hp, p.player_hp + heal)
            self.log(f"🧪 Restored {heal} HP!")
        elif item == "Bandage":
            if not p.has_item(item):
                self.log("You don't have any Bandages!"); return
            p.remove_item(item)
            self.bleed_turns = 0
            self.log("🩹 Bleeding cured!")
        elif item == "Antidote":
            if not p.has_item(item):
                self.log("You don't have any Antidotes!"); return
            p.remove_item(item)
            self.poison_turns = 0
            self.log("🧪 Poison cured!")
        elif item == "Damage Potion":
            available = min(p.item_count(item), 3 - len(self.damage_potion_timers))
            if available <= 0:
                self.log("❌ No usable Damage Potions! Max 3 active stacks."); return
            p.remove_item(item)
            self.damage_potion_timers.append(3)
            self.log(f"🔥 Damage Potion activated! Multiplier x{2 ** len(self.damage_potion_timers)} for 3 turns.")
        else:
            return
        self._end_player_action(is_item=True)

    # ------------------------------------------------------------------
    def _end_player_action(self, defended=False, daze_enemy=False, is_item=False):
        p = self.player
        if self.defend_cooldown > 0:
            self.defend_cooldown -= 1
        if self.feint_cooldown > 0:
            self.feint_cooldown -= 1

        if self.damage_potion_timers:
            before = len(self.damage_potion_timers)
            self.damage_potion_timers = tick_damage_potion_timers(self.damage_potion_timers)
            if before and not self.damage_potion_timers:
                self.log("⚗️ Damage Potion effect expired.")

        if self.enemy_hp <= 0:
            self._on_victory()
            return

        if daze_enemy:
            return  # enemy loses its turn entirely, no start_of_round re-tick needed here
        if defended:
            self.log(f"🛡️ You completely blocked the {self.encounter}'s attack!")
        elif not is_item:
            self._enemy_turn()
        else:
            return

        if p.player_hp <= 0 and not self.over:
            self.log("You were defeated! You woke up in the village with half your gold.")
            p.gold = max(0, p.gold // 2)
            p.player_hp = p.max_hp
            self.over = True
            self.victory = False
            return

        self.start_of_round()

    def _enemy_turn(self):
        p = self.player
        lo, hi = self.dmg_lo, self.dmg_hi
        dealt = random.randint(lo, hi)
        if self.is_enraged:
            dealt += 5

        if random.random() < 0.25:
            e = self.encounter
            if e == "Venomous Stalker":
                if random.random() >= p.poison_resistance / 100:
                    self.poison_turns = 4
                    self.log("🐍 Venomous Stalker used VENOM STRIKE!")
                else:
                    self.log("🛡️ Your poison resistance blocked VENOM STRIKE!")
            elif e == "Corrupted Treant":
                self.armor_broken_turns = 3
                self.log("🪵 Corrupted Treant used ARMOR CRUSH!")
            elif e == "Corrupted Drake":
                if random.random() >= p.poison_resistance / 100:
                    self.poison_turns = 3
                    self.log("🐉 Corrupted Drake used CORRUPTED BREATH!")
                else:
                    self.log("🛡️ Your poison resistance blocked the Drake's poison!")
                self.armor_broken_turns = 2
                self.log("🐉 Corrupted Drake cracked your armor!")
            elif e == "Blighted Beast":
                steal = int(dealt * 0.5 * (1 - p.life_steal_resistance / 100))
                old = self.enemy_hp
                self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + steal)
                self.log(f"💀 Blighted Beast used LIFE DRAIN! Recovered {self.enemy_hp - old} HP.")
            elif e == "Corrupted Knight":
                steal = int(dealt * 0.45 * (1 - p.life_steal_resistance / 100))
                old = self.enemy_hp
                self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + steal)
                self.log(f"🗡️ Corrupted Knight used UNHOLY DRAIN! Recovered {self.enemy_hp - old} HP.")
            elif e in ("Wolf", "Alpha Dire Wolf"):
                self.bleed_turns = 3
                self.log(f"🐺 The {e} used BITE & BLEED!")

        effective_armor = 0 if self.armor_broken_turns > 0 else self.player.armor_reduction
        final = max(1, dealt - effective_armor)
        p.player_hp -= final
        self.log(f"The {self.encounter} dealt {final} damage to you!")

    def _on_victory(self):
        gained_exp = random.randint(self.exp_lo, self.exp_hi)
        gained_gold = random.randint(self.gold_lo, self.gold_hi)
        self.player.exp += gained_exp
        self.player.gold += gained_gold
        self.rewards = {"gold": gained_gold, "exp": gained_exp}
        self.log(f"🏆 You defeated the {self.encounter}! +{gained_exp} EXP +{gained_gold} gold.")
        aq = self.player.active_quest
        if aq and aq.get("target") == self.encounter:
            aq["progress"] += 1
            self.log(f"🎯 Quest progress: {aq['progress']}/{aq['required']}")
            if aq["progress"] >= aq["required"]:
                self.player.gold += aq["gold_reward"]
                self.player.exp += aq["exp_reward"]
                self.log(f"🎉 QUEST COMPLETE! +{aq['gold_reward']} gold +{aq['exp_reward']} EXP!")
                if aq.get("source") == "clark":
                    self.player.valoria_quests_completed += 1
                self.player.active_quest = None
        self.over = True
        self.victory = True


# =========================================================================
# DEATH FOREST
# =========================================================================
def death_forest_hit_damage(encounter, hit_count, armor_reduction, armor_broken):
    data_ = DEATH_FOREST_ENEMIES[encounter]
    if encounter == "Thornbound Executioner":
        raw = 400 if hit_count % 2 == 0 else 300
    elif encounter == "Bloodroot Ravager":
        raw = 300 + (300 if hit_count % 2 == 0 else 0)
    elif encounter == "Grave Warden" and hit_count % 2 == 0:
        raw = 400
    else:
        raw = random.randint(*data_["damage"])
    armor = 0 if armor_broken else armor_reduction
    return max(1, raw - armor), raw


def death_forest_first_strike(encounter, armor_reduction):
    if encounter == "Rotfang":
        return max(1, random.randint(100, 130) - armor_reduction)
    if encounter == "Crypt Stalker" and random.random() < 0.35:
        return max(1, random.randint(70, 100) - armor_reduction)
    return 0


class DeathForestBattle(LogMixin):
    CATEGORY = "death_forest"

    def __init__(self, encounter, player):
        self.encounter = encounter
        self.player = player
        info = DEATH_FOREST_ENEMIES[encounter]
        self.enemy_max_hp = info["hp"]
        self.enemy_hp = info["hp"]
        self.exp_reward = info["exp"]
        self.gold_reward = info["gold"]

        self.bleed_turns = 0
        self.poison_turns = 0
        self.armor_broken_turns = 0
        self.curse_turns = 0
        self.stunned = False
        self.executioner_healed = False
        self.grave_warden_healed = False
        self.grave_warden_special_used = False
        self.hit_count = 0
        self.damage_potion_timers = []
        self.defend_cooldown = 0
        self.feint_cooldown = 0
        self.feint_buff = False

        self.messages = []
        self.over = False
        self.victory = False
        self.fled = False
        self.rewards = {"gold": 0, "exp": 0}
        self.antidote_allowed = encounter != "Thornbound Executioner"

        if player.has_item("Speed Potion"):
            self.log("⚡ Speed Potion preserved: Death Forest enemies do not dodge.")

        first = death_forest_first_strike(encounter, player.armor_reduction)
        if encounter == "Rotfang":
            player.player_hp = max(0, player.player_hp - first)
            if random.random() >= player.poison_resistance / 100:
                self.poison_turns = 3
                pmsg = "Poison applied."
            else:
                pmsg = "Your poison resistance blocked the poison."
            self.bleed_turns = 3
            self.armor_broken_turns = 3
            self.log(f"🩸 ROTFANG used FIRST STRIKE! You took {first} damage!")
            self.log(f"☠️ {pmsg} Bleeding and armor break applied immediately!")
        elif encounter == "Crypt Stalker" and first > 0:
            player.player_hp = max(0, player.player_hp - first)
            self.log(f"🗡️ CRYPT STALKER used FIRST STRIKE! You took {first} damage!")

        self.start_of_round()

    def start_of_round(self):
        p = self.player
        if self.poison_turns > 0:
            base = 12 if self.encounter == "Rotfang" else 10
            dmg = max(1, int(base * (1 - p.poison_resistance / 100)))
            p.player_hp = max(0, p.player_hp - dmg)
            self.poison_turns -= 1
            self.log(f"☠️ Poison deals {dmg} damage. ({self.poison_turns} left)")
        if self.bleed_turns > 0:
            p.player_hp = max(0, p.player_hp - 10)
            self.bleed_turns -= 1
            self.log(f"🩸 Bleeding deals 10 damage. ({self.bleed_turns} left)")
        if self.armor_broken_turns > 0:
            self.armor_broken_turns -= 1
            self.log(f"🦴 Armor Break active. ({self.armor_broken_turns} left)")
        if self.curse_turns > 0:
            self.curse_turns -= 1
            self.log(f"☠️ Curse active. ({self.curse_turns} left)")
        self.defend_cooldown = max(0, self.defend_cooldown - 1)
        self.feint_cooldown = max(0, self.feint_cooldown - 1)

        if p.player_hp <= 0:
            self._on_defeat()

    def _mult(self, val):
        val = int(val)
        if self.curse_turns:
            val = max(1, int(val * 0.85))
        if self.damage_potion_timers:
            val *= 2 ** len(self.damage_potion_timers)
        return val

    def do_attack(self, kind):
        if self.over:
            return
        if self.stunned:
            self.log("💫 ROOTBOUND! You lose this turn!")
            self.stunned = False
            self._end_action(enemy_turn=True)
            return
        p = self.player
        dealt = 0
        daze = False
        if kind == "light":
            dealt = self._mult(random.randint(max(1, p.damage - 2), p.damage + 2) * (1.5 if random.random() < 0.15 else 1.0))
            self.enemy_hp -= dealt
            self.log(f"⚔️ Light Attack dealt {dealt} damage.")
        elif kind == "heavy":
            miss = 0.30 if self.feint_buff else 0.50
            if random.random() < miss:
                self.log("💨 Heavy Attack MISSED!")
                self.feint_buff = False
            else:
                if self.feint_buff:
                    self.log("🎯 Feint Buff consumed!")
                    self.feint_buff = False
                raw = random.randint(max(1, int(p.damage * 1.5)), max(1, int(p.damage * 1.75)))
                dealt = self._mult(raw * (1.5 if random.random() < 0.10 else 1.0))
                self.enemy_hp -= dealt
                self.log(f"🪓 Heavy Attack dealt {dealt} damage.")
        elif kind == "quick":
            dealt = self._mult(random.randint(max(1, p.damage - 2), p.damage))
            self.enemy_hp -= dealt
            self.log(f"⚡ Quick Strike dealt {dealt} damage.")
            if self.enemy_hp > 0 and random.random() < 0.50:
                daze = True
                self.log(f"💫 {self.encounter} was DAZED and loses its turn!")
        elif kind == "feint":
            if self.feint_cooldown:
                return
            dealt = self._mult(max(1, p.damage // 2))
            self.enemy_hp -= dealt
            self.feint_buff = True
            self.feint_cooldown = 4
            self.log(f"🤺 Feint & Strike dealt {dealt} damage.")
        elif kind == "wild":
            dealt = self._mult(random.randint(1, max(1, p.damage * 2)) * (2.5 if random.random() < 0.15 else 1.0))
            self.enemy_hp -= dealt
            self.log(f"🌀 Wild Swing dealt {dealt} damage.")

        self._end_action(enemy_turn=not daze)

    def do_defend(self):
        if self.over or self.defend_cooldown:
            return
        p = self.player
        self.defend_cooldown = 4
        heal = int(p.max_hp * 0.10)
        p.player_hp = min(p.max_hp, p.player_hp + heal)
        counter = self._mult(max(1, p.damage // 2))
        self.enemy_hp -= counter
        self.log(f"🛡️ PERFECT PARRY! +{heal} HP and {counter} counter damage.")
        self._end_action(enemy_turn=False, defended=True)

    def do_run(self):
        if self.over:
            return
        if random.random() < 0.20:
            self.log(f"🏃 You escaped from {self.encounter}!")
            self.over = True
            self.fled = True
        else:
            self.log("❌ Escape failed! The enemy attacks!")
            self._end_action(enemy_turn=True)

    def do_item(self, item, amount=1):
        if self.over:
            return
        p = self.player
        if item == "Health potion":
            if not p.has_item(item):
                self.log("❌ No Health Potion."); return
            p.remove_item(item)
            heal = int(p.max_hp * 0.20)
            p.player_hp = min(p.max_hp, p.player_hp + heal)
            self.log(f"🧪 Restored {heal} HP.")
        elif item == "Bandage":
            if not p.has_item(item):
                self.log("❌ No Bandage."); return
            p.remove_item(item)
            self.bleed_turns = 0
            self.log("🩹 Bleeding cured.")
        elif item == "Antidote":
            if not self.antidote_allowed:
                self.log("☠️ Thornbound Executioner has DISABLED your Antidotes!"); return
            if not p.has_item(item):
                self.log("❌ No Antidote."); return
            p.remove_item(item)
            self.poison_turns = 0
            self.log("🧪 Poison cured.")
        elif item == "Damage Potion":
            available = min(p.item_count(item), 3 - len(self.damage_potion_timers))
            amount = max(1, min(amount, available))
            if available <= 0:
                self.log("❌ No usable Damage Potions."); return
            for _ in range(amount):
                p.remove_item(item)
                self.damage_potion_timers.append(3)
            self.log(f"🔥 Damage multiplier now x{2 ** len(self.damage_potion_timers)}.")
        else:
            return
        self._end_action(enemy_turn=False, is_item=True)

    def _end_action(self, enemy_turn, defended=False, is_item=False):
        if self.damage_potion_timers and not is_item:
            before = len(self.damage_potion_timers)
            self.damage_potion_timers = tick_damage_potion_timers(self.damage_potion_timers)
            if before and not self.damage_potion_timers:
                self.log("⚗️ Damage Potion effect expired.")

        if self.enemy_hp <= 0:
            self._on_victory()
            return

        if self.encounter == "Thornbound Executioner" and not self.executioner_healed and self.enemy_hp <= self.enemy_max_hp * 0.10:
            self.enemy_hp = self.enemy_max_hp
            self.executioner_healed = True
            self.log("☠️ ROOT REBIRTH! THORNBOUND EXECUTIONER FULLY HEALS!")

        if is_item:
            return

        if enemy_turn:
            self._enemy_turn()
            if self.player.player_hp <= 0:
                self._on_defeat()
                return

        self.start_of_round()

    def _enemy_turn(self):
        p = self.player
        self.hit_count += 1
        dealt, raw = death_forest_hit_damage(self.encounter, self.hit_count, p.armor_reduction, self.armor_broken_turns > 0)
        p.player_hp = max(0, p.player_hp - dealt)
        self.log(f"💀 {self.encounter} dealt {dealt} damage.")

        e = self.encounter
        if e == "Rotfang":
            if random.random() < 0.35:
                if random.random() >= p.poison_resistance / 100:
                    self.poison_turns = max(self.poison_turns, 3)
                self.bleed_turns = max(self.bleed_turns, 3)
                self.armor_broken_turns = max(self.armor_broken_turns, 3)
                self.log("🩸 ROTFANG'S FANGS! Poison, bleeding and armor break applied!")
        elif e == "Bloodroot Ravager":
            heal = max(0, int(raw * 0.20 * (1 - p.life_steal_resistance / 100)))
            self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal)
            if heal:
                self.log(f"🩸 BLOODROOT LIFESTEAL! Recovered {heal} HP.")
            if random.random() < 0.20 and random.random() >= p.poison_resistance / 100:
                self.poison_turns = max(self.poison_turns, 2)
                self.log("🌿 BLOODROOT VENOM! Poison applied!")
        elif e == "Death Crawler":
            if random.random() < 0.20 and p.player_hp > 0:
                extra = max(1, random.randint(75, 100) - (0 if self.armor_broken_turns > 0 else p.armor_reduction))
                p.player_hp = max(0, p.player_hp - extra)
                self.log(f"🕷️ DOUBLE STRIKE! Death Crawler hit again for {extra} damage!")
            if random.random() < 0.85:
                if random.random() >= p.poison_resistance / 100:
                    self.poison_turns = max(self.poison_turns, 3)
                    self.log("🧪 VENOM BITE! Poison applied for 3 turns.")
                else:
                    self.log("🛡️ Poison resistance blocked Venom Bite!")
                self.bleed_turns = max(self.bleed_turns, 2)
                self.log("🩸 VENOM BITE! Bleed applied for 2 turns.")
        elif e == "Necromancer":
            if random.random() < 0.18 and p.player_hp > 0:
                skeleton = random.randint(50, 80)
                skeleton = max(1, skeleton - (0 if self.armor_broken_turns > 0 else p.armor_reduction))
                p.player_hp = max(0, p.player_hp - skeleton)
                self.log(f"💀 SKELETON SUMMON! A skeleton hit you for {skeleton} damage!")
            if random.random() < 0.12:
                self.curse_turns = max(self.curse_turns, 2)
                self.log("☠️ CURSE! Your damage is reduced by 15% for 2 turns.")
        elif e == "Crypt Stalker":
            if random.random() < 0.12:
                self.stunned = True
                self.log("💫 CRIPPLING BLOW! You are stunned for 1 turn!")
        elif e == "Bone Golem":
            if random.random() < 0.12:
                self.armor_broken_turns = max(self.armor_broken_turns, 3)
                self.log("🦴 CRUSHING SLAM! Your armor is broken for 3 turns!")
        elif e == "Grave Warden":
            if self.hit_count % 2 == 0:
                self.log("💀 DARK SMITE! Grave Warden unleashed its 400-damage special attack!")
            if not self.grave_warden_healed and self.enemy_hp <= self.enemy_max_hp * 0.40:
                self.enemy_hp = self.enemy_max_hp
                self.grave_warden_healed = True
                self.log("☠️ DARK HEAL! GRAVE WARDEN RETURNS TO 100% HP!")
        elif e == "Thornbound Executioner":
            heal = max(0, int(raw * 0.50 * (1 - p.life_steal_resistance / 100)))
            self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal)
            if heal:
                self.log(f"🩸 THORNBOUND LIFESTEAL! Recovered {heal} HP.")
            if random.random() >= p.poison_resistance / 100:
                self.poison_turns = max(self.poison_turns, 3)
            self.bleed_turns = max(self.bleed_turns, 3)
            self.armor_broken_turns = max(self.armor_broken_turns, 3)
            self.log("🌿 THORN EXECUTION! Poison, bleeding and armor break applied!")
            if random.random() < 0.20 and p.player_hp > 0:
                self.stunned = True
                self.log("💫 ROOTBOUND! You are stunned for 1 turn!")

    def _on_victory(self):
        self.player.exp += self.exp_reward
        self.player.gold += self.gold_reward
        self.rewards = {"gold": self.gold_reward, "exp": self.exp_reward}
        self.log(f"🏆 You defeated {self.encounter}! +{self.exp_reward} EXP +{self.gold_reward} gold.")
        aq = self.player.active_quest
        if aq and aq.get("target") == self.encounter:
            aq["progress"] += 1
            self.log(f"🎯 Bounty progress: {aq['progress']}/{aq['required']}")
            if aq["progress"] >= aq["required"]:
                self.player.gold += aq["gold_reward"]
                self.player.exp += aq["exp_reward"]
                self.log(f"🎉 BOUNTY COMPLETE! +{aq['gold_reward']} gold +{aq['exp_reward']} EXP!")
                if aq.get("source") == "clark":
                    self.player.valoria_quests_completed = min(3, self.player.valoria_quests_completed + 1)
                self.player.active_quest = None
        self.over = True
        self.victory = True

    def _on_defeat(self):
        self.player.gold = max(0, int(self.player.gold * 0.10))
        self.player.exp = max(0, int(self.player.exp * 0.50))
        self.player.player_hp = self.player.max_hp
        self.log("☠️ YOU WERE DEFEATED IN THE DEATH FOREST!")
        self.log("💰 Lost 90% of your gold. ✨ Lost 50% of your EXP.")
        self.over = True
        self.victory = False


# =========================================================================
# THE LAST WITNESS (Apex boss)
# =========================================================================
def last_witness_phase(enemy_hp, enemy_max_hp=LAST_WITNESS_MAX_HP):
    return 1 if enemy_hp > enemy_max_hp * 0.50 else 2


def last_witness_normal_damage(phase):
    if phase == 1:
        return random.randint(300, 420)
    if phase == 2:
        return random.randint(350, 500)
    raise ValueError("Only phases 1 and 2 exist.")


def forest_uplift(player_hp, max_hp):
    target_hp = max(1, int((int(max_hp) * 0.05) + 0.5))
    return target_hp, True


class LastWitnessBattle(LogMixin):
    CATEGORY = "boss"

    def __init__(self, player):
        self.player = player
        self.enemy_max_hp = LAST_WITNESS_MAX_HP
        self.enemy_hp = self.enemy_max_hp
        self.uplift_used = False
        self.poison_turns = 0
        self.bleed_turns = 0
        self.armor_broken_turns = 0
        self.curse_turns = 0
        self.stunned = False
        self.damage_potion_timers = []
        self.defend_cooldown = 0

        self.messages = []
        self.over = False
        self.victory = False
        self.rewards = {"gold": 0, "exp": 0}

        self.log("👁️ THE LAST WITNESS AWAKENS. 30,000 HP. Exactly 2 phases.")
        self.start_of_round()

    @property
    def phase(self):
        return last_witness_phase(self.enemy_hp, self.enemy_max_hp)

    def start_of_round(self):
        p = self.player
        if self.poison_turns > 0:
            dmg = max(1, int(15 * (1 - p.poison_resistance / 100)))
            p.player_hp = max(0, p.player_hp - dmg)
            self.poison_turns -= 1
            self.log(f"☠️ Corruption deals {dmg} damage. ({self.poison_turns} left)")
        if self.bleed_turns > 0:
            p.player_hp = max(0, p.player_hp - 8)
            self.bleed_turns -= 1
            self.log(f"🩸 Bleeding deals 8 damage. ({self.bleed_turns} left)")
        if self.armor_broken_turns > 0:
            self.armor_broken_turns -= 1
            self.log(f"🦴 Armor remains broken. ({self.armor_broken_turns} left)")
        if self.curse_turns > 0:
            self.curse_turns -= 1
            self.log(f"☠️ Corruption weakens your attacks. ({self.curse_turns} left)")
        self.defend_cooldown = max(0, self.defend_cooldown - 1)
        if p.player_hp <= 0:
            self._on_defeat()

    def _mult(self, val):
        val = int(val)
        if self.curse_turns > 0:
            val = int(val * 0.50)
        val = int(val * (2 ** len(self.damage_potion_timers)))
        return val

    def do_attack(self, kind):
        """kind: normal / heavy"""
        if self.over:
            return
        if self.stunned:
            self.log("💫 ROOTBOUND! You are stunned and lose this turn!")
            self.stunned = False
            self._resolve_enemy_phase()
            return
        p = self.player
        multiplier = 1.0 if kind == "normal" else 1.75
        raw = random.randint(max(1, p.damage - 2), p.damage + 2)
        dealt = self._mult(raw * multiplier)
        if kind == "heavy" and random.random() < 0.30:
            self.log("💨 Your Heavy Attack MISSED!")
            dealt = 0
        if dealt > 0:
            if random.random() < (0.15 if kind == "normal" else 0.10):
                dealt = int(dealt * 1.5)
                self.log("⚡ CRITICAL HIT!")
            self.enemy_hp = max(0, self.enemy_hp - dealt)
            self.log(f"⚔️ You dealt {dealt} damage.")
        self._after_action()

    def do_defend(self):
        if self.over or self.defend_cooldown:
            return
        p = self.player
        self.defend_cooldown = 4
        heal = int(p.max_hp * 0.10)
        p.player_hp = min(p.max_hp, p.player_hp + heal)
        counter = self._mult(max(1, p.damage // 2))
        self.enemy_hp = max(0, self.enemy_hp - counter)
        self.log(f"🛡️ PERFECT PARRY! +{heal} HP and {counter} counter damage.")
        self._after_action(defended=True)

    def do_item(self, item):
        if self.over:
            return
        p = self.player
        if item == "Health potion":
            if not p.has_item(item):
                self.log("❌ No Health Potions."); return
            p.remove_item(item)
            heal = int(p.max_hp * 0.20)
            p.player_hp = min(p.max_hp, p.player_hp + heal)
            self.log(f"🧪 Restored {heal} HP.")
        elif item == "Bandage":
            if not p.has_item(item):
                self.log("❌ No Bandages."); return
            p.remove_item(item)
            self.bleed_turns = 0
            self.log("🩹 Bleeding cured.")
        elif item == "Antidote":
            if not p.has_item(item):
                self.log("❌ No Antidotes."); return
            p.remove_item(item)
            self.poison_turns = 0
            self.log("🧪 Corruption cleansed.")
        elif item == "Speed Potion":
            self.log("⚡ The Last Witness cannot dodge. Speed Potion was not consumed.")
            return
        elif item == "Damage Potion":
            if not p.has_item(item) or len(self.damage_potion_timers) >= 3:
                self.log("❌ No usable Damage Potion stacks."); return
            p.remove_item(item)
            self.damage_potion_timers.append(3)
            self.log(f"🔥 Damage Potion active: x{2 ** len(self.damage_potion_timers)} damage for 3 turns.")
        else:
            return
        self._after_action(is_item=True)

    def _after_action(self, defended=False, is_item=False):
        if self.damage_potion_timers and not is_item:
            before = len(self.damage_potion_timers)
            self.damage_potion_timers = tick_damage_potion_timers(self.damage_potion_timers)
            if before and not self.damage_potion_timers:
                self.log("⚗️ Damage Potion effect expired.")

        if self.enemy_hp <= 0:
            self._on_victory()
            return

        self._resolve_enemy_phase(defended=defended)

    def _resolve_enemy_phase(self, defended=False):
        p = self.player
        phase = self.phase
        if phase == 2 and not self.uplift_used and random.random() < 0.30:
            self.uplift_used = True
            p.player_hp, _ = forest_uplift(p.player_hp, p.max_hp)
            self.log("🌲 FOREST UPLIFT! Leaves you at the nearest whole-number value to 5% HP.")
            self.start_of_round()
            return

        if defended:
            self.log("🛡️ The Last Witness strikes, but your perfect block absorbs everything!")
            self.start_of_round()
            return

        boss_damage = last_witness_normal_damage(phase)
        final_damage = boss_damage if self.armor_broken_turns else max(1, boss_damage - p.armor_reduction)
        p.player_hp = max(0, p.player_hp - final_damage)
        self.log(f"☠️ The Last Witness dealt {final_damage} damage.")

        if phase == 2 and p.player_hp > 0 and random.random() < 0.35:
            effect = random.choice(("poison", "bleed", "armor", "curse"))
            if effect == "poison":
                self.poison_turns = max(self.poison_turns, 3); self.log("☠️ ABSOLUTE CORRUPTION! Poison inflicted!")
            elif effect == "bleed":
                self.bleed_turns = max(self.bleed_turns, 3); self.log("🩸 ABSOLUTE CORRUPTION! Bleeding inflicted!")
            elif effect == "armor":
                self.armor_broken_turns = max(self.armor_broken_turns, 3); self.log("🦴 ABSOLUTE CORRUPTION! Armor broken!")
            else:
                self.curse_turns = max(self.curse_turns, 2)
                self.log("🌿 TANGLING OF DESTRUCTION! Your damage is reduced by 50%!")
                self.stunned = True

        if p.player_hp <= 0:
            self._on_defeat()
            return
        self.start_of_round()

    def _on_victory(self):
        p = self.player
        if "Forest Heart" not in p.inventory:
            p.inventory.append("Forest Heart")
        p.exp += 50000
        p.gold += 100000
        self.rewards = {"gold": 100000, "exp": 50000}
        self.log("🏆 YOU DEFEATED THE LAST WITNESS! 🌲 THE FOREST HEART HAS BEEN CLAIMED.")
        self.log("✨ +50,000 EXP | +100,000 GOLD | Forest Heart obtained!")
        self.over = True
        self.victory = True

    def _on_defeat(self):
        p = self.player
        p.player_hp = p.max_hp
        p.level = max(1, p.level - 5)
        p.exp_needed = get_exp_needed(p.level)
        self.log("☠️ YOU WERE DEFEATED BY THE LAST WITNESS. The forest claims 5 levels from you.")
        self.over = True
        self.victory = False




# ==========================================================================
# SCREENS — every screen in the game
# ==========================================================================

import math
import random
import pygame



# ===========================================================================
# Base screen + shared helpers
# ===========================================================================
class Screen:
    def __init__(self, app):
        self.app = app
        self.buttons = []
        self.t = 0.0

    def on_enter(self):
        pass

    def on_resume(self):
        pass

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        self.t += dt
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(mouse, dt)

    def draw(self, surf):
        pass


def draw_header(surf, title, subtitle=None):
    draw_text(surf, title, (WIDTH // 2, 54), size=40, color=GOLD, bold=True, center=True)
    if subtitle:
        draw_text(surf, subtitle, (WIDTH // 2, 92), size=18, color=TEXT_DIM, center=True)


def draw_status_bar(surf, player):
    rect = pygame.Rect(20, 20, 340, 92)
    rounded_panel(surf, rect, color=(18, 22, 20), border=PANEL_BORDER, alpha=225)
    draw_text(surf, f"{player.name}" + ("  👑" if player.is_admin else ""), (rect.x + 14, rect.y + 8), size=20, color=GOLD, bold=True)
    draw_text(surf, f"Lv. {player.level}", (rect.right - 14, rect.y + 8), size=18, color=TEXT, align="right")
    hp_ratio = player.player_hp / max(1, player.max_hp)
    hp_color = HP_GREEN if hp_ratio > 0.5 else (HP_YELLOW if hp_ratio > 0.25 else HP_RED)
    bar(surf, (rect.x + 14, rect.y + 34, rect.w - 28, 16), hp_ratio, hp_color)
    draw_text(surf, f"{player.player_hp}/{player.max_hp} HP", (rect.x + rect.w // 2, rect.y + 42), size=13, color=WHITE, center=True, shadow=False)
    exp_ratio = player.exp / max(1, player.exp_needed) if player.exp_needed else 1.0
    bar(surf, (rect.x + 14, rect.y + 56, rect.w - 28, 10), exp_ratio, EXP_BLUE)
    draw_text(surf, f"💰 {player.gold:,}   ⚔️ {player.damage}   🛡️ {player.armor_reduction}", (rect.x + 14, rect.y + 70), size=14, color=TEXT_DIM)


# ===========================================================================
# CLOUD ACCOUNT / SAVE SERVICE
# ===========================================================================
# v1.6 uses account-backed cloud saves as the PRIMARY persistence layer.
# Configure OAKHAVEN_API_URL to point at the deployed Oakhaven backend.
# Save codes remain available only as an optional backup/export mechanism.

CLOUD_API_URL = os.environ.get("OAKHAVEN_API_URL", "http://127.0.0.1:8000").rstrip("/")
CLOUD_REQUEST_TIMEOUT = 12


class CloudSaveError(Exception):
    pass


class CloudSaveService:
    """Small dependency-free REST client used by the Pygame client.

    The server owns passwords, account records, and save data. The game only
    keeps the short-lived session token and the current PlayerState in memory.
    """
    def __init__(self, base_url=CLOUD_API_URL):
        self.base_url = base_url.rstrip("/")
        self.token = None
        self.username = None
        self.logged_in = False

    def _request_sync(self, method, path, payload=None):
        body = None
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=CLOUD_REQUEST_TIMEOUT) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))
            except Exception:
                detail = {}
            raise CloudSaveError(detail.get("detail", f"Cloud server returned HTTP {exc.code}."))
        except Exception as exc:
            raise CloudSaveError(f"Could not reach the cloud server: {exc}")

    async def register(self, username, password, display_name):
        return await asyncio.to_thread(self._register_sync, username, password, display_name)

    def _register_sync(self, username, password, display_name):
        data = self._request_sync("POST", "/auth/register", {
            "username": username, "password": password, "display_name": display_name
        })
        self.token = data["token"]
        self.username = data.get("username", username)
        self.logged_in = True
        return data

    async def login(self, username, password):
        return await asyncio.to_thread(self._login_sync, username, password)

    def _login_sync(self, username, password):
        data = self._request_sync("POST", "/auth/login", {"username": username, "password": password})
        self.token = data["token"]
        self.username = data.get("username", username)
        self.logged_in = True
        return data

    async def load_save(self):
        return await asyncio.to_thread(self._request_sync, "GET", "/save")

    async def save_player(self, player_dict):
        return await asyncio.to_thread(self._request_sync, "PUT", "/save", {"save": player_dict})

    def logout(self):
        self.token = None
        self.username = None
        self.logged_in = False


# ===========================================================================
# LOGIN
# ===========================================================================
class LoginScreen(Screen):
    def on_enter(self):
        cx = WIDTH // 2
        self.user_in = TextInput((cx - 180, 270, 360, 48), placeholder="Username")
        self.pass_in = TextInput((cx - 180, 340, 360, 48), placeholder="Password", password=True)
        self.error = ""
        self.busy = False
        self.buttons = [
            Button((cx - 180, 420, 170, 52), "Login", self._login, size=22),
            Button((cx + 10, 420, 170, 52), "Create Account", lambda: self.app.push(NewAccountScreen(self.app)), size=20),
            Button((cx - 180, 485, 170, 46), "Offline Backup", lambda: self.app.push(LoadGameScreen(self.app)), size=18, base_color=(40, 40, 44)),
            Button((cx + 10, 485, 170, 46), "Exit", self.app.quit, size=18, base_color=(60, 30, 30), accent=DANGER),
        ]

    def _login(self):
        if self.busy:
            return
        username = self.user_in.text.strip()
        password = self.pass_in.text
        if not username or not password:
            self.error = "Enter both your username and password."
            return
        self.busy = True
        self.error = "Connecting to Oakhaven Cloud..."
        self.app.start_task(self._login_async(username, password))

    async def _login_async(self, username, password):
        try:
            data = await self.app.cloud.login(username, password)
            save = data.get("save")
            if save:
                self.app.player = PlayerState.from_dict(save)
                self.app.toast.push(f"Cloud save loaded — welcome back, {self.app.player.name}!", ACCENT)
                self.app.goto_village()
            else:
                # Valid account with no save yet: create the first character.
                self.app.player = PlayerState(data.get("display_name") or username)
                self.app.toast.push("Account ready. Your journey will now save to the cloud.", ACCENT)
                self.app.goto_village(fresh=True)
                self.app.autosave_silent()
        except CloudSaveError as exc:
            self.error = f"❌ {exc}"
        except Exception as exc:
            self.error = f"❌ Login failed: {exc}"
        finally:
            self.busy = False

    def handle_event(self, event):
        super().handle_event(event)
        self.user_in.handle_event(event)
        self.pass_in.handle_event(event)

    def update(self, dt):
        super().update(dt)
        self.user_in.update(dt)
        self.pass_in.update(dt)

    def draw(self, surf):
        draw_background(surf, self.t, "forest")
        draw_header(surf, "OAKHAVEN", "The Tale of the Corrupted Root  •  v1.6")
        draw_text(surf, "Sign in to load your cloud save automatically", (WIDTH // 2, 145), size=19, color=ACCENT, center=True)
        draw_text(surf, "Your account is the save slot. Save codes are only an optional backup.", (WIDTH // 2, 175), size=14, color=TEXT_DIM, center=True)
        draw_text(surf, "Username", (WIDTH // 2 - 180, 248), size=15, color=TEXT_DIM)
        draw_text(surf, "Password", (WIDTH // 2 - 180, 318), size=15, color=TEXT_DIM)
        self.user_in.draw(surf)
        self.pass_in.draw(surf)
        for b in self.buttons:
            b.enabled = not self.busy or b.text in ("Exit",)
            b.draw(surf)
        if self.error:
            draw_text(surf, self.error, (WIDTH // 2, 555), size=15, color=DANGER if "❌" in self.error else TEXT_DIM, center=True)


class NewAccountScreen(Screen):
    def on_enter(self):
        cx = WIDTH // 2
        self.name_in = TextInput((cx - 180, 270, 360, 48), placeholder="Username")
        self.display_in = TextInput((cx - 180, 340, 360, 48), placeholder="Warden name")
        self.pass_in = TextInput((cx - 180, 410, 360, 48), placeholder="Password (8+ characters)", password=True)
        self.error = ""
        self.busy = False
        self.buttons = [
            Button((cx - 180, 485, 170, 50), "Back", lambda: self.app.pop(), base_color=(40, 40, 44)),
            Button((cx + 10, 485, 170, 50), "Create", self._begin, size=21),
        ]

    def _begin(self):
        if self.busy:
            return
        username = self.name_in.text.strip()
        display_name = self.display_in.text.strip() or username
        password = self.pass_in.text
        if len(username) < 3:
            self.error = "Username must be at least 3 characters."
            return
        if len(password) < 8:
            self.error = "Password must be at least 8 characters."
            return
        self.busy = True
        self.error = "Creating secure cloud account..."
        self.app.start_task(self._create_async(username, display_name, password))

    async def _create_async(self, username, display_name, password):
        try:
            await self.app.cloud.register(username, password, display_name)
            self.app.player = PlayerState(display_name)
            self.app.toast.push("Account created. Cloud saving is now active.", ACCENT)
            self.app.push(StoryPopupScreen(
                self.app, "THE TALE OF THE CORRUPTED ROOT",
                [
                    "For decades, the Village of Oakhaven lived in peace under the shadow of the",
                    "Ancient Forest. But recently, a dark miasma has crept out from the woods.",
                    "Monsters grow aggressive, trees twist into abominations, and the air tastes of venom.",
                    "",
                    f"Elder Marcus appointed {display_name} as Oakhaven's newest Warden.",
                    "Your duty: cleanse the woods, grow in strength, and uncover the source of the",
                    "Corruption before it swallows the village whole!",
                ],
                on_continue=lambda: (self.app.goto_village(fresh=True), self.app.autosave_silent()),
                mood="forest",
            ))
        except CloudSaveError as exc:
            self.error = f"❌ {exc}"
        except Exception as exc:
            self.error = f"❌ Account creation failed: {exc}"
        finally:
            self.busy = False

    def handle_event(self, event):
        super().handle_event(event)
        self.name_in.handle_event(event)
        self.display_in.handle_event(event)
        self.pass_in.handle_event(event)

    def update(self, dt):
        super().update(dt)
        self.name_in.update(dt); self.display_in.update(dt); self.pass_in.update(dt)

    def draw(self, surf):
        draw_background(surf, self.t, "forest")
        draw_header(surf, "Create Warden Account", "Your progress will be tied to this account")
        draw_text(surf, "Username", (WIDTH // 2 - 180, 248), size=15, color=TEXT_DIM)
        draw_text(surf, "Warden Name", (WIDTH // 2 - 180, 318), size=15, color=TEXT_DIM)
        draw_text(surf, "Password", (WIDTH // 2 - 180, 388), size=15, color=TEXT_DIM)
        self.name_in.draw(surf); self.display_in.draw(surf); self.pass_in.draw(surf)
        for b in self.buttons:
            b.enabled = not self.busy
            b.draw(surf)
        if self.error:
            draw_text(surf, self.error, (WIDTH // 2, 560), size=15, color=DANGER if "❌" in self.error else TEXT_DIM, center=True)


class LoadGameScreen(Screen):
    """Legacy/manual save-code import. Cloud login is the normal path."""
    def on_enter(self):
        cx = WIDTH // 2
        self.code_in = TextInput((cx - 300, 320, 600, 52), placeholder="Paste your backup save code here", max_len=4000)
        self.error = ""
        self.buttons = [
            Button((cx - 160, 400, 150, 50), "Back", lambda: self.app.pop(), base_color=(40, 40, 44)),
            Button((cx + 10, 400, 150, 50), "Import", self._load),
        ]

    def _load(self):
        d = load_from_save_code(self.code_in.text)
        if d is None:
            self.error = "❌ Invalid or corrupted save code."
            return
        self.app.player = PlayerState.from_dict(d)
        self.app.toast.push("Backup loaded. Log in to a cloud account to sync it.", GOLD)
        self.app.goto_village()

    def handle_event(self, event):
        super().handle_event(event); self.code_in.handle_event(event)

    def update(self, dt):
        super().update(dt); self.code_in.update(dt)

    def draw(self, surf):
        draw_background(surf, self.t, "forest")
        draw_header(surf, "Offline Backup Import", "Optional fallback — cloud accounts are the primary save system")
        self.code_in.draw(surf)
        if self.error:
            draw_text(surf, self.error, (WIDTH // 2, 390), size=16, color=DANGER, center=True)
        for b in self.buttons: b.draw(surf)


# ===========================================================================
# Generic story / message popup
# ===========================================================================
class StoryPopupScreen(Screen):
    def __init__(self, app, title, lines, on_continue=None, mood="forest", reward_text=None):
        super().__init__(app)
        self.title = title
        self.lines = lines
        self.on_continue = on_continue
        self.mood = mood
        self.reward_text = reward_text

    def on_enter(self):
        cx = WIDTH // 2
        self.buttons = [Button((cx - 100, HEIGHT - 100, 200, 52), "Continue", self._continue)]

    def _continue(self):
        self.app.pop()
        if self.on_continue:
            self.on_continue()

    def draw(self, surf):
        draw_background(surf, self.t, self.mood)
        panel = pygame.Rect(WIDTH // 2 - 420, 110, 840, 500)
        rounded_panel(surf, panel, color=(16, 18, 18), border=GOLD, alpha=235, radius=18)
        draw_text(surf, self.title, (panel.centerx, panel.y + 44), size=30, color=GOLD, bold=True, center=True)
        y = panel.y + 100
        for line in self.lines:
            draw_text(surf, line, (panel.centerx, y), size=18, color=TEXT, center=True)
            y += 30
        if self.reward_text:
            draw_text(surf, self.reward_text, (panel.centerx, panel.bottom - 70), size=20, color=ACCENT, bold=True, center=True)
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# LEVEL UP (modal, chained until all pending levels are resolved)
# ===========================================================================
class LevelUpScreen(Screen):
    def __init__(self, app, on_done):
        super().__init__(app)
        self.on_done = on_done

    def on_enter(self):
        cx = WIDTH // 2
        self.buttons = [
            Button((cx - 220, 420, 200, 70), "+15 Max HP", lambda: self._choose("hp"), size=22),
            Button((cx + 20, 420, 200, 70), "+3 Damage", lambda: self._choose("dmg"), size=22),
        ]

    def _choose(self, stat):
        p = self.app.player
        p.apply_level_up(stat)
        self.app.toast.push(f"Level {p.level}! +{'15 Max HP' if stat=='hp' else '3 Damage'}", GOLD)
        self.app.pop()
        self.on_done()

    def draw(self, surf):
        draw_background(surf, self.t, "forest")
        p = self.app.player
        panel = pygame.Rect(WIDTH // 2 - 320, 180, 640, 340)
        rounded_panel(surf, panel, color=(16, 18, 18), border=GOLD, alpha=240, radius=18)
        draw_text(surf, "🎉 LEVEL UP!", (panel.centerx, panel.y + 50), size=36, color=GOLD, bold=True, center=True)
        draw_text(surf, f"You reached Level {p.level + 1}!", (panel.centerx, panel.y + 96), size=22, color=TEXT, center=True)
        draw_text(surf, "Choose 1 stat point to increase:", (panel.centerx, panel.y + 150), size=18, color=TEXT_DIM, center=True)
        for b in self.buttons:
            b.draw(surf)


def resolve_progression(app, on_done):
    """Chains LevelUpScreen prompts until the player has no pending level-ups."""
    p = app.player
    if p.ready_to_level():
        app.push(LevelUpScreen(app, lambda: resolve_progression(app, on_done)))
    else:
        on_done()


# ===========================================================================
# VILLAGE HUB (root screen)
# ===========================================================================
class VillageScreen(Screen):
    def on_enter(self):
        self._check_story_triggers()

    def on_resume(self):
        self._build_buttons()
        self._check_story_triggers()

    def _check_story_triggers(self):
        p = self.app.player
        if p is None:
            return
        if p.level >= 20 and not p.story_lvl20_seen:
            p.story_lvl20_seen = True
            reward = ""
            if p.item_count("Antidote") < MAX_ANTIDOTES:
                p.add_item("Antidote", 1)
                reward = "🧪 Received 1x free Antidote from Elder Marcus!"
            else:
                p.gold += 200
                reward = "💰 Antidotes full — Elder Marcus gives you 200 gold instead."
            self.app.push(StoryPopupScreen(
                self.app, "CHAPTER 1: BEYOND THE TREE LINE",
                [
                    f"As you return to the village, Elder Marcus approaches with a grim face.",
                    f'"{p.name}, your strength has grown impressive, but I fear the corruption has',
                    'deepened. The barriers at the Edge of the Deep Forest have collapsed.',
                    'Corrupted Treants and Venomous Stalkers are spilling toward Oakhaven."',
                    "",
                    'He hands you a sealed vial of purple liquid.',
                    '"Take this Antidote. You must hold the line in the Deep Forest Edge!"',
                ],
                on_continue=lambda: (self.app.autosave_silent(), self._check_story_triggers()),
                mood="forest", reward_text=reward,
            ))
            return
        if p.level >= 50 and not p.story_lvl50_seen:
            p.story_lvl50_seen = True
            p.gold += 2000
            self.app.push(StoryPopupScreen(
                self.app, "CHAPTER 2: THE DARK FOREST",
                [
                    "You emerge from the Deep Forest, battered but victorious.",
                    f'Elder Marcus: "{p.name}, the corruption spreads further than we feared!"',
                    "Daylight fades beyond the Deep Forest. Shadow Specters, Blighted Beasts,",
                    "and armored undead now stalk the Dark Forest Ruins.",
                    "",
                    '"Here — all the gold I claimed on my adventures. Steel yourself, Warden."',
                    "",
                    "📖 New Zone Unlocked: Dark Forest Ruins (Lv. 50-89)",
                ],
                on_continue=lambda: (self.app.autosave_silent(), self._check_story_triggers()),
                mood="forest", reward_text="💰 +2000 Gold",
            ))
            return
        self._build_buttons()

    def _build_buttons(self):
        p = self.app.player
        cx = WIDTH // 2
        y0 = 220
        gap = 66
        opts = [
            ("🌲 Venture out to train", self._train),
            ("🏪 Village Shop", lambda: self.app.push(ShopScreen(self.app))),
            ("📜 Bounty Board", lambda: self.app.push(BountyBoardScreen(self.app))),
            ("🏰 Town Gate", lambda: self.app.push(GateScreen(self.app))),
            ("🎒 Inventory", lambda: self.app.push(InventoryScreen(self.app))),
            ("💾 Save Game", lambda: self.app.push(SaveCodeScreen(self.app))),
        ]
        if p.is_admin:
            opts.append(("🔧 Admin Menu", lambda: self.app.push(AdminScreen(self.app))))
        opts.append(("🚪 Exit Game", self.app.quit))

        self.buttons = []
        for i, (label, cb) in enumerate(opts):
            col = i % 2
            row = i // 2
            rect = (cx - 310 + col * 330, y0 + row * gap, 300, 52)
            self.buttons.append(Button(rect, label, cb, size=20))

    def _train(self):
        p = self.app.player
        if p.level >= 20:
            self.app.push(ZoneSelectScreen(self.app))
        else:
            self.app.start_forest_zone("forest")

    def draw(self, surf):
        draw_background(surf, self.t, "forest")
        p = self.app.player
        draw_header(surf, "OAKHAVEN VILLAGE", f"Welcome home, {p.name}")
        draw_status_bar(surf, p)
        if p.active_quest:
            aq = p.active_quest
            rect = pygame.Rect(WIDTH - 380, 20, 340, 60)
            rounded_panel(surf, rect, color=(22, 20, 14), border=GOLD, alpha=220)
            draw_text(surf, "📜 Active Bounty", (rect.x + 12, rect.y + 8), size=15, color=GOLD)
            draw_text(surf, f"{aq['target']} — {aq['progress']}/{aq['required']}", (rect.x + 12, rect.y + 30), size=16, color=TEXT)
        cx, cy = WIDTH // 2, 170
        draw_hero(surf, cx, cy, self.t, weapon=p.equipped_weapon(), armor=p.equipped_armor(), scale=1.3)
        for b in self.buttons:
            b.draw(surf)


class ZoneSelectScreen(Screen):
    def on_enter(self):
        cx = WIDTH // 2
        self.buttons = [
            Button((cx - 220, 330, 440, 60), "🌲 Forest (Lv. 1-19)", lambda: self.app.start_forest_zone("forest"), size=22),
            Button((cx - 220, 410, 440, 60), "🌑 Deep Forest Edge (Lv. 20-49)", lambda: self.app.start_forest_zone("deep_forest"), size=22),
            Button((cx - 100, 500, 200, 50), "Back", lambda: self.app.pop(), base_color=(40, 40, 44)),
        ]

    def draw(self, surf):
        draw_background(surf, self.t, "forest")
        draw_header(surf, "Where would you like to venture?")
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# SHOP (village)
# ===========================================================================
class ShopScreen(Screen):
    def on_enter(self):
        self._build()

    def _build(self):
        p = self.app.player
        cx = WIDTH // 2
        self.buttons = []
        rows = self._rows()
        y = 190
        for label, price, cb, enabled in rows:
            self.buttons.append(Button((cx - 340, y, 500, 54), label, cb, enabled=enabled, size=18))
            y += 62
        self.buttons.append(Button((cx - 340 + 520, 190, 200, 54), "Back to Village", self.app.goto_village, base_color=(40, 40, 44)))

    def _rows(self):
        p = self.app.player
        rows = []
        # weapon
        if "Steel Longsword" in p.inventory:
            rows.append(("⚔️ Steel Longsword (owned — strongest)", None, lambda: None, False))
        elif "Old sword" in p.inventory:
            rows.append(("⚔️ Upgrade: Steel Longsword — 750g (+25 dmg)", 750, lambda: self._buy_weapon("Steel Longsword", 750, 25, "Old sword"), p.gold >= 750))
        else:
            rows.append(("⚔️ Old Sword — 250g (+15 dmg)", 250, lambda: self._buy_weapon("Old sword", 250, 15, None), p.gold >= 250))
        # armor
        if "Iron Plate Armor" in p.inventory:
            rows.append(("🛡️ Iron Plate Armor (owned — strongest)", None, lambda: None, False))
        elif "Leather Tunic" in p.inventory:
            rows.append(("🛡️ Upgrade: Iron Plate Armor — 950g (armor 12)", 950, lambda: self._buy_armor("Iron Plate Armor", 950, 12, "Leather Tunic"), p.gold >= 950))
        else:
            rows.append(("🛡️ Leather Tunic — 300g (armor 5)", 300, lambda: self._buy_armor("Leather Tunic", 300, 5, None), p.gold >= 300))

        heal = int(p.max_hp * 0.20)
        rows.append((f"🧪 Health Potion — 30g (+{heal} HP) [{p.item_count('Health potion')}/{MAX_POTIONS}]", 30,
                     lambda: self._buy_item("Health potion", 30, MAX_POTIONS), p.gold >= 30 and p.item_count("Health potion") < MAX_POTIONS))
        rows.append((f"🩹 Bandage — 50g (cures bleed) [{p.item_count('Bandage')}/{MAX_BANDAGES}]", 50,
                     lambda: self._buy_item("Bandage", 50, MAX_BANDAGES), p.gold >= 50 and p.item_count("Bandage") < MAX_BANDAGES))
        rows.append((f"🧪 Antidote — 100g (cures poison) [{p.item_count('Antidote')}/{MAX_ANTIDOTES}]", 100,
                     lambda: self._buy_item("Antidote", 100, MAX_ANTIDOTES), p.gold >= 100 and p.item_count("Antidote") < MAX_ANTIDOTES))
        rows.append((f"⚡ Speed Potion — 500g (-30% enemy dodge) [{p.item_count('Speed Potion')}/{MAX_SPEED_POTIONS}]", 500,
                     lambda: self._buy_item("Speed Potion", 500, MAX_SPEED_POTIONS), p.gold >= 500 and p.item_count("Speed Potion") < MAX_SPEED_POTIONS))
        return rows

    def _buy_weapon(self, name, cost, dmg, remove):
        p = self.app.player
        if p.gold < cost:
            return
        p.gold -= cost
        if remove:
            p.remove_item(remove)
        p.inventory.append(name)
        p.damage += dmg
        self.app.toast.push(f"Bought {name}!", ACCENT)
        self._build()

    def _buy_armor(self, name, cost, armor, remove):
        p = self.app.player
        if p.gold < cost:
            return
        p.gold -= cost
        if remove:
            p.remove_item(remove)
        p.inventory.append(name)
        p.armor_reduction = armor
        self.app.toast.push(f"Bought {name}!", ACCENT)
        self._build()

    def _buy_item(self, name, cost, cap):
        p = self.app.player
        if p.gold < cost or p.item_count(name) >= cap:
            return
        p.gold -= cost
        p.add_item(name, 1)
        self.app.toast.push(f"Bought {name}!", ACCENT)
        self.app.autosave_silent()
        self._build()

    def draw(self, surf):
        draw_background(surf, self.t, "town")
        p = self.app.player
        draw_header(surf, "OAKHAVEN VILLAGE SHOP")
        draw_status_bar(surf, p)
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# BOUNTY BOARD
# ===========================================================================
class BountyBoardScreen(Screen):
    def on_enter(self):
        self._build()

    def _build(self):
        p = self.app.player
        cx = WIDTH // 2
        self.buttons = [Button((cx - 100, HEIGHT - 80, 200, 50), "Back to Village", self.app.goto_village, base_color=(40, 40, 44))]
        if p.active_quest:
            aq = p.active_quest
            self.buttons.insert(0, Button((cx - 150, 300, 300, 54), "Abandon Quest",
                                              self._abandon, base_color=(60, 30, 30), accent=DANGER))
            self._active_text = f"Defeat {aq['required']} {aq['target']}s — Progress {aq['progress']}/{aq['required']}"
        else:
            self._active_text = None
            y = 200
            for b in BOUNTIES:
                if p.level < b["min_level"]:
                    continue
                label = f"Hunt {b['required']} {b['target']}(s) — {b['gold_reward']}g / {b['exp_reward']} EXP"
                self.buttons.insert(-1, Button((cx - 320, y, 640, 48), label, (lambda bb=b: self._accept(bb)), size=17))
                y += 54

    def _accept(self, bounty):
        p = self.app.player
        p.active_quest = {"target": bounty["target"], "required": bounty["required"], "progress": 0,
                           "gold_reward": bounty["gold_reward"], "exp_reward": bounty["exp_reward"]}
        self.app.toast.push(f"Accepted: Hunt {bounty['required']} {bounty['target']}(s)!", GOLD)
        self.app.autosave_silent()
        self._build()

    def _abandon(self):
        self.app.player.active_quest = None
        self.app.toast.push("Quest abandoned.", TEXT_DIM)
        self._build()

    def draw(self, surf):
        draw_background(surf, self.t, "town")
        p = self.app.player
        draw_header(surf, "VILLAGE NOTICE BOARD")
        draw_status_bar(surf, p)
        if self._active_text:
            draw_text(surf, "📜 Active Quest", (WIDTH // 2, 220), size=24, color=GOLD, center=True, bold=True)
            draw_text(surf, self._active_text, (WIDTH // 2, 260), size=20, color=TEXT, center=True)
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# TOWN GATE -> VALORIA
# ===========================================================================
class GateScreen(Screen):
    def on_enter(self):
        p = self.app.player
        cx = WIDTH // 2
        if p.level >= 50:
            self.buttons = [
                Button((cx - 220, 380, 440, 60), "Enter Town of Valoria", lambda: self._enter(), size=22),
                Button((cx - 100, 460, 200, 50), "Back to Village", self.app.goto_village, base_color=(40, 40, 44)),
            ]
        else:
            self.buttons = [Button((cx - 100, 460, 200, 50), "Back to Village", self.app.goto_village, base_color=(40, 40, 44))]

    def _enter(self):
        p = self.app.player
        p.valoria_unlocked = True
        p.visited_valoria = True
        self.app.push(ValoriaHubScreen(self.app))

    def draw(self, surf):
        draw_background(surf, self.t, "town")
        p = self.app.player
        draw_header(surf, "THE TOWN GATES OF VALORIA")
        draw_status_bar(surf, p)
        if p.level >= 50:
            draw_text(surf, 'Guard Captain: "Halt, Warden! The legends speak of your deeds!"', (WIDTH // 2, 220), size=18, color=TEXT, center=True)
            draw_text(surf, 'Guard Captain: "Beyond these gates lies the Town of Valoria. Retired', (WIDTH // 2, 250), size=18, color=TEXT, center=True)
            draw_text(surf, 'Warden Clark awaits your arrival!"', (WIDTH // 2, 280), size=18, color=TEXT, center=True)
        else:
            draw_text(surf, 'Guard Captain: "Halt! The road to Valoria is blocked by the monster surge."', (WIDTH // 2, 240), size=18, color=TEXT, center=True)
            draw_text(surf, 'Only Wardens who have proven themselves in the Deep Forest (Lv. 50) may pass.', (WIDTH // 2, 270), size=16, color=TEXT_DIM, center=True)
            draw_text(surf, f"(Your Level: {p.level}/50)", (WIDTH // 2, 300), size=16, color=GOLD, center=True)
        for b in self.buttons:
            b.draw(surf)


class ValoriaHubScreen(Screen):
    def on_enter(self):
        p = self.app.player
        cx = WIDTH // 2
        opts = [
            ("⚔️ Valoria Arms & Armor Shop", lambda: self.app.push(ValoriaShopScreen(self.app))),
            ("👴 Seek out Retired Warden Clark", lambda: self.app.push(ClarkScreen(self.app))),
        ]
        if p.level >= 90:
            opts.append(("☠️ Adventure to the Death Forest (Lv. 90+)", self._death_forest))
        opts.append(("🏘️ Return to Oakhaven", self.app.goto_village))
        self.buttons = []
        y = 230
        for label, cb in opts:
            self.buttons.append(Button((cx - 260, y, 520, 56), label, cb, size=20))
            y += 66

    def _death_forest(self):
        self.app.start_death_forest()

    def draw(self, surf):
        draw_background(surf, self.t, "town")
        p = self.app.player
        draw_header(surf, "TOWN OF VALORIA")
        draw_status_bar(surf, p)
        for b in self.buttons:
            b.draw(surf)


class ValoriaShopScreen(Screen):
    def on_enter(self):
        self._build()

    def _build(self):
        p = self.app.player
        cx = WIDTH // 2
        self.buttons = []
        y = 180
        for w in VALORIA_WEAPONS:
            owned = w["name"] in p.inventory
            better_owned = any(WEAPON_ORDER.index(x) > WEAPON_ORDER.index(w["name"]) for x in p.inventory if x in WEAPON_ORDER)
            label = f"⚔️ {w['name']} (owned)" if owned else f"⚔️ {w['name']} — {w['cost']:,}g ({w['desc']})"
            enabled = (not owned) and (not better_owned) and p.gold >= w["cost"]
            self.buttons.append(Button((cx - 340, y, 680, 46), label, (lambda ww=w: self._buy_weapon(ww)), enabled=enabled, size=16))
            y += 52
        for a in VALORIA_ARMOR:
            owned = a["name"] in p.inventory
            better_owned = any(ARMOR_ORDER.index(x) > ARMOR_ORDER.index(a["name"]) for x in p.inventory if x in ARMOR_ORDER)
            label = f"🛡️ {a['name']} (owned)" if owned else f"🛡️ {a['name']} — {a['cost']:,}g ({a['desc']})"
            enabled = (not owned) and (not better_owned) and p.gold >= a["cost"]
            self.buttons.append(Button((cx - 340, y, 680, 46), label, (lambda aa=a: self._buy_armor(aa)), enabled=enabled, size=16))
            y += 52
        dp = p.item_count("Damage Potion")
        self.buttons.append(Button((cx - 340, y, 680, 46), f"💥 Damage Potion — 800g [{dp}/{MAX_DAMAGE_POTIONS}]",
                                       self._buy_potion, enabled=p.gold >= 800 and dp < MAX_DAMAGE_POTIONS, size=16))
        y += 60
        self.buttons.append(Button((cx - 100, y, 200, 50), "Back", lambda: self.app.pop(), base_color=(40, 40, 44)))

    def _buy_weapon(self, w):
        p = self.app.player
        if p.gold < w["cost"] or w["name"] in p.inventory:
            return
        for old in WEAPON_ORDER:
            if old in p.inventory and old != w["name"]:
                p.remove_item(old)
        p.gold -= w["cost"]
        p.inventory.append(w["name"])
        p.damage += w["dmg_add"]
        self.app.toast.push(f"Acquired {w['name']}!", ACCENT)
        self._build()

    def _buy_armor(self, a):
        p = self.app.player
        if p.gold < a["cost"] or a["name"] in p.inventory:
            return
        for old in ARMOR_ORDER:
            if old in p.inventory and old != a["name"]:
                p.remove_item(old)
        p.gold -= a["cost"]
        p.inventory.append(a["name"])
        p.armor_reduction = a["armor"]
        p.poison_resistance = a.get("poison_res", p.poison_resistance)
        p.life_steal_resistance = a.get("life_steal_res", p.life_steal_resistance)
        self.app.toast.push(f"Acquired {a['name']}!", ACCENT)
        self._build()

    def _buy_potion(self):
        p = self.app.player
        if p.gold < 800 or p.item_count("Damage Potion") >= MAX_DAMAGE_POTIONS:
            return
        p.gold -= 800
        p.add_item("Damage Potion", 1)
        self.app.toast.push("Bought a Damage Potion!", ACCENT)
        self._build()

    def draw(self, surf):
        draw_background(surf, self.t, "town")
        p = self.app.player
        draw_header(surf, "VALORIA ARMS & ARMOR")
        draw_status_bar(surf, p)
        for b in self.buttons:
            b.draw(surf)


class ClarkScreen(Screen):
    def on_enter(self):
        self._build()

    def _build(self):
        p = self.app.player
        cx = WIDTH // 2
        self.buttons = [Button((cx - 100, HEIGHT - 80, 200, 50), "Back", lambda: self.app.pop(), base_color=(40, 40, 44))]
        if p.valoria_quests_completed >= 4:
            self.info = "✅ Clark's final reward has already been claimed."
        elif p.valoria_quests_completed >= 3:
            self.info = "🎉 All 3 Clark quests complete! Claim your reward below."
            self.buttons.insert(0, Button((cx - 160, 340, 320, 56), "Claim Final Reward", self._claim, size=20))
        elif p.active_quest:
            aq = p.active_quest
            self.info = f"Current bounty: {aq['target']} — {aq['progress']}/{aq['required']}"
        else:
            self.info = None
            y = 280
            for q in CLARK_QUESTS:
                label = f"Hunt {q['required']} {q['target']}(s) — {q['gold_reward']}g / {q['exp_reward']} EXP"
                self.buttons.insert(-1, Button((cx - 300, y, 600, 48), label, (lambda qq=q: self._accept(qq)), size=17))
                y += 56

    def _accept(self, q):
        p = self.app.player
        p.active_quest = {"target": q["target"], "required": q["required"], "progress": 0,
                           "gold_reward": q["gold_reward"], "exp_reward": q["exp_reward"], "source": "clark"}
        self.app.toast.push(f"Accepted Clark's bounty: {q['target']}!", GOLD)
        self._build()

    def _claim(self):
        p = self.app.player
        superior_sword = any(x in p.inventory for x in ("Mythril Sword", "Absolute Adamantium Hellfire"))
        superior_armor = any(x in p.inventory for x in ("Mythrillic Armor", "Adamantium Hellfire"))
        got_sword = "Diamond Sword" in p.inventory or superior_sword
        got_armor = "Diamond Armor" in p.inventory or superior_armor
        if got_sword and got_armor:
            p.gold += 5000
            self.app.toast.push("Already own the Diamond Set or better — received 5000 Gold!", GOLD)
        else:
            if not got_sword:
                p.inventory.append("Diamond Sword")
                p.damage += 50
            if not got_armor:
                p.inventory.append("Diamond Armor")
                p.armor_reduction = max(p.armor_reduction, 50)
            p.gold += 3500
            self.app.toast.push("Received 3500 Gold + applicable Diamond Set pieces!", GOLD)
        p.valoria_quests_completed = 4
        self._build()

    def draw(self, surf):
        draw_background(surf, self.t, "town")
        p = self.app.player
        draw_header(surf, "RETIRED WARDEN CLARK")
        draw_status_bar(surf, p)
        draw_text(surf, f'Clark: "Ah, {p.name}, I have been expecting you."', (WIDTH // 2, 200), size=18, color=TEXT, center=True)
        draw_text(surf, "Complete my bounties, and I'll grant a reward worthy of a hero.", (WIDTH // 2, 228), size=16, color=TEXT_DIM, center=True)
        if self.info:
            draw_text(surf, self.info, (WIDTH // 2, 270), size=18, color=GOLD, center=True)
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# INVENTORY
# ===========================================================================
class InventoryScreen(Screen):
    def on_enter(self):
        cx = WIDTH // 2
        self.buttons = [Button((cx - 100, HEIGHT - 80, 200, 50), "Back to Village", self.app.goto_village, base_color=(40, 40, 44))]

    def draw(self, surf):
        draw_background(surf, self.t, "town")
        p = self.app.player
        draw_header(surf, "🎒 INVENTORY", f"{len(p.inventory)} total items")
        draw_status_bar(surf, p)
        panel = pygame.Rect(WIDTH // 2 - 380, 150, 760, 460)
        rounded_panel(surf, panel, color=(16, 18, 18), border=PANEL_BORDER, alpha=225)
        y = panel.y + 24
        for label, cap in [("Health Potions", MAX_POTIONS), ("Bandages", MAX_BANDAGES),
                            ("Antidotes", MAX_ANTIDOTES), ("Speed Potions", MAX_SPEED_POTIONS),
                            ("Damage Potions", MAX_DAMAGE_POTIONS)]:
        
            key = {"Health Potions": "Health potion", "Bandages": "Bandage", "Antidotes": "Antidote",
                   "Speed Potions": "Speed Potion", "Damage Potions": "Damage Potion"}[label]
            draw_text(surf, f"{label}: {p.item_count(key)}/{cap}", (panel.x + 30, y), size=20, color=TEXT)
            y += 34
        y += 10
        others = [i for i in p.inventory if i not in CONSUMABLES]
        draw_text(surf, "Equipment & Key Items:", (panel.x + 30, y), size=20, color=GOLD, bold=True)
        y += 36
        if others:
            for item in sorted(set(others)):
                draw_text(surf, f"• {item}", (panel.x + 50, y), size=18, color=TEXT_DIM)
                y += 28
        else:
            draw_text(surf, "(none yet)", (panel.x + 50, y), size=18, color=TEXT_FAINT)
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# SAVE CODE
# ===========================================================================
class SaveCodeScreen(Screen):
    def on_enter(self):
        self.code = generate_save_code(self.app.player.to_dict())
        cx = WIDTH // 2
        self.buttons = [
            Button((cx - 220, HEIGHT - 100, 200, 52), "Copy to Clipboard", self._copy),
            Button((cx + 20, HEIGHT - 100, 200, 52), "Back to Village", self.app.goto_village, base_color=(40, 40, 44)),
        ]

    def _copy(self):
        try:
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, self.code.encode("utf-8"))
            self.app.toast.push("Save code copied to clipboard!", ACCENT)
        except Exception:
            self.app.toast.push("Clipboard unavailable — select the code manually.", DANGER)

    def draw(self, surf):
        draw_background(surf, self.t, "forest")
        p = self.app.player
        draw_header(surf, "💾 YOUR SAVE CODE", "Keep this safe — it's your entire game state")
        panel = pygame.Rect(WIDTH // 2 - 460, 160, 920, 380)
        rounded_panel(surf, panel, color=(14, 16, 16), border=GOLD, alpha=235)
        wrapped = [self.code[i:i + 60] for i in range(0, len(self.code), 60)]
        y = panel.y + 24
        for line in wrapped[:14]:
            draw_text(surf, line, (panel.x + 24, y), size=16, color=ACCENT, shadow=False)
            y += 24
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# ADMIN
# ===========================================================================
class AdminScreen(Screen):
    def on_enter(self):
        cx = WIDTH // 2
        opts = [
            ("Max Out Stats", self._max_stats),
            ("Get All Items", self._all_items),
            ("Jump to Level 50", lambda: self._jump(50)),
            ("Jump to Level 90", lambda: self._jump(90)),
            ("Unlock All Zones", self._unlock_zones),
            ("Add 99,999 Gold", self._add_gold),
            ("Reset Game Progress", self._reset),
            ("Back", self.app.goto_village),
        ]
        self.buttons = []
        y = 190
        for label, cb in opts:
            self.buttons.append(Button((cx - 200, y, 400, 50), label, cb, size=19,
                                           base_color=(60, 30, 30) if label == "Reset Game Progress" else PANEL_LIGHT))
            y += 58

    def _max_stats(self):
        p = self.app.player
        p.max_hp = 500; p.player_hp = 500; p.damage = 300; p.gold += 50000; p.level = 100
        self.app.toast.push("Stats maxed!", GOLD)

    def _all_items(self):
        p = self.app.player
        for name, cap in CAPS.items():
            while p.item_count(name) < cap:
                p.inventory.append(name)
        if "Absolute Adamantium Hellfire" not in p.inventory:
            p.inventory.append("Absolute Adamantium Hellfire"); p.damage += 300
        if "Adamantium Hellfire" not in p.inventory:
            p.inventory.append("Adamantium Hellfire"); p.armor_reduction = 200; p.life_steal_resistance = 50
        self.app.toast.push("All items acquired!", GOLD)

    def _jump(self, lvl):
        p = self.app.player
        p.level = lvl
        p.story_lvl20_seen = True
        p.story_lvl50_seen = True
        p.valoria_unlocked = True
        if lvl >= 90:
            p.visited_valoria = True
            p.valoria_quests_completed = 3
        self.app.toast.push(f"Jumped to Level {lvl}!", GOLD)

    def _unlock_zones(self):
        p = self.app.player
        p.story_lvl20_seen = True
        p.story_lvl50_seen = True
        p.valoria_unlocked = True
        p.visited_valoria = True
        if p.level < 50:
            p.level = 50
        self.app.toast.push("All zones unlocked!", GOLD)

    def _add_gold(self):
        self.app.player.gold += 99999
        self.app.toast.push("+99,999 Gold!", GOLD)

    def _reset(self):
        self.app.player = PlayerState(self.app.player.name)
        self.app.toast.push("Progress reset.", DANGER)
        self.app.goto_village()

    def draw(self, surf):
        draw_background(surf, self.t, "town")
        draw_header(surf, "🔧 ADMIN TESTING MENU")
        draw_status_bar(surf, self.app.player)
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# TREASURE
# ===========================================================================
class TreasureScreen(Screen):
    def __init__(self, app, gold, exp, items_found, mood="forest"):
        super().__init__(app)
        self.gold = gold
        self.exp = exp
        self.items_found = items_found
        self.mood = mood

    def on_enter(self):
        p = self.app.player
        p.gold += self.gold
        p.exp += self.exp
        cx = WIDTH // 2
        self.buttons = [Button((cx - 100, HEIGHT - 120, 200, 52), "Continue", self._continue)]
        self.app.autosave_silent()

    def _continue(self):
        self.app.pop()
        resolve_progression(self.app, self.app.goto_village)

    def draw(self, surf):
        draw_background(surf, self.t, self.mood)
        panel = pygame.Rect(WIDTH // 2 - 320, 180, 640, 340)
        rounded_panel(surf, panel, color=(20, 22, 16), border=GOLD, alpha=235, radius=18)
        draw_text(surf, "💰 TREASURE FOUND!", (panel.centerx, panel.y + 50), size=32, color=GOLD, bold=True, center=True)
        draw_text(surf, f"+{self.gold} Gold   •   +{self.exp} EXP", (panel.centerx, panel.y + 110), size=22, color=TEXT, center=True)
        y = panel.y + 160
        for item in self.items_found:
            draw_text(surf, f"✨ Found: {item}", (panel.centerx, y), size=18, color=ACCENT, center=True)
            y += 28
        for b in self.buttons:
            b.draw(surf)


# ===========================================================================
# COMBAT
# ===========================================================================
ENEMY_VISUAL = {}
for _n, _d in REGULAR_ENEMIES.items():
    ENEMY_VISUAL[_n] = (_d["shape"], _d["color"])
for _n, _d in DEATH_FOREST_ENEMIES.items():
    ENEMY_VISUAL[_n] = (_d["shape"], _d["color"])
ENEMY_VISUAL["The Last Witness"] = ("witness", (90, 40, 30))


class CombatScreen(Screen):
    def __init__(self, app, battle, encounter_name, mood="forest", on_finish=None):
        super().__init__(app)
        self.battle = battle
        self.encounter_name = encounter_name
        self.mood = mood
        self.on_finish = on_finish or (lambda: self.app.goto_village())
        self.shape, self.color = ENEMY_VISUAL.get(encounter_name, ("blob", (150, 150, 150)))
        self.menu = "main"
        self.hero_flash = 0.0
        self.enemy_flash = 0.0
        self.hero_hurt = 0.0
        self.enemy_hurt = 0.0
        self.hero_attack = 0.0
        self.enemy_attack = 0.0
        self.result_delay = 0.0
        self.dmg_potion_amount = 1

    def on_enter(self):
        self.log = ScrollLog((60, HEIGHT - 200, WIDTH - 120, 130), size=16)
        for m in self.battle.messages:
            self.log.add(m)
        self._enemy_hp_prev = self.battle.enemy_hp
        self._player_hp_prev = self.battle.player.player_hp
        self._build_menu()

    # -- menu construction --------------------------------------------
    def _build_menu(self):
        cx = WIDTH // 2
        by = HEIGHT - 60
        self.buttons = []
        cat = self.battle.CATEGORY
        if self.battle.over:
            self.buttons = [Button((cx - 110, by, 220, 50), "Continue", self._finish, size=22)]
            return

        if self.menu == "main":
            xs = [cx - 430, cx - 210, cx + 10, cx + 230]
            self.buttons.append(Button((xs[0], by, 200, 52), "⚔️ Attack", lambda: self._set_menu("attack"), size=20))
            defend_label = "🛡️ Defend" if self.battle.defend_cooldown == 0 else f"🛡️ Defend ({self.battle.defend_cooldown})"
            self.buttons.append(Button((xs[1], by, 200, 52), defend_label, self._defend, size=20, enabled=self.battle.defend_cooldown == 0))
            self.buttons.append(Button((xs[2], by, 200, 52), "🎒 Items", lambda: self._set_menu("items"), size=20))
            if cat != "boss":
                self.buttons.append(Button((xs[3], by, 200, 52), "🏃 Run", self._run, size=20))
        elif self.menu == "attack":
            p = self.battle.player
            if cat == "boss":
                opts = [("Normal Attack", "normal"), ("Heavy Attack (+75%, 30% miss)", "heavy")]
            else:
                fcd = self.battle.feint_cooldown
                opts = [
                    ("Light Attack", "light"),
                    ("Heavy Attack (50% miss)", "heavy"),
                    ("Quick Strike (50% daze)", "quick"),
                    (f"Feint & Strike{' (CD ' + str(fcd) + ')' if fcd else ''}", "feint"),
                    ("Wild Swing", "wild"),
                ]
            x = cx - (len(opts) * 210) // 2
            for label, kind in opts:
                enabled = not (kind == "feint" and getattr(self.battle, "feint_cooldown", 0) > 0)
                self.buttons.append(Button((x, by - 70, 200, 50), label, (lambda k=kind: self._attack(k)), size=15, enabled=enabled))
                x += 210
            self.buttons.append(Button((cx - 100, by, 200, 46), "Back", lambda: self._set_menu("main"), base_color=(40, 40, 44)))
        elif self.menu == "items":
            p = self.battle.player
            antidote_ok = getattr(self.battle, "antidote_allowed", True)
            opts = [
                (f"🧪 Health Potion ({p.item_count('Health potion')})", "Health potion", p.has_item("Health potion")),
                (f"🩹 Bandage ({p.item_count('Bandage')})", "Bandage", p.has_item("Bandage")),
                (f"🧪 Antidote ({p.item_count('Antidote')})" + ("" if antidote_ok else " [DISABLED]"), "Antidote", p.has_item("Antidote") and antidote_ok),
                (f"🔥 Damage Potion x{2 ** len(getattr(self.battle, 'damage_potion_timers', []))} ({p.item_count('Damage Potion')})", "Damage Potion",
                 p.has_item("Damage Potion") and len(getattr(self.battle, "damage_potion_timers", [])) < 3),
            ]
            x = cx - (len(opts) * 220) // 2
            for label, item, enabled in opts:
                self.buttons.append(Button((x, by - 70, 210, 50), label, (lambda it=item: self._item(it)), size=14, enabled=enabled))
                x += 220
            self.buttons.append(Button((cx - 100, by, 200, 46), "Back", lambda: self._set_menu("main"), base_color=(40, 40, 44)))

    def _set_menu(self, m):
        self.menu = m
        self._build_menu()

    # -- action wrapper --------------------------------------------------
    def _run_action(self, fn):
        b = self.battle
        pre_enemy = b.enemy_hp
        pre_player = b.player.player_hp
        pre_len = len(b.messages)
        fn()
        for m in b.messages[pre_len:]:
            self.log.add(m)
        dmg_enemy = max(0, pre_enemy - b.enemy_hp)
        dmg_player = max(0, pre_player - b.player.player_hp)
        heal_player = max(0, b.player.player_hp - pre_player)
        fx = self.app.fx
        ex, ey = WIDTH - 260, 300
        hx, hy = 260, 340
        if dmg_enemy > 0:
            fx.damage_number((ex, ey - 40), dmg_enemy)
            fx.burst((ex, ey), self.color)
            self.enemy_flash = 0.35
            self.enemy_hurt = 0.3
            self.hero_attack = 0.35
        if dmg_player > 0:
            fx.damage_number((hx, hy - 40), dmg_player)
            fx.burst((hx, hy), DANGER)
            self.hero_flash = 0.35
            self.hero_hurt = 0.3
            fx.shake(10, 0.3)
        if heal_player > 0:
            fx.damage_number((hx, hy - 70), heal_player, kind="heal")
        self.menu = "main"
        self._build_menu()
        if b.over:
            self.result_delay = 0.4

    def _attack(self, kind):
        self._run_action(lambda: self.battle.do_attack(kind))

    def _defend(self):
        self._run_action(lambda: self.battle.do_defend())

    def _run(self):
        self._run_action(lambda: self.battle.do_run())

    def _item(self, item):
        self._run_action(lambda: self.battle.do_item(item))

    def _finish(self):
        self.on_finish()

    def update(self, dt):
        super().update(dt)
        for name in ("hero_flash", "enemy_flash", "hero_hurt", "enemy_hurt", "hero_attack", "enemy_attack"):
            v = getattr(self, name)
            if v > 0:
                setattr(self, name, max(0.0, v - dt * 2.6))
        self.log.handle_event  # no-op reference

    def handle_event(self, event):
        super().handle_event(event)
        self.log.handle_event(event)

    def draw(self, surf):
        draw_background(surf, self.t, self.mood)
        b = self.battle
        p = b.player
        off = self.app.fx.offset()

        # header / phase
        title = self.encounter_name
        if b.CATEGORY == "boss":
            title = f"👁️ THE LAST WITNESS — PHASE {b.phase}"
        draw_header(surf, title)

        # enemy panel (right)
        ex, ey = WIDTH - 260 + off[0], 300 + off[1]
        enemy_scale = 2.2 if b.CATEGORY == "boss" else (1.6 if b.CATEGORY == "death_forest" else 1.3)
        draw_enemy(surf, self.shape, self.color, ex, ey, self.t, scale=enemy_scale,
                            flash=self.enemy_flash * 2.5, attack=self.enemy_attack, hurt=self.enemy_hurt,
                            enraged=getattr(b, "is_enraged", False))
        enemy_ratio = b.enemy_hp / max(1, b.enemy_max_hp)
        bar_rect = (WIDTH - 460, 120, 400, 22)
        bar(surf, bar_rect, enemy_ratio, BOSS_RED if b.CATEGORY == "boss" else HP_RED)
        draw_text(surf, f"{b.enemy_hp:,}/{b.enemy_max_hp:,} HP", (bar_rect[0] + bar_rect[2] // 2, bar_rect[1] + 11), size=14, color=WHITE, center=True, shadow=False)

        # hero panel (left)
        hx, hy = 260 + off[0], 340 + off[1]
        draw_hero(surf, hx, hy, self.t, weapon=p.equipped_weapon(), armor=p.equipped_armor(), scale=1.5,
                           flash=self.hero_flash * 2.5, attack=self.hero_attack, hurt=self.hero_hurt)
        hp_ratio = p.player_hp / max(1, p.max_hp)
        hp_color = HP_GREEN if hp_ratio > 0.5 else (HP_YELLOW if hp_ratio > 0.25 else HP_RED)
        bar_rect2 = (60, 120, 400, 22)
        bar(surf, bar_rect2, hp_ratio, hp_color)
        draw_text(surf, f"{p.player_hp}/{p.max_hp} HP", (bar_rect2[0] + bar_rect2[2] // 2, bar_rect2[1] + 11), size=14, color=WHITE, center=True, shadow=False)
        draw_text(surf, p.name, (bar_rect2[0], bar_rect2[1] - 22), size=16, color=ACCENT)
        draw_text(surf, self.encounter_name, (bar_rect[0] + bar_rect[2], bar_rect[1] - 22), size=16, color=DANGER, align="right")

        # status icons
        status_bits = []
        if getattr(b, "poison_turns", 0): status_bits.append(f"☠️x{b.poison_turns}")
        if getattr(b, "bleed_turns", 0): status_bits.append(f"🩸x{b.bleed_turns}")
        if getattr(b, "armor_broken_turns", 0): status_bits.append(f"🦴x{b.armor_broken_turns}")
        if getattr(b, "curse_turns", 0): status_bits.append(f"🌿x{b.curse_turns}")
        if getattr(b, "damage_potion_timers", []): status_bits.append(f"🔥x{2 ** len(b.damage_potion_timers)}")
        if status_bits:
            draw_text(surf, "  ".join(status_bits), (bar_rect2[0], bar_rect2[1] + 30), size=15, color=POISON)

        self.log.draw(surf)
        self.app.fx.draw(surf)

        if b.over:
            panel = pygame.Rect(WIDTH // 2 - 300, 200, 600, 220)
            win = b.victory
            fled = getattr(b, "fled", False)
            col = GOLD if win else (TEXT_DIM if fled else DANGER)
            title2 = "🏆 VICTORY!" if win else ("🏃 ESCAPED" if fled else "☠️ DEFEATED")
            rounded_panel(surf, panel, color=(16, 18, 16), border=col, alpha=235, radius=16)
            draw_text(surf, title2, (panel.centerx, panel.y + 50), size=32, color=col, bold=True, center=True)
            if win and (b.rewards["gold"] or b.rewards["exp"]):
                draw_text(surf, f"+{b.rewards['exp']} EXP   •   +{b.rewards['gold']} Gold", (panel.centerx, panel.y + 100), size=22, color=TEXT, center=True)

        for btn in self.buttons:
            btn.draw(surf)




# ==========================================================================
# APP — screen stack, game loop, encounter orchestration
# ==========================================================================

import random

import pygame




class App:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Oakhaven — The Tale of the Corrupted Root")
        self.clock = pygame.time.Clock()
        self.running = True

        self.player = None
        self.cloud = CloudSaveService()
        self.last_autosave_code = None
        self.cloud_save_task = None
        self.last_cloud_save_error = ""
        self.stack = []
        self.toast = Toast()
        self.fx = EffectLayer()

        self.push(LoginScreen(self))

    # -- navigation -----------------------------------------------------
    def start_task(self, coro):
        return asyncio.create_task(coro)

    def push(self, screen):
        self.stack.append(screen)
        screen.on_enter()

    def pop(self):
        if len(self.stack) > 1:
            self.stack.pop()
            self.stack[-1].on_resume()

    def top(self):
        return self.stack[-1]

    def goto_village(self, fresh=False):
        self.stack = [VillageScreen(self)]
        self.stack[-1].on_enter()

    def quit(self):
        self.running = False

    def autosave_silent(self):
        """Queue a cloud save; save codes are only generated as an optional backup."""
        if not self.player:
            return None
        try:
            payload = self.player.to_dict()
            code = generate_save_code(payload)
            self.last_autosave_code = code
            if self.cloud.logged_in:
                if self.cloud_save_task and not self.cloud_save_task.done():
                    self.cloud_save_task.cancel()
                self.cloud_save_task = self.start_task(self._cloud_save(payload))
            return code
        except Exception as exc:
            self.last_cloud_save_error = str(exc)
            return None

    async def _cloud_save(self, payload):
        try:
            await self.cloud.save_player(payload)
            self.last_cloud_save_error = ""
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.last_cloud_save_error = str(exc)


    # -- encounter orchestration -----------------------------------------
    def start_forest_zone(self, zone):
        p = self.player
        table = forest_spawn_table(p.level) if zone == "forest" else DEEP_FOREST_TABLE
        names, weights = table
        encounter = random.choices(names, weights=weights, k=1)[0]
        mood = "forest" if zone == "forest" else "death"
        if encounter == "Treasure":
            exp, gold = treasure_reward(p.level)
            self.stack = [VillageScreen(self)]
            self.push(TreasureScreen(self, gold, exp, [], mood=mood))
            return
        battle = Battle(encounter, p)
        self.stack = [VillageScreen(self)]
        self.push(CombatScreen(self, battle, encounter, mood=mood, on_finish=self._after_encounter))

    def start_death_forest(self):
        p = self.player
        if p.level < 90:
            self.toast.push("You must be Level 90+ to enter the Death Forest.", DANGER)
            return
        if p.level >= 150:
            self.push(StoryPopupScreen(
                self, "THE LAST WITNESS STIRS",
                ["You feel an ancient presence deeper in the forest...",
                 "Will you challenge The Last Witness now, or explore the Death Forest instead?"],
                on_continue=self._offer_boss_choice, mood="boss",
            ))
            return
        self._enter_death_forest_encounter()

    def _offer_boss_choice(self):
        # simple two-button prompt reusing a lightweight screen
        self.push(BossChoiceScreen(self))

    def _enter_death_forest_encounter(self):
        p = self.player
        names, weights = DEATH_FOREST_TABLE
        encounter = random.choices(names, weights=weights, k=1)[0]
        if encounter == "Treasure":
            gold = random.randint(250, 600)
            exp = random.randint(300, 700)
            items = []
            if p.item_count("Health potion") < MAX_POTIONS and random.random() < 0.45:
                p.add_item("Health potion", 1); items.append("Health Potion")
            if p.item_count("Bandage") < MAX_BANDAGES and random.random() < 0.35:
                p.add_item("Bandage", 1); items.append("Bandage")
            if p.item_count("Antidote") < MAX_ANTIDOTES and random.random() < 0.25:
                p.add_item("Antidote", 1); items.append("Antidote")
            if p.item_count("Damage Potion") < MAX_DAMAGE_POTIONS and random.random() < 0.05:
                p.add_item("Damage Potion", 1); items.append("Damage Potion (RARE!)")
            self.stack = [VillageScreen(self)]
            self.push(TreasureScreen(self, gold, exp, items, mood="death"))
            return
        battle = DeathForestBattle(encounter, p)
        self.stack = [VillageScreen(self)]
        self.push(CombatScreen(self, battle, encounter, mood="death", on_finish=self._after_encounter))

    def start_boss_fight(self):
        p = self.player
        battle = LastWitnessBattle(p)
        self.stack = [VillageScreen(self)]
        self.push(CombatScreen(self, battle, "The Last Witness", mood="boss", on_finish=self._after_boss))

    def _after_encounter(self):
        self.pop()
        resolve_progression(self, self.goto_village)

    def _after_boss(self):
        self.pop()
        resolve_progression(self, self.goto_village)

    # -- main loop --------------------------------------------------------
    async def run(self):
        # Cooperative frame yield keeps the same Pygame loop usable by desktop
        # Python and browser runtimes such as pygbag.
        cloud_timer = 0.0
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.top().handle_event(event)
            self.top().update(dt)
            cloud_timer += dt
            if cloud_timer >= 20.0 and self.player and self.cloud.logged_in:
                cloud_timer = 0.0
                self.autosave_silent()
            self.toast.update(dt)
            self.fx.update(dt)

            self.top().draw(self.screen)
            self.toast.draw(self.screen)
            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()


class BossChoiceScreen(Screen):
    def on_enter(self):
        cx = WIDTH // 2
        self.buttons = [
            Button((cx - 220, 380, 200, 60), "Challenge Boss", self._yes, size=20),
            Button((cx + 20, 380, 200, 60), "Explore Forest", self._no, size=20, base_color=(40, 40, 44)),
        ]

    def _yes(self):
        self.app.pop()
        self.app.start_boss_fight()

    def _no(self):
        self.app.pop()
        self.app._enter_death_forest_encounter()

    def draw(self, surf):
        draw_background(surf, self.t, "boss")
        draw_header(surf, "THE DEATH FOREST")
        for b in self.buttons:
            b.draw(surf)





if __name__ == "__main__":
    asyncio.run(App().run())
