import base64
import json
import random

# Inventory Capacity Limits
MAX_POTIONS = 5
MAX_BANDAGES = 5
MAX_ANTIDOTES = 3
MAX_SPEED_POTIONS = 3
MAX_DAMAGE_POTIONS = 3


def generate_save_code(data):
    json_str = json.dumps(data)
    encoded_bytes = base64.b64encode(json_str.encode("utf-8"))
    return encoded_bytes.decode("utf-8")


def load_from_save_code(code):
    try:
        decoded_bytes = base64.b64decode(code.strip().encode("utf-8"))
        json_str = decoded_bytes.decode("utf-8")
        return json.loads(json_str)
    except Exception:
        print("\n❌ Invalid or corrupted save password!")
        return None


def trigger_autosave(data_dict):
    """Generates and prints current player state & save password."""
    code = generate_save_code(data_dict)
    print("\n" + "💾" * 20)
    print(" [💾 AUTO-SAVED!] Current Save Code:")
    print(f" {code}")
    print("💾" * 20 + "\n")
    return code



def run_death_forest_encounter(encounter, player_hp, max_hp, gold, exp, inventory, damage, armor_reduction, poison_resistance, life_steal_resistance, active_quest, valoria_quests_completed):
    """Run a Death Forest encounter and return the updated player state."""
    stats = {
        "Death Crawler": (1000, 75, 106, 300, 240),
        "Necromancer": (1500, 88, 119, 500, 400),
        "Crypt Stalker": (1300, 69, 106, 450, 360),
        "Bone Golem": (2000, 113, 150, 900, 700),
        "Grave Warden": (2500, 100, 138, 1500, 1200),
    }
    enemy_hp, enemy_min_damage, enemy_max_damage, fixed_exp, fixed_gold = stats[encounter]
    enemy_max_hp = enemy_hp
    print(f"\n⚠️ DEATH FOREST ENCOUNTER! A {encounter} appeared!")

    bleed_turns = 0
    poison_turns = 0
    armor_broken_turns = 0
    curse_turns = 0
    stunned = False
    dark_heal_used = False
    damage_potion_timers = []

    # Crypt Stalker can strike before the first player action.
    if encounter == "Crypt Stalker" and random.random() < 0.35:
        first_strike = random.randint(69, 106)
        effective_armor = 0 if armor_broken_turns > 0 else armor_reduction
        first_strike = max(1, first_strike - effective_armor)
        player_hp -= first_strike
        print(f"🗡️ CRYPT STALKER used FIRST STRIKE! You took {first_strike} damage!")

    while enemy_hp > 0 and player_hp > 0:
        # Damage-over-time effects happen at the start of the player's turn.
        if poison_turns > 0:
            poison_dmg = 12
            player_hp -= poison_dmg
            poison_turns -= 1
            print(f"🟣 Venom burns through you! Took {poison_dmg} poison damage. ({poison_turns} turns left)")
        if bleed_turns > 0:
            bleed_dmg = 10
            player_hp -= bleed_dmg
            bleed_turns -= 1
            print(f"🩸 You are bleeding! Took {bleed_dmg} damage. ({bleed_turns} turns left)")
        if armor_broken_turns > 0:
            armor_broken_turns -= 1
            print(f"🛡️ Your armor is shattered! Defense is 0. ({armor_broken_turns} turns left)")
        if curse_turns > 0:
            curse_turns -= 1
            print(f"☠️ Curse weakens your attacks! ({curse_turns} turns left)")

        if player_hp <= 0:
            break

        print(f"\n--- ☠️ Death Forest Combat ({encounter}: {enemy_hp}/{enemy_max_hp} HP | You: {player_hp}/{max_hp} HP) ---")
        print("1. Attack")
        print("2. Defend (Blocks 100% damage, restores 10% HP, counter-attacks)")
        print("3. Run (20% chance to escape)")
        print("4. Items")
        fight_choice = input("Choose 1, 2, 3, or 4\n>")

        action_taken = False
        enemy_turn = True

        if stunned:
            print("💫 You are STUNNED and lose this turn!")
            stunned = False
            action_taken = True
        elif fight_choice == "1":
            try:
                atk_choice = input("\n1. Normal Attack\n2. Heavy Attack (75% damage bonus, 30% miss chance)\n> ")
            except EOFError:
                atk_choice = "1"
            if atk_choice not in {"1", "2"}:
                print("❌ Invalid attack choice.")
                continue
            multiplier = 1.0 if atk_choice == "1" else 1.75
            if curse_turns > 0:
                multiplier *= 0.85
            damage_multiplier = 2 ** len(damage_potion_timers)
            player_deal = int(max(1, random.randint(max(1, damage - 2), damage + 2) * multiplier * damage_multiplier))
            if atk_choice == "2" and random.random() < 0.30:
                print("💨 Your Heavy Attack MISSED!")
                player_deal = 0
            if player_deal > 0:
                enemy_hp -= player_deal
                print(f"⚔️ You dealt {player_deal} damage!")
            action_taken = True

        elif fight_choice == "2":
            heal_amount = int(max_hp * 0.10)
            player_hp = min(max_hp, player_hp + heal_amount)
            counter = max(1, int(damage * 0.50))
            if curse_turns > 0:
                counter = max(1, int(counter * 0.85))
            counter *= 2 ** len(damage_potion_timers)
            enemy_hp -= counter
            print(f"🛡️ PERFECT PARRY! Restored {heal_amount} HP and countered for {counter} damage!")
            action_taken = True

        elif fight_choice == "3":
            action_taken = True
            if random.random() < 0.20:
                print(f"🏃 You escaped from the {encounter}!")
                break
            print("❌ Escape failed!")

        elif fight_choice == "4":
            print("\n1. Health Potion")
            print("2. Bandage")
            print("3. Antidote")
            print("4. Damage Potion (drink 1-3; each stack lasts 3 turns)")
            print("5. Back")
            item_choice = input("Choose 1 to 5\n>")
            if item_choice == "1" and "Health potion" in inventory:
                inventory.remove("Health potion")
                heal_amount = int(max_hp * 0.20)
                player_hp = min(max_hp, player_hp + heal_amount)
                print(f"🧪 Restored {heal_amount} HP!")
                continue
            elif item_choice == "2" and "Bandage" in inventory:
                inventory.remove("Bandage")
                bleed_turns = 0
                print("🩹 Bleeding cured!")
                continue
            elif item_choice == "3" and "Antidote" in inventory:
                inventory.remove("Antidote")
                poison_turns = 0
                print("🧪 Poison cured!")
                continue
            elif item_choice == "4":
                available = min(3, inventory.count("Damage Potion"), 3 - len(damage_potion_timers))
                if available <= 0:
                    print("❌ You have no usable Damage Potions (or all 3 stacks are active).")
                    continue
                amount_raw = input(f"How many? (1-{available})\n>")
                try:
                    amount = int(amount_raw)
                except ValueError:
                    amount = 0
                if not 1 <= amount <= available:
                    print("❌ Invalid amount.")
                    continue
                for _ in range(amount):
                    inventory.remove("Damage Potion")
                    damage_potion_timers.append(3)
                print(f"💥 Drank {amount} Damage Potion stack(s)! Damage multiplier is now x{2 ** len(damage_potion_timers)}.")
                continue
            elif item_choice == "5":
                continue
            else:
                print("❌ You don't have that item.")
                continue
        else:
            print("❌ Invalid choice.")
            continue

        if not action_taken:
            continue

        # Each completed combat turn advances active Damage Potion stacks.
        if damage_potion_timers:
            damage_potion_timers = [t - 1 for t in damage_potion_timers if t - 1 > 0]
            if len(damage_potion_timers) < 3:
                print(f"💥 Damage Potion stacks remaining: {len(damage_potion_timers)} (x{2 ** len(damage_potion_timers)} damage)")

        if enemy_hp <= 0:
            gained_exp = fixed_exp
            gained_gold = fixed_gold
            exp += gained_exp
            gold += gained_gold
            print(f"\n🏆 You defeated the {encounter}! +{gained_exp} EXP, +{gained_gold} gold.")
            if encounter == "Crypt Stalker" and random.random() < 0.10 and inventory.count("Damage Potion") < MAX_DAMAGE_POTIONS:
                inventory.append("Damage Potion")
                print("💥 Rare drop: Damage Potion!")
            if active_quest and active_quest.get("target") == encounter:
                active_quest["progress"] += 1
                print(f"🎯 Bounty progress: {active_quest['progress']}/{active_quest['required']}")
                if active_quest["progress"] >= active_quest["required"]:
                    gold += active_quest["gold_reward"]
                    exp += active_quest["exp_reward"]
                    print(f"🎉 BOUNTY COMPLETE! +{active_quest['gold_reward']} gold, +{active_quest['exp_reward']} EXP!")
                    if active_quest.get("source") == "clark":
                        valoria_quests_completed += 1
                    active_quest = None
            break

        # Grave Warden's one-time heal triggers at <=40% HP.
        if encounter == "Grave Warden" and not dark_heal_used and enemy_hp <= enemy_max_hp * 0.40:
            heal = int(enemy_max_hp * 0.15)
            enemy_hp = min(enemy_max_hp, enemy_hp + heal)
            dark_heal_used = True
            print(f"🌑 GRAVE WARDEN used DARK HEAL! Restored {heal} HP!")

        if enemy_turn:
            enemy_deal = random.randint(enemy_min_damage, enemy_max_damage)
            effective_armor = 0 if armor_broken_turns > 0 else armor_reduction
            final_damage = max(1, enemy_deal - effective_armor)
            player_hp -= final_damage
            print(f"💀 {encounter} dealt {final_damage} damage to you!")

            if encounter == "Death Crawler":
                if random.random() < 0.20 and player_hp > 0:
                    extra = max(1, random.randint(75, 106) - effective_armor)
                    player_hp -= extra
                    print(f"🕷️ DOUBLE STRIKE! Death Crawler hit again for {extra} damage!")
                if random.random() < 0.85:
                    if random.random() >= poison_resistance / 100:
                        poison_turns = max(poison_turns, 3)
                        print("🧪 VENOM BITE! Poison applied: 12 damage for 3 turns.")
                    else:
                        print("🛡️ Poison resistance blocked Venom Bite's poison!")
                    bleed_turns = max(bleed_turns, 2)
                    print("🩸 VENOM BITE! Bleed applied: 10 damage for 2 turns.")
            elif encounter == "Necromancer":
                if random.random() < 0.18 and player_hp > 0:
                    minion = random.randint(20, 40)
                    minion = max(1, minion - effective_armor)
                    player_hp -= minion
                    print(f"💀 SKELETON SUMMON! A skeleton hit you for {minion} damage!")
                if random.random() < 0.12:
                    curse_turns = max(curse_turns, 2)
                    print("☠️ CURSE! Your damage is reduced by 15% for 2 turns.")
            elif encounter == "Crypt Stalker":
                if random.random() < 0.12:
                    stunned = True
                    print("💫 CRIPPLING BLOW! You are stunned for 1 turn!")
            elif encounter == "Bone Golem":
                if random.random() < 0.12:
                    armor_broken_turns = 3
                    print("🦴 CRUSHING SLAM! Your armor is reduced to 0 for 3 turns!")
            elif encounter == "Grave Warden":
                if random.random() < 0.18 and player_hp > 0:
                    minion = random.randint(25, 45)
                    minion = max(1, minion - effective_armor)
                    player_hp -= minion
                    print(f"🦴 BONE MINION SUMMON! The minion hit you for {minion} damage!")

        if player_hp <= 0:
            gold = max(0, int(gold * 0.10))
            exp = max(0, int(exp * 0.50))
            player_hp = max_hp
            print("\n☠️ YOU WERE DEFEATED IN THE DEATH FOREST!")
            print("💰 You lost 90% of your gold.")
            print("✨ You lost 50% of your EXP.")
            break

    return player_hp, gold, exp, inventory, active_quest, valoria_quests_completed

# LOGIN SYSTEM
print("==================================")
print("    WELCOME TO THE RPG v1.4!      ")
print("  (Update 1.4: The Death Forest)   ")
print("==================================\n")

is_admin = False
name = ""

while True:
    print("\n🔐 --- LOGIN MENU ---")
    print("1. New Account")
    print("2. Load Game")
    print("3. Exit")
    login_choice = input("Choose 1, 2, or 3\n>")
    
    if login_choice == "3":
        print("👋 Goodbye!")
        exit()
    
    elif login_choice == "1":
        # New Account
        name = input("\nEnter your username:\n>").strip()
        password = input("Enter your password:\n>").strip()
        
        # Check for admin account
        is_admin = (name.lower() == "debugger pro")
        
        if is_admin:
            print(f"\n✨ ADMIN MODE ACTIVATED! Welcome, {name}!")
        else:
            print(f"\n👋 Welcome, {name}!")
        
        player_hp = 25
        max_hp = 25
        gold = 0
        Level = 1
        damage = 5
        exp = 0
        exp_needed = 20
        inventory = []
        armor_reduction = 0
        active_quest = None
        story_lvl20_seen = False
        story_lvl50_seen = False
        poison_resistance = 0
        life_steal_resistance = 0
        valoria_unlocked = False
        valoria_quests_completed = 0
        visited_valoria = False
        
        print("\n" + "=" * 50)
        print("📜 --- THE TALE OF THE CORRUPTED ROOT ---")
        print("For decades, the Village of Oakhaven lived in peace under")
        print("the shadow of the Ancient Forest. But recently, a dark miasma")
        print("has crept out from the woods. Monsters grow aggressive, trees")
        print("twist into abominations, and the air tastes of venom.")
        print("\nElder Marcus appointed you as Oakhaven's newest Warden.")
        print("Your duty: Cleanse the woods, grow in strength, and uncover")
        print("the source of the Corruption before it swallows the village whole!")
        print("=" * 50 + "\n")
        input("Press ENTER to begin your journey...")
        break
    
    elif login_choice == "2":
        # Load Game
        code_input = input("\nEnter your save code:\n>")
        saved_data = load_from_save_code(code_input)
        
        if saved_data:
            name = saved_data.get("name", "Hero")
            player_hp = saved_data.get("player_hp", 25)
            max_hp = saved_data.get("max_hp", 25)
            gold = saved_data.get("gold", 0)
            Level = saved_data.get("Level", 1)
            damage = saved_data.get("damage", 5)
            exp = saved_data.get("exp", 0)
            exp_needed = saved_data.get("exp_needed", 20)
            inventory = saved_data.get("inventory", [])
            armor_reduction = saved_data.get("armor_reduction", 0)
            active_quest = saved_data.get("active_quest", None)
            story_lvl20_seen = saved_data.get("story_lvl20_seen", False)
            story_lvl50_seen = saved_data.get("story_lvl50_seen", False)
            poison_resistance = saved_data.get("poison_resistance", 0)
            life_steal_resistance = saved_data.get("life_steal_resistance", 0)
            valoria_unlocked = saved_data.get("valoria_unlocked", False)
            valoria_quests_completed = saved_data.get("valoria_quests_completed", 0)
            visited_valoria = saved_data.get("visited_valoria", False)
            
            # Check for admin account
            is_admin = (name.lower() == "debugger pro")
            
            if is_admin:
                print(f"\n✨ ADMIN MODE ACTIVATED! Welcome back, {name}!")
            else:
                print(f"\n🎉 Save loaded! Welcome back, {name}!")
            break
        else:
            print("\n❌ Invalid or corrupted save code. Please try again.")

print(f"\nAlright {name}, welcome to Oakhaven!")


def build_save_state():
    return {
        "name": name, "player_hp": player_hp, "max_hp": max_hp,
        "gold": gold, "Level": Level, "damage": damage,
        "exp": exp, "exp_needed": exp_needed, "inventory": inventory,
        "armor_reduction": armor_reduction, "active_quest": active_quest,
        "story_lvl20_seen": story_lvl20_seen, "story_lvl50_seen": story_lvl50_seen,
        "poison_resistance": poison_resistance,
        "life_steal_resistance": life_steal_resistance,
        "valoria_unlocked": valoria_unlocked,
        "valoria_quests_completed": valoria_quests_completed,
        "visited_valoria": visited_valoria
    }

pending_zone = None

while True:
    # Save state is built only when it is actually saved, so it is never stale.

    # Level 20 Story Cutscene Trigger
    if Level >= 20 and not story_lvl20_seen:
        story_lvl20_seen = True
        print("\n" + "🌲" * 25)
        print("📜 --- STORY CHAPTER 1: BEYOND THE TREE LINE ---")
        print(f"\nAs you return to the village, Elder Marcus approaches with a grim face.")
        print(f"Elder Marcus: '{name}, your strength has grown impressive, but I fear")
        print("the corruption has deepened. The Scouts report that the barriers at the")
        print("Edge of the Deep Forest have collapsed. Corrupted Treants and Venomous")
        print("Stalkers are spilling toward Oakhaven.'")
        print("\nElder Marcus hands you a sealed vial containing a purple liquid.")
        print("Elder Marcus: 'Take this Antidote. The beasts past the tree line carry lethal")
        print("venom. You must venture into the Deep Forest Edge and hold the line!'")
        print("🌲" * 25 + "\n")
        if inventory.count("Antidote") < MAX_ANTIDOTES:
            inventory.append("Antidote")
            print("🧪 Received [1x Free Antidote] from Elder Marcus!")
        else:
            gold += 200
            print("🧪 You already have the maximum number of Antidotes.")
            print("💰 Elder Marcus gives you 200 gold instead for your troubles.")
        input("\nPress ENTER to continue...")
        trigger_autosave(build_save_state())

    # Level 50 Story Cutscene Trigger
    if Level >= 50 and not story_lvl50_seen:
        story_lvl50_seen = True
        print("\n" + "🌑" * 25)
        print("📜 --- STORY CHAPTER 2: THE DARK FOREST ---")
        print(f"\nYou emerge from the Deep Forest, battered but victorious.")
        print(f"Elder Marcus greets you with urgency, his face pale as ash.")
        print(f"Elder Marcus: '{name}, the corruption spreads further than we feared!'")
        print("'Daylight itself fades beyond the Deep Forest. Scouts report that shadows")
        print("move with intent. The Dark Forest Ruins have awakened with creatures")
        print("we've never seen—Shadow Specters, Blighted Beasts, and armored undead")
        print("that drain the very life from those they touch.'")
        print("\nElder Marcus produces a huge amount of gold.")
        print("Elder Marcus: 'Here this is all the gold I claimed on my adventures, I hope you can use it well. Steel yourself, Warden. The rot has grown teeth and hunger.'")
        gold += 2000
        print("🌑" * 25 + "\n")
        print("📖 New Zone Unlocked: Dark Forest Ruins (Lv. 50-89)")
        input("\nPress ENTER to continue...")
        trigger_autosave(build_save_state())

    print(
        f"\nYou are Level {Level} ({exp}/{exp_needed} EXP), deal {damage} damage, "
        f"and have {player_hp}/{max_hp} HP with {gold} gold."
    )
    if active_quest:
        print(
            f"📜 Active Quest: Defeat {active_quest['required']} {active_quest['target']}s "
            f"({active_quest['progress']}/{active_quest['required']})"
        )

    if is_admin:
        print(f"\n{name} [👑 ADMIN], as you are at the village you have 7 options:")
        print("1. Venture out to train (Forests)")
        print("2. Go to the village shop")
        print("3. Check the Village Bounty Board")
        print("4. Go to the town gate")
        print("5. See inventory")
        print("6. 💾 Save Game (Get Save Password Code)")
        print("7. 🔧 Admin Testing Menu")
        print("8. Exit Game")
        choice = input("Choose from 1 to 8\n>")
    else:
        print(f"\n{name}, as you are at the village you have 6 options:")
        print("1. Venture out to train (Forests)")
        print("2. Go to the village shop")
        print("3. Check the Village Bounty Board")
        print("4. Go to the town gate")
        print("5. See inventory")
        print("6. 💾 Save Game (Get Save Password Code)")
        print("7. Exit Game")
        choice = input("Choose from 1 to 7\n>")

    if choice == "1" or pending_zone == "dark_forest":
        selected_zone = pending_zone if pending_zone else "forest"

        if Level >= 20 and pending_zone is None:
            print("\n🌲 Where would you like to venture?")
            print("1. Forest (Lv. 1-19)")
            print("2. Deep Forest Edge (Lv. 20-49)")
            zone_choice = input("Choose 1 or 2\n>")
            if zone_choice == "2":
                selected_zone = "deep_forest"
            elif zone_choice != "1":
                print("❌ Invalid zone choice.")
                continue

        if selected_zone == "forest":
            print("\n🌲 Welcome to the Forest!")
            if Level >= 16:
                Forest_spawn_rates = ["Hobgoblin Warlord", "Alpha Dire Wolf", "Bandit Chieftain", "Treasure"]
                weights = [25, 25, 25, 25]
            elif Level >= 6:
                Forest_spawn_rates = ["Goblin", "Bandit", "Wolf", "Bear", "Hobgoblin Warlord", "Alpha Dire Wolf", "Bandit Chieftain", "Treasure"]
                weights = [10, 15, 20, 15, 10, 5, 5, 10]
            else:
                Forest_spawn_rates = ["Goblin", "Bandit", "Wolf", "Bear", "Hobgoblin Warlord", "Alpha Dire Wolf", "Bandit Chieftain", "Treasure"]
                weights = [39, 30, 20, 3, 1, 1, 1, 5]
        elif selected_zone == "deep_forest":
            print("\n🌲 You step beyond the tree line into the dark Deep Forest Edge...")
            Forest_spawn_rates = ["Corrupted Treant", "Venomous Stalker", "Corrupted Drake", "Treasure"]
            weights = [40, 35, 20, 5]
        elif selected_zone == "dark_forest":
            if Level < 90:
                print("❌ The Death Forest is sealed. You must be Level 90+ to enter through Valoria's gates.")
                pending_zone = None
                continue
            print("\n☠️ You pass through Valoria's deepest gate into the DEATH FOREST...")
            print("💀 The trees are dead, the ground is covered in ancient bones, and something is watching you.")
            Forest_spawn_rates = ["Death Crawler", "Necromancer", "Crypt Stalker", "Bone Golem", "Grave Warden", "Treasure"]
            weights = [35, 25, 20, 10, 5, 5]

        encounter = random.choices(Forest_spawn_rates, weights=weights, k=1)[0]

        if selected_zone == "dark_forest":
            if encounter == "Treasure":
                gained_exp = random.randint(300, 700)
                gained_gold = random.randint(250, 600)
                exp += gained_exp
                gold += gained_gold
                print(f"\n💰 DEATH FOREST TREASURE! +{gained_gold} gold and +{gained_exp} EXP!")
                if inventory.count("Health potion") < MAX_POTIONS and random.random() < 0.45:
                    inventory.append("Health potion")
                    print("🧪 Found a Health Potion!")
                if inventory.count("Bandage") < MAX_BANDAGES and random.random() < 0.35:
                    inventory.append("Bandage")
                    print("🩹 Found a Bandage!")
                if inventory.count("Antidote") < MAX_ANTIDOTES and random.random() < 0.25:
                    inventory.append("Antidote")
                    print("🧪 Found an Antidote!")
                if inventory.count("Damage Potion") < MAX_DAMAGE_POTIONS and random.random() < 0.05:
                    inventory.append("Damage Potion")
                    print("💥 RARE DROP: Damage Potion!")
            else:
                (player_hp, gold, exp, inventory, active_quest, valoria_quests_completed) = run_death_forest_encounter(
                    encounter, player_hp, max_hp, gold, exp, inventory, damage, armor_reduction,
                    poison_resistance, life_steal_resistance, active_quest, valoria_quests_completed
                )

            while exp >= exp_needed:
                Level += 1
                exp -= exp_needed
                exp_needed = int(exp_needed * 1.5)
                print(f"\n🎉 LEVEL UP! You reached Level {Level}!")
                while True:
                    print("\nChoose 1 stat point to increase:")
                    print("1. +15 Max HP")
                    print("2. +3 Damage")
                    stat_choice = input("Choose 1 or 2\n>")
                    if stat_choice == "1":
                        max_hp += 15
                        print("Increased Max HP by 15!")
                        break
                    elif stat_choice == "2":
                        damage += 3
                        print("Increased Damage by 3!")
                        break
                    else:
                        print("Invalid choice, try again.")
                player_hp = max_hp

            pending_zone = None
            trigger_autosave(build_save_state())
            continue

        if encounter in [
            "Goblin", "Bandit", "Wolf", "Bear",
            "Hobgoblin Warlord", "Alpha Dire Wolf", "Bandit Chieftain",
            "Corrupted Treant", "Venomous Stalker", "Corrupted Drake",
            "Shadow Specter", "Blighted Beast", "Corrupted Knight"
        ]:
            if encounter == "Goblin":
                enemy_hp = 28; enemy_min_damage = 5; enemy_max_damage = 9
                gold_gainable = [10, 20]; exp_gainable = [15, 25]
            elif encounter == "Bandit":
                enemy_hp = 40; enemy_min_damage = 8; enemy_max_damage = 14
                gold_gainable = [20, 30]; exp_gainable = [25, 40]
            elif encounter == "Wolf":
                enemy_hp = 50; enemy_min_damage = 10; enemy_max_damage = 16
                gold_gainable = [30, 50]; exp_gainable = [35, 50]
            elif encounter == "Bear":
                enemy_hp = 90; enemy_min_damage = 14; enemy_max_damage = 22
                gold_gainable = [50, 70]; exp_gainable = [50, 75]
            elif encounter == "Hobgoblin Warlord":
                enemy_hp = 140; enemy_min_damage = 18; enemy_max_damage = 26
                gold_gainable = [40, 55]; exp_gainable = [45, 60]
            elif encounter == "Alpha Dire Wolf":
                enemy_hp = 175; enemy_min_damage = 22; enemy_max_damage = 30
                gold_gainable = [50, 65]; exp_gainable = [55, 70]
            elif encounter == "Bandit Chieftain":
                enemy_hp = 210; enemy_min_damage = 25; enemy_max_damage = 35
                gold_gainable = [60, 80]; exp_gainable = [65, 80]
            elif encounter == "Corrupted Treant":
                enemy_hp = 280; enemy_min_damage = 30; enemy_max_damage = 42
                gold_gainable = [60, 90]; exp_gainable = [70, 100]
            elif encounter == "Venomous Stalker":
                enemy_hp = 340; enemy_min_damage = 28; enemy_max_damage = 38
                gold_gainable = [70, 110]; exp_gainable = [80, 115]
            elif encounter == "Corrupted Drake":
                enemy_hp = 400; enemy_min_damage = 42; enemy_max_damage = 58
                gold_gainable = [120, 170]; exp_gainable = [130, 180]
            elif encounter == "Shadow Specter":
                enemy_hp = 600; enemy_min_damage = 60; enemy_max_damage = 75
                gold_gainable = [140, 200]; exp_gainable = [160, 220]
            elif encounter == "Blighted Beast":
                enemy_hp = 680; enemy_min_damage = 80; enemy_max_damage = 100
                gold_gainable = [160, 220]; exp_gainable = [180, 250]
            elif encounter == "Corrupted Knight":
                enemy_hp = 800; enemy_min_damage = 50; enemy_max_damage = 68
                gold_gainable = [180, 250]; exp_gainable = [210, 300]

            print(f"\n⚠️ ENCOUNTER! A wild {encounter} appeared!")
            bleed_turns = 0
            poison_turns = 0
            armor_broken_turns = 0
            defend_cooldown = 0
            feint_cooldown = 0
            feint_buff = False
            is_enraged = False
            enemy_dodge_turns = 0
            enemy_armor_broken_turns = 0
            enemy_poison_turns = 0
            speed_potion_active = False
            if "Speed Potion" in inventory:
                inventory.remove("Speed Potion")
                speed_potion_active = True
                print("⚡ Speed Potion activated! Enemy dodge is reduced by 30% for this battle.")
            enemy_max_hp_start = enemy_hp

            while enemy_hp > 0 and player_hp > 0:
                if enemy_poison_turns > 0:
                    enemy_poison_dmg = 12
                    enemy_hp = max(1, enemy_hp - enemy_poison_dmg)
                    enemy_poison_turns -= 1
                    print(f"🟣 The {encounter} is poisoned! Took {enemy_poison_dmg} damage! ({enemy_poison_turns} turns left)")
                if enemy_armor_broken_turns > 0:
                    enemy_armor_broken_turns -= 1
                    print(f"💎 {encounter}'s armor is weakened! ({enemy_armor_broken_turns} turns left)")

                if encounter in ["Hobgoblin Warlord", "Alpha Dire Wolf", "Bandit Chieftain"] and not is_enraged and enemy_hp <= (enemy_max_hp_start * 0.20):
                    is_enraged = True
                    print(f"\n🔥 THE {encounter} IS ENRAGED! Deals +5 bonus damage and takes reduced damage!")

                if bleed_turns > 0:
                    bleed_dmg = 8 if encounter == "Alpha Dire Wolf" else 4
                    player_hp -= bleed_dmg
                    bleed_turns -= 1
                    print(f"🩸 You are bleeding profusely! Took {bleed_dmg} damage! ({bleed_turns} turns left)")

                if poison_turns > 0:
                    poison_dmg = 12 if encounter == "Corrupted Drake" else 10
                    player_hp -= poison_dmg
                    poison_turns -= 1
                    print(f"🧪 Deadly Poison burns inside you! Took {poison_dmg} damage! ({poison_turns} turns left)")

                if player_hp <= 0:
                    print("\nYou succumbed to status effects! You woke up in the village with half your gold.")
                    gold = max(0, gold // 2)
                    player_hp = max_hp
                    break

                if armor_broken_turns > 0:
                    armor_broken_turns -= 1
                    print(f"🛡️ Your armor is cracked! Defense reduced to 0! ({armor_broken_turns} turns left)")

                defend_status = "READY" if defend_cooldown == 0 else f"ON COOLDOWN ({defend_cooldown} turns)"
                print(f"\n--- Combat ({encounter}: {enemy_hp}/{enemy_max_hp_start} HP | You: {player_hp}/{max_hp} HP) ---")
                print("1. Attack Options")
                print(f"2. Defend [{defend_status}] (Blocks 100% damage, restores 10% HP, counter-attacks)")
                print("3. Run (20% chance to escape)")
                print("4. Items (Potion / Bandage / Antidote)")
                fight_choice = input("Choose 1, 2, 3, or 4\n>")

                enemy_turn = True
                is_defending = False
                action_taken = False
                player_deal = 0

                # Enemy dodge is checked when YOU attack, not during the enemy's turn.
                enemy_dodge_chance = 0.0
                if encounter == "Shadow Specter":
                    enemy_dodge_chance = 0.175 if speed_potion_active else 0.25
                elif encounter == "Corrupted Knight":
                    enemy_dodge_chance = 0.14 if speed_potion_active else 0.20

                if fight_choice == "1":
                    feint_status = "READY" if feint_cooldown == 0 else f"ON COOLDOWN ({feint_cooldown} turns)"
                    print("\nSelect an Attack Type:")
                    print("1. Light Attack (Reliable, +15% Crit, reduces Defend Cooldown by 1)")
                    print("2. Heavy Attack (High damage, 50% miss chance unless Feinted)")
                    print("3. Quick Strike (Low damage, 50% chance to daze enemy)")
                    print(f"4. Feint & Strike [{feint_status}] (Light damage, +40% Heavy Attack accuracy next turn)")
                    print("5. Wild Swing (Extreme damage variance, 15% chance for 2.5x Super Crit)")
                    print("6. Back")
                    atk_choice = input("Choose 1 to 6\n>")

                    if atk_choice == "6":
                        continue
                    if atk_choice not in {"1", "2", "3", "4", "5"}:
                        print("Invalid attack choice.")
                        continue

                    # Dodge is an enemy defense against the player's attack.
                    if enemy_dodge_chance and random.random() < enemy_dodge_chance:
                        print(f"👻 The {encounter} dodged your attack!")
                        action_taken = True
                    elif atk_choice == "1":
                        is_crit = random.random() < 0.15
                        crit_mult = 1.5 if is_crit else 1.0
                        player_deal = int(random.randint(damage, damage + 2) * crit_mult)
                        if is_enraged:
                            player_deal = int(player_deal * 0.90)
                        if enemy_armor_broken_turns > 0:
                            player_deal = int(player_deal * 1.25)
                        enemy_hp -= player_deal
                        msg = (f"💥 CRITICAL HIT! Light Attack dealt {player_deal} damage!"
                               if is_crit else f"You landed a Light Attack dealing {player_deal} damage!")
                        print(msg)
                        action_taken = True

                    elif atk_choice == "2":
                        miss_chance = 0.30 if feint_buff else 0.80
                        if random.random() < miss_chance:
                            print("You swung wide with a Heavy Attack and MISSED!")
                        else:
                            if feint_buff:
                                print("🎯 Feint Buff consumed! High precision Heavy Attack landed!")
                                feint_buff = False
                            is_crit = random.random() < 0.10
                            raw_dmg = random.randint(int(damage * 1.5), max(int(damage * 1.5), int(damage * 1.75)))
                            player_deal = int(raw_dmg * (1.5 if is_crit else 1.0))
                            if is_enraged:
                                player_deal = int(player_deal * 0.90)
                            if enemy_armor_broken_turns > 0:
                                player_deal = int(player_deal * 1.25)
                            enemy_hp -= player_deal
                            if is_crit:
                                print(f"💥 CRITICAL HEAVY ATTACK! You dealt {player_deal} damage!")
                            else:
                                print(f"💥 HEAVY ATTACK! You dealt {player_deal} damage!")
                        action_taken = True

                    elif atk_choice == "3":
                        is_crit = random.random() < 0.10
                        crit_mult = 1.5 if is_crit else 1.0
                        low_roll = max(1, damage - 2)
                        player_deal = int(random.randint(low_roll, damage) * crit_mult)
                        if is_enraged:
                            player_deal = int(player_deal * 0.90)
                        if enemy_armor_broken_turns > 0:
                            player_deal = int(player_deal * 1.25)
                        enemy_hp -= player_deal
                        print(f"You struck with a Quick Strike dealing {player_deal} damage!")
                        if random.random() < 0.50 and enemy_hp > 0:
                            print(f"💫 The {encounter} was DAZED and loses its turn!")
                            enemy_turn = False
                        action_taken = True

                    elif atk_choice == "4":
                        if feint_cooldown > 0:
                            print(f"❌ Feint & Strike is on cooldown! ({feint_cooldown} turn(s) remaining)")
                            continue
                        player_deal = max(1, damage // 2)
                        if is_enraged:
                            player_deal = int(player_deal * 0.90)
                        if enemy_armor_broken_turns > 0:
                            player_deal = int(player_deal * 1.25)
                        enemy_hp -= player_deal
                        feint_buff = True
                        feint_cooldown = 4
                        print(f"🤺 You feinted the {encounter}, dealing {player_deal} damage! Your next Heavy Attack gets +40% accuracy!")
                        action_taken = True

                    elif atk_choice == "5":
                        is_super_crit = random.random() < 0.15
                        raw_dmg = random.randint(1, max(1, damage * 2))
                        player_deal = int(raw_dmg * (2.5 if is_super_crit else 1.0))
                        if is_enraged:
                            player_deal = int(player_deal * 0.90)
                        if enemy_armor_broken_turns > 0:
                            player_deal = int(player_deal * 1.25)
                        enemy_hp -= player_deal
                        if is_super_crit:
                            print(f"⚡ SUPER CRITICAL HIT! Wild Swing dealt {player_deal} MASSIVE damage!")
                        else:
                            print(f"🌀 Wild Swing dealt {player_deal} damage!")
                        action_taken = True

                    # Weapon special effects trigger only on successful attacks.
                    if action_taken and player_deal > 0:
                        if "Diamond Sword" in inventory and random.random() < 0.25:
                            enemy_armor_broken_turns = 3
                            print("💎 Diamond Sword triggered ARMOR BREAK! You deal +25% damage for 3 turns!")
                        elif "Mythril Sword" in inventory and random.random() < 0.25:
                            enemy_poison_turns = 3
                            print("🟣 Mythril Sword triggered POISON! The enemy is poisoned for 3 turns!")
                        elif "Absolute Adamantium Hellfire" in inventory and random.random() < 0.25:
                            steal = max(1, int(player_deal * 0.50))
                            old_hp = player_hp
                            player_hp = min(max_hp, player_hp + steal)
                            print(f"🔥 Adamantium Hellfire triggered LIFE STEAL! Restored {player_hp - old_hp} HP!")

                elif fight_choice == "2":
                    if defend_cooldown > 0:
                        print(f"❌ Defend is on cooldown! ({defend_cooldown} turn(s) remaining)")
                        continue
    
                    is_defending = True
                    defend_cooldown = 4
                    heal_amount = int(max_hp * 0.10)
                    player_hp = min(max_hp, player_hp + heal_amount)
                    counter_dmg = max(1, damage // 2)
                    enemy_hp -= counter_dmg
                    print(f"🛡️ PERFECT PARRY! Restored {heal_amount} HP and counter-struck for {counter_dmg} damage!")
                    action_taken = True

                elif fight_choice == "3":
                    action_taken = True
                    if random.random() < 0.20:
                        print(f"You successfully ran away from the {encounter}!")
                        break
                    else:
                        print("Escape failed!")

                elif fight_choice == "4":
                    print("\nUse an Item:")
                    print("1. Health Potion (Restores 20% Max HP)")
                    print("2. Bandage (Cures Bleeding)")
                    print("3. Antidote (Cures Poison)")
                    print("4. Back")
                    item_choice = input("Choose 1, 2, 3, or 4\n>")

                    if item_choice == "1":
                        if "Health potion" in inventory:
                            inventory.remove("Health potion")
                            heal_amount = int(max_hp * 0.20)
                            player_hp = min(max_hp, player_hp + heal_amount)
                            print(f"🧪 You drank a potion and restored {heal_amount} HP! ({player_hp}/{max_hp} HP)")
                            continue
                        else:
                            print("You don't have any health potions!")
                            continue
                    elif item_choice == "2":
                        if "Bandage" in inventory:
                            inventory.remove("Bandage")
                            bleed_turns = 0
                            print("🩹 You applied a bandage and stopped the bleeding!")
                            continue
                        else:
                            print("You don't have any bandages!")
                            continue
                    elif item_choice == "3":
                        if "Antidote" in inventory:
                            inventory.remove("Antidote")
                            poison_turns = 0
                            print("🧪 You drank an Antidote and cured the poison!")
                            continue
                        else:
                            print("You don't have any Antidotes!")
                            continue
                    else:
                        continue
                else:
                    print("Invalid choice.")
                    continue

                if action_taken:
                    if defend_cooldown > 0: defend_cooldown -= 1
                    if feint_cooldown > 0: feint_cooldown -= 1

                if enemy_hp <= 0:
                    gained_exp = random.randint(exp_gainable[0], exp_gainable[1])
                    gained_gold = random.randint(gold_gainable[0], gold_gainable[1])
                    exp += gained_exp
                    gold += gained_gold
                    print(f"\nYou defeated the {encounter}! Gained {gained_exp} EXP and {gained_gold} gold.")

                    if active_quest and active_quest["target"] == encounter:
                        active_quest["progress"] += 1
                        print(f"🎯 Quest Progress: {active_quest['progress']}/{active_quest['required']} defeated!")
                        if active_quest["progress"] >= active_quest["required"]:
                            print(f"🎉 QUEST COMPLETE! Claimed {active_quest['gold_reward']} gold and {active_quest['exp_reward']} EXP!")
                            gold += active_quest["gold_reward"]
                            exp += active_quest["exp_reward"]
                            if active_quest.get("source") == "clark":
                                valoria_quests_completed += 1
                                print(f"🏛️ Clark quest progress: {valoria_quests_completed}/3")
                            active_quest = None
                    break

                if enemy_turn:
                    if is_defending:
                        print(f"🛡️ You completely blocked the {encounter}'s attack! (0 damage taken)")
                    else:
                        enemy_deal = random.randint(enemy_min_damage, enemy_max_damage)
                        if is_enraged: enemy_deal += 5


                        if random.random() < 0.25:
                            if encounter == "Venomous Stalker":
                                if random.random() >= poison_resistance / 100:
                                    poison_turns = 4
                                    print("🐍 Venomous Stalker used VENOM STRIKE! Injected deadly poison!")
                                else:
                                    print("🛡️ Your poison resistance blocked VENOM STRIKE!")
                            elif encounter == "Corrupted Treant":
                                armor_broken_turns = 3
                                print("🪵 Corrupted Treant used ARMOR CRUSH! Shattered your defense!")
                            elif encounter == "Corrupted Drake":
                                if random.random() >= poison_resistance / 100:
                                    poison_turns = 3
                                    print("🐉 Corrupted Drake used CORRUPTED BREATH! Injected poison!")
                                else:
                                    print("🛡️ Your poison resistance blocked the Drake's poison!")
                                armor_broken_turns = 2
                                print("🐉 Corrupted Drake cracked your armor!")
                            elif encounter == "Blighted Beast":
                                life_steal_amount = int(enemy_deal * 0.5 * (1 - life_steal_resistance / 100))
                                enemy_hp += life_steal_amount
                                print(f"💀 Blighted Beast used LIFE DRAIN! Drained {life_steal_amount} life from you!")
                            elif encounter == "Corrupted Knight":
                                # Corrupted Knight does both dodge and lifesteal
                                dodge_chance = 0.20 if not speed_potion_active else 0.20 - 0.06  # 20% or 14% with Speed Potion
                                if random.random() < dodge_chance:
                                    print(f"🗡️ Corrupted Knight evaded your attack!")
                                    enemy_turn = False
                                    continue
                                # Otherwise, use lifesteal
                                life_steal_amount = int(enemy_deal * 0.45 * (1 - life_steal_resistance / 100))
                                enemy_hp += life_steal_amount
                                print(f"🗡️ Corrupted Knight used UNHOLY DRAIN! Drained {life_steal_amount} life essence!")
                            elif encounter in ["Wolf", "Alpha Dire Wolf"]:
                                bleed_turns = 3
                                print(f"🐺 The {encounter} used BITE & BLEED!")

                        effective_armor = 0 if armor_broken_turns > 0 else armor_reduction
                        final_damage = max(1, enemy_deal - effective_armor)
                        player_hp -= final_damage
                        print(f"The {encounter} dealt {final_damage} damage to you!")

                if player_hp <= 0:
                    print("\nYou were defeated! You woke up in the village with half your gold.")
                    gold = max(0, gold // 2)
                    player_hp = max_hp
                    break

        else:
            if Level > 20:
                gained_exp = random.randint(100, 500)
                gained_gold = random.randint(100, 200)
                exp += gained_exp
                gold += gained_gold
            elif Level > 10:
                gained_exp = random.randint(50, 250)
                gained_gold = random.randint(50, 100)
                exp += gained_exp
                gold += gained_gold
            elif Level > 5:
                gained_exp = random.randint(25, 125)
                gained_gold = random.randint(25, 50)
                exp += gained_exp
                gold += gained_gold
            else:
                gained_exp = random.randint(10, 75)
                gained_gold = random.randint(12, 25)
                exp += gained_exp
                gold += gained_gold
            
            print(f"\nYou found a Treasure Chest! Gained {gained_exp} EXP and {gained_gold} gold!")

        while exp >= exp_needed:
            Level += 1
            exp -= exp_needed
            exp_needed = int(exp_needed * 1.5)
            print(f"\n🎉 LEVEL UP! You reached Level {Level}!")

            while True:
                print("\nChoose 1 stat point to increase:")
                print("1. +15 Max HP")
                print("2. +3 Damage")
                stat_choice = input("Choose 1 or 2\n>")

                if stat_choice == "1":
                    max_hp += 15
                    print("Increased Max HP by 15!")
                    break
                elif stat_choice == "2":
                    damage += 3
                    print("Increased Damage by 3!")
                    break
                else:
                    print("Invalid choice, try again.")

            player_hp = max_hp

        # Clear a Dark Forest trip launched from Valoria.
        pending_zone = None

        # Auto-Save after returning from combat
        trigger_autosave(build_save_state())

    elif choice == "2":
        potion_heal = int(max_hp * 0.20)
        print("\n=== 🏪 OAKHAVEN VILLAGE SHOP ===")
        print("1. Weapons (Old Sword / Steel Longsword)")
        print("2. Armor (Leather Tunic / Iron Plate Armor)")
        print(f"3. Health Potion - 30 gold (+{potion_heal} HP) [Cap: {MAX_POTIONS}]")
        print(f"4. Bandage - 50 gold (Cures Bleed) [Cap: {MAX_BANDAGES}]")
        print(f"5. Antidote - 100 gold (Cures Poison) [Cap: {MAX_ANTIDOTES}]")
        print(f"6. Speed Potion - 500 gold (Reduces enemy dodge by 30%) [Cap: {MAX_SPEED_POTIONS}]")
        print("7. Back to village")
        shop_choice = input("Choose 1 to 7\n>")

        if shop_choice == "1":
            if "Steel Longsword" in inventory:
                print("⚔️ You already own the strongest sword in Oakhaven!")
            elif "Old sword" in inventory:
                print("\nUpgrade: Steel Longsword (+25 additional damage, +40 total)")
                print("Cost: 750 Gold")
                buy = input("Buy Steel Longsword upgrade? (y/n)\n>").lower()
                if buy == 'y':
                    if gold >= 750:
                        inventory.remove("Old sword")
                        inventory.append("Steel Longsword")
                        damage += 25
                        gold -= 750
                        print("⚔️ Upgraded to Steel Longsword! You now have +40 total weapon damage.")
                    else:
                        print("❌ You need 750 gold to upgrade to the Steel Longsword.")
            else:
                print("\nWeapon: Old Sword (+15 damage)")
                print("Cost: 250 Gold")
                buy = input("Buy Old Sword? (y/n)\n>").lower()
                if buy == 'y':
                    if gold >= 250:
                        gold -= 250
                        inventory.append("Old sword")
                        damage += 15
                        print("⚔️ Bought Old Sword (+5 damage)!")
                    else:
                        print("❌ You don't have enough gold! Old Sword costs 250 gold.")

        elif shop_choice == "2":
            if "Iron Plate Armor" in inventory:
                print("🛡️ You already own the strongest armor in Oakhaven!")
            elif "Leather Tunic" in inventory:
                print("\nUpgrade: Iron Plate Armor (Reduces enemy damage taken by 12)")
                print("Cost: 950 Gold")
                buy = input("Buy Iron Plate Armor upgrade? (y/n)\n>").lower()
                if buy == 'y':
                    if gold >= 950:
                        inventory.remove("Leather Tunic")
                        inventory.append("Iron Plate Armor")
                        armor_reduction = 12
                        gold -= 950
                        print("🛡️ Upgraded to Iron Plate Armor! Reduces incoming damage by 12!")
                    else:
                        print("❌ You need 950 gold to upgrade to Iron Plate Armor.")
            else:
                print("\nArmor: Leather Tunic (Reduces enemy damage taken by 3)")
                print("Cost: 300 Gold")
                buy = input("Buy Leather Tunic? (y/n)\n>").lower()
                if buy == 'y':
                    if gold >= 300:
                        gold -= 300
                        inventory.append("Leather Tunic")
                        armor_reduction = 5
                        print("🛡️ Bought Leather Tunic! Reduces incoming damage by 5!")
                    else:
                        print("❌ You don't have enough gold! Leather Tunic costs 300 gold.")

        elif shop_choice == "3":
            if inventory.count("Health potion") >= MAX_POTIONS:
                print(f"❌ Full! Max {MAX_POTIONS} Health Potions allowed.")
            elif gold >= 30:
                gold -= 30
                inventory.append("Health potion")
                print("🧪 Bought a Health Potion!")
            else:
                print("❌ Not enough gold! Health Potions cost 30 gold.")

        elif shop_choice == "4":
            if inventory.count("Bandage") >= MAX_BANDAGES:
                print(f"❌ Full! Max {MAX_BANDAGES} Bandages allowed.")
            elif gold >= 50:
                gold -= 50
                inventory.append("Bandage")
                print("🩹 Bought a Bandage!")
            else:
                print("❌ Not enough gold! Bandages cost 50 gold.")

        elif shop_choice == "5":
            if inventory.count("Antidote") >= MAX_ANTIDOTES:
                print(f"❌ Full! Max {MAX_ANTIDOTES} Antidotes allowed.")
            elif gold >= 100:
                gold -= 100
                inventory.append("Antidote")
                print("🧪 Bought an Antidote!")
            else:
                print("❌ Not enough gold! Antidotes cost 100 gold.")

        elif shop_choice == "6":
            if inventory.count("Speed Potion") >= MAX_SPEED_POTIONS:
                print(f"❌ Full! Max {MAX_SPEED_POTIONS} Speed Potions allowed.")
            elif gold >= 500:
                gold -= 500
                inventory.append("Speed Potion")
                print("⚡ Bought a Speed Potion! Reduces enemy dodge by 30% in the next quest.")
            else:
                print("❌ Not enough gold! Speed Potions cost 500 gold.")

        # Auto-Save after shopping
        save_state = {
            "name": name, "player_hp": player_hp, "max_hp": max_hp,
            "gold": gold, "Level": Level, "damage": damage,
            "exp": exp, "exp_needed": exp_needed, "inventory": inventory,
            "armor_reduction": armor_reduction, "active_quest": active_quest,
            "story_lvl20_seen": story_lvl20_seen, "story_lvl50_seen": story_lvl50_seen,
            "poison_resistance": poison_resistance, "life_steal_resistance": life_steal_resistance,
            "valoria_unlocked": valoria_unlocked, "valoria_quests_completed": valoria_quests_completed,
            "visited_valoria": visited_valoria
        }
        trigger_autosave(build_save_state())

    elif choice == "3":
        print("\n--- 📜 Village Notice Board ---")
        if active_quest:
            print(f"Active Quest: Defeat {active_quest['required']} {active_quest['target']}s.")
            print(f"Progress: {active_quest['progress']}/{active_quest['required']}")
            print("1. Abandon Quest")
            print("2. Back")
            q_opt = input("Choose 1 or 2\n>")
            if q_opt == "1":
                active_quest = None
                print("Quest abandoned.")
        else:
            print("Available Bounties:")
            print("1. Hunt 3 Goblins (45 Gold, 35 EXP)")
            print("2. Hunt 2 Wolves (70 Gold, 60 EXP)")
            print("3. Hunt 1 Hobgoblin Warlord (140 Gold, 150 EXP)")
            
            if Level >= 20:
                print("4. Hunt 2 Corrupted Treants (220 Gold, 280 EXP)")
                print("5. Hunt 2 Venomous Stalkers (260 Gold, 320 EXP)")
                print("6. Hunt 1 Corrupted Drake (380 Gold, 450 EXP)")
            
            if Level >= 50:
                print("7. Hunt 2 Shadow Specters (420 Gold, 520 EXP)")
                print("8. Hunt 2 Blighted Beasts (480 Gold, 620 EXP)")
                print("9. Hunt 1 Corrupted Knight (540 Gold, 750 EXP)")
                if Level >= 90:
                    print("10. Hunt 5 Death Crawlers (2400 Gold, 3000 EXP)")
                    print("11. Hunt 2 Necromancers (3200 Gold, 5000 EXP)")
                    print("12. Hunt 1 Bone Golem (7000 Gold, 9000 EXP)")
                    print("13. Hunt 1 Grave Warden (1200 Gold, 1500 EXP)")
                    print("14. Leave Board")
                else:
                    print("10. Leave Board")
            else:
                print("7. Leave Board")
            
            b_choice = input("Choose an option\n>")
            
            if b_choice == "1":
                active_quest = {"target": "Goblin", "required": 3, "progress": 0, "gold_reward": 45, "exp_reward": 35}
                print(" Accepted: Goblin Bounty!")
            elif b_choice == "2":
                active_quest = {"target": "Wolf", "required": 2, "progress": 0, "gold_reward": 70, "exp_reward": 60}
                print(" Accepted: Wolf Bounty!")
            elif b_choice == "3":
                active_quest = {"target": "Hobgoblin Warlord", "required": 1, "progress": 0, "gold_reward": 140, "exp_reward": 150}
                print(" Accepted: Hobgoblin Warlord Bounty!")
            elif b_choice == "4" and Level >= 20:
                active_quest = {"target": "Corrupted Treant", "required": 2, "progress": 0, "gold_reward": 220, "exp_reward": 280}
                print(" Accepted: Corrupted Treant Bounty!")
            elif b_choice == "5" and Level >= 20:
                active_quest = {"target": "Venomous Stalker", "required": 2, "progress": 0, "gold_reward": 260, "exp_reward": 320}
                print(" Accepted: Venomous Stalker Bounty!")
            elif b_choice == "6" and Level >= 20:
                active_quest = {"target": "Corrupted Drake", "required": 1, "progress": 0, "gold_reward": 380, "exp_reward": 450}
                print(" Accepted: Corrupted Drake Bounty!")
            elif b_choice == "7" and Level >= 50:
                active_quest = {"target": "Shadow Specter", "required": 2, "progress": 0, "gold_reward": 420, "exp_reward": 520}
                print(" Accepted: Shadow Specter Bounty!")
            elif b_choice == "8" and Level >= 50:
                active_quest = {"target": "Blighted Beast", "required": 2, "progress": 0, "gold_reward": 480, "exp_reward": 620}
                print(" Accepted: Blighted Beast Bounty!")
            elif b_choice == "9" and Level >= 50:
                active_quest = {"target": "Corrupted Knight", "required": 1, "progress": 0, "gold_reward": 540, "exp_reward": 750}
                print(" Accepted: Corrupted Knight Bounty!")
            elif b_choice == "10" and Level >= 90:
                active_quest = {"target": "Death Crawler", "required": 5, "progress": 0, "gold_reward": 2400, "exp_reward": 3000}
                print(" Accepted: Death Crawler Bounty!")
            elif b_choice == "11" and Level >= 90:
                active_quest = {"target": "Necromancer", "required": 2, "progress": 0, "gold_reward": 3200, "exp_reward": 5000}
                print(" Accepted: Necromancer Bounty!")
            elif b_choice == "12" and Level >= 90:
                active_quest = {"target": "Bone Golem", "required": 1, "progress": 0, "gold_reward": 7000, "exp_reward": 9000}
                print(" Accepted: Bone Golem Bounty!")
            elif b_choice == "13" and Level >= 90:
                active_quest = {"target": "Grave Warden", "required": 1, "progress": 0, "gold_reward": 1200, "exp_reward": 1500}
                print(" Accepted: Grave Warden Bounty!")

        # Auto-Save after Notice Board selection
        save_state = {
            "name": name, "player_hp": player_hp, "max_hp": max_hp,
            "gold": gold, "Level": Level, "damage": damage,
            "exp": exp, "exp_needed": exp_needed, "inventory": inventory,
            "armor_reduction": armor_reduction, "active_quest": active_quest,
            "story_lvl20_seen": story_lvl20_seen, "story_lvl50_seen": story_lvl50_seen,
            "poison_resistance": poison_resistance, "life_steal_resistance": life_steal_resistance,
            "valoria_unlocked": valoria_unlocked, "valoria_quests_completed": valoria_quests_completed,
            "visited_valoria": visited_valoria
        }
        trigger_autosave(build_save_state())

    elif choice == "4":
        print("\n🏰 --- THE TOWN GATES OF VALORIA ---")
        if Level >= 50:
            print("Guard Captain: 'Halt, Warden! The legends speak of your deeds!'")
            print("Guard Captain: 'Beyond these gates lies the Town of Valoria.'")
            print("Guard Captain: 'Retired Warden Clark await your arrival!'")
            print("\n1. Enter Town of Valoria")
            print("2. Back to village")
            valoria_choice = input("Choose 1 or 2\n>")
            
            if valoria_choice == "1":
                valoria_unlocked = True
                visited_valoria = True
                
                while True:
                    print("\n" + "🏛️" * 20)
                    print("🏛️ WELCOME TO THE TOWN OFVALORIA 🏛️")
                    print("🏛️" * 20)
                    print("1. Valoria Arms & Armor Shop")
                    print("2. Seek out Retired Warden Clark")
                    print("3. Adventure to the Death Forest (Lv. 90+)")
                    print("4. Return to Oakhaven")
                    valoria_action = input("Choose 1, 2, 3, or 4\n>")
                    
                    if valoria_action == "1":
                        # Valoria Shop with new weapons and armor
                        print("\n=== ⚔️ VALORIA ARMS & ARMOR SHOP ===")
                        print("WEAPONS:")
                        print("1. Diamond Sword - 5000 gold (+50 damage, Armor Break)")
                        print("2. Mythril Sword - 15000 gold (+150 damage, Poison)")
                        print("3. Absolute Adamantium Hellfire - 50000 gold (+300 damage, Life Steal)")
                        print("\nARMOR:")
                        print("4. Diamond Armor - 7500 gold (+50 damage reduction)")
                        print("5. Mythrillic Armor - 20000 gold (+100 damage reduction, 25% Poison Resistance)")
                        print("6. Adamantium Hellfire - 75000 gold (+200 damage reduction, 50% Life Steal Resistance)")
                        print("7. Damage Potion - 800 gold (max 3; stacks up to x8 damage for 3 turns)")
                        print("8. Back to Valoria")
                        shop_choice = input("Choose 1 to 8\n>")
                        
                        if shop_choice == "1":  # Diamond Sword
                            if "Mythril Sword" in inventory or "Absolute Adamantium Hellfire" in inventory:
                                print("⚔️ You already own a superior sword!")
                            elif "Diamond Sword" in inventory:
                                print("⚔️ You already own the Diamond Sword!")
                            elif "Steel Longsword" in inventory or "Old sword" in inventory:
                                print("\nWeapon Upgrade: Diamond Sword (+50 damage, Armor Break)")
                                print("Cost: 5000 Gold")
                                buy = input("Buy Diamond Sword? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 5000:
                                        if "Old sword" in inventory:
                                            inventory.remove("Old sword")
                                        elif "Steel Longsword" in inventory:
                                            inventory.remove("Steel Longsword")
                                        inventory.append("Diamond Sword")
                                        damage += 50
                                        gold -= 5000
                                        print("⚔️ Acquired Diamond Sword! Damage +50!")
                                    else:
                                        print("❌ You need 5000 gold for the Diamond Sword.")
                            else:
                                print("\nWeapon: Diamond Sword (+50 damage, Armor Break)")
                                print("Cost: 5000 Gold")
                                buy = input("Buy Diamond Sword? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 5000:
                                        inventory.append("Diamond Sword")
                                        damage += 50
                                        gold -= 5000
                                        print("⚔️ Bought Diamond Sword! Damage +50!")
                                    else:
                                        print("❌ You need 5000 gold for the Diamond Sword.")
                        
                        elif shop_choice == "2":  # Mythril Sword
                            if "Absolute Adamantium Hellfire" in inventory:
                                print("⚔️ You already own the ultimate sword!")
                            elif "Mythril Sword" in inventory:
                                print("⚔️ You already own the Mythril Sword!")
                            elif "Diamond Sword" in inventory or "Steel Longsword" in inventory or "Old sword" in inventory:
                                print("\nWeapon Upgrade: Mythril Sword (+150 damage, Poison)")
                                print("Cost: 15000 Gold")
                                buy = input("Buy Mythril Sword? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 15000:
                                        for sword in ["Old sword", "Steel Longsword", "Diamond Sword"]:
                                            if sword in inventory:
                                                inventory.remove(sword)
                                        inventory.append("Mythril Sword")
                                        damage += 150
                                        gold -= 15000
                                        print("⚔️ Acquired Mythril Sword! Damage +150!")
                                    else:
                                        print("❌ You need 15000 gold for the Mythril Sword.")
                            else:
                                print("\nWeapon: Mythril Sword (+150 damage, Poison)")
                                print("Cost: 15000 Gold")
                                buy = input("Buy Mythril Sword? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 15000:
                                        inventory.append("Mythril Sword")
                                        damage += 150
                                        gold -= 15000
                                        print("⚔️ Bought Mythril Sword! Damage +150!")
                                    else:
                                        print("❌ You need 15000 gold for the Mythril Sword.")
                        
                        elif shop_choice == "3":  # Absolute Adamantium Hellfire
                            if "Absolute Adamantium Hellfire" in inventory:
                                print("⚔️ You wield the ultimate weapon!")
                            else:
                                print("\nWeapon: Absolute Adamantium Hellfire (+300 damage, Life Steal)")
                                print("Cost: 50000 Gold")
                                buy = input("Buy this item? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 50000:
                                        for sword in ["Old sword", "Steel Longsword", "Diamond Sword", "Mythril Sword"]:
                                            if sword in inventory:
                                                inventory.remove(sword)
                                        inventory.append("Absolute Adamantium Hellfire")
                                        damage += 300
                                        gold -= 50000
                                        print("⚡ Acquired Absolute Adamantium Hellfire! You now wield true power!")
                                    else:
                                        print(f"❌ You need 50000 gold. You have: {gold}")
                        
                        elif shop_choice == "4":  # Diamond Armor
                            if "Mythrillic Armor" in inventory or "Adamantium Hellfire" in inventory:
                                print("🛡️ You already own superior armor!")
                            elif "Diamond Armor" in inventory:
                                print("🛡️ You already own the Diamond Armor!")
                            elif "Leather Tunic" in inventory or "Iron Plate Armor" in inventory:
                                print("\nArmor Upgrade: Diamond Armor (+50 damage reduction, Armor Break)")
                                print("Cost: 7500 Gold")
                                buy = input("Buy Diamond Armor? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 7500:
                                        if "Leather Tunic" in inventory:
                                            inventory.remove("Leather Tunic")
                                        elif "Iron Plate Armor" in inventory:
                                            inventory.remove("Iron Plate Armor")
                                        inventory.append("Diamond Armor")
                                        armor_reduction = 50
                                        gold -= 7500
                                        print("🛡️ Acquired Diamond Armor! Defense +50!")
                                    else:
                                        print("❌ You need 7500 gold for Diamond Armor.")
                            else:
                                print("\nArmor: Diamond Armor (+50 damage reduction)")
                                print("Cost: 7500 Gold")
                                buy = input("Buy Diamond Armor? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 7500:
                                        inventory.append("Diamond Armor")
                                        armor_reduction = 50
                                        gold -= 7500
                                        print("🛡️ Bought Diamond Armor! Defense +50!")
                                    else:
                                        print("❌ You need 7500 gold for Diamond Armor.")
                        
                        elif shop_choice == "5":  # Mythrillic Armor
                            if "Adamantium Hellfire" in inventory:
                                print("🛡️ You already own the ultimate armor!")
                            elif "Mythrillic Armor" in inventory:
                                print("🛡️ You already own Mythrillic Armor!")
                            else:
                                print("\nArmor: Mythrillic Armor (+100 damage reduction, 25% Poison Resistance)")
                                print("Cost: 20000 Gold")
                                buy = input("Buy Mythrillic Armor? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 20000:
                                        for armor in ["Leather Tunic", "Iron Plate Armor", "Diamond Armor"]:
                                            if armor in inventory:
                                                inventory.remove(armor)
                                        inventory.append("Mythrillic Armor")
                                        armor_reduction = 100
                                        poison_resistance = 25
                                        gold -= 20000
                                        print("🛡️ Acquired Mythrillic Armor! Defense +100, Poison Resistance +25%!")
                                    else:
                                        print("❌ You need 20000 gold for Mythrillic Armor.")
                        
                        elif shop_choice == "6":  # Adamantium Hellfire Armor
                            if "Adamantium Hellfire" in inventory:
                                print("🛡️ You wield the ultimate defense!")
                            else:
                                print("\nArmor: Adamantium Hellfire (+200 damage reduction, 50% Life Steal Resistance)")
                                print("Cost: 75000 Gold")
                                buy = input("Buy this item? (y/n)\n>").lower()
                                if buy == 'y':
                                    if gold >= 75000:
                                        for armor in ["Leather Tunic", "Iron Plate Armor", "Diamond Armor", "Mythrillic Armor"]:
                                            if armor in inventory:
                                                inventory.remove(armor)
                                        inventory.append("Adamantium Hellfire")
                                        armor_reduction = 200
                                        life_steal_resistance = 50
                                        gold -= 75000
                                        print("⚡ Acquired Adamantium Hellfire Armor! Defense +200, Life Steal Resistance +50%!")
                                    else:
                                        print(f"❌ You need 75000 gold. You have: {gold}")
                    
                        elif shop_choice == "7":  # Damage Potion
                            current = inventory.count("Damage Potion")
                            print(f"\n💥 Damage Potion: 800 Gold | Owned: {current}/{MAX_DAMAGE_POTIONS}")
                            if current >= MAX_DAMAGE_POTIONS:
                                print("❌ You already have the maximum 3 Damage Potions.")
                            else:
                                buy = input("Buy Damage Potion? (y/n)\n>").lower()
                                if buy == "y":
                                    if gold >= 800:
                                        inventory.append("Damage Potion")
                                        gold -= 800
                                        print("💥 Bought 1 Damage Potion!")
                                    else:
                                        print("❌ You need 800 gold.")

                    elif valoria_action == "2":
                        # Retired Warden Clark NPC
                        print("\n" + "👴" * 20)
                        print("You find the Retired Warden Clark in his chamber.")
                        print("Clark: 'Ah, {}, I've been expecting you.'".format(name))
                        print("Clark: 'Your deeds in the Dark Forest have restored hope to our kingdom.'")
                        print("Clark: 'I've prepared bounties for you. Complete them all, and I shall grant you")
                        print("a reward worthy of a true hero of Valoria.'")
                        print("👴" * 20)
                        print("\n1. View Clark's Bounties")
                        print("2. Back")
                        clark_choice = input("Choose 1 or 2\n>")
                        
                        if clark_choice == "1":
                            print("\n📜 --- CLARK'S BOUNTIES ---")
                            if valoria_quests_completed == 3:
                                print("🎉 All 3 Clark quests have been completed!")
                                print("1. Claim Final Reward")
                                print("2. Back")
                                reward_choice = input("Choose 1 or 2\n>")
                                if reward_choice == "1":
                                    if "Diamond Sword" in inventory and "Diamond Armor" in inventory:
                                        gold += 5000
                                        print("✨ You already own the Diamond Set. Received 5000 Gold instead!")
                                    else:
                                        if "Diamond Sword" not in inventory:
                                            inventory.append("Diamond Sword")
                                            damage += 50
                                        if "Diamond Armor" not in inventory:
                                            inventory.append("Diamond Armor")
                                            armor_reduction = 50
                                        gold += 3500
                                        print("✨ Received: 3500 Gold + Diamond Set!")
                                    valoria_quests_completed = 4  # Final reward claimed; prevents duplicate claims.
                            elif valoria_quests_completed > 3:
                                print("✅ Clark's final reward has already been claimed.")
                            elif active_quest:
                                print(f"⚔️ You already have a quest: Defeat {active_quest['required']} {active_quest['target']}s.")
                                print(f"Progress: {active_quest['progress']}/{active_quest['required']}")
                            else:
                                clark_quests = [
                                    ("1", "Shadow Specter", 3, 500, 800),
                                    ("2", "Blighted Beast", 3, 600, 900),
                                    ("3", "Corrupted Knight", 2, 700, 1000),
                                ]
                                print("Choose a bounty:")
                                for number, target, required, reward_gold, reward_exp in clark_quests:
                                    print(f"{number}. Hunt {required} {target}s - {reward_gold} Gold, {reward_exp} EXP")
                                print("4. Back")
                                bounty_choice = input("Choose 1 to 4\n>")
                                selected = next((q for q in clark_quests if q[0] == bounty_choice), None)
                                if selected:
                                    _, target, required, reward_gold, reward_exp = selected
                                    active_quest = {
                                        "target": target, "required": required, "progress": 0,
                                        "gold_reward": reward_gold, "exp_reward": reward_exp,
                                        "source": "clark"
                                    }
                                    print(f"🏛️ Accepted Clark's bounty: defeat {required} {target}s!")
                                elif bounty_choice != "4":
                                    print("❌ Invalid bounty choice.")

                    elif valoria_action == "3":
                        if Level >= 90:
                            print("\n☠️ --- DEATH FOREST ---")
                            print("Beyond this gate lies Valoria's deadliest territory.")
                            print("Enemies: Death Crawlers, Necromancers, Crypt Stalkers, Bone Golems, and Grave Wardens.")
                            print("☠️ Defeat here costs 90% of your gold and 50% of your EXP.")
                            input("\nPress ENTER to enter the Death Forest...")
                            pending_zone = "dark_forest"
                            break
                        else:
                            print("You need to be at least Level 90 to enter the Death Forest.")

        else:
            print("Guard Captain: 'Halt! The road to Valoria is blocked due to the monster surge.'")
            print("Guard Captain: 'Only Wardens who have proven themselves in the Deep Forest (Lv. 50)")
            print("may pass through these gates.'")
            print(f" (Your Level: {Level}/50)")

    elif choice == "5":
        print(f"\n🎒 Inventory ({len(inventory)} total items):")
        print(f"- Health Potions: {inventory.count('Health potion')}/{MAX_POTIONS}")
        print(f"- Bandages: {inventory.count('Bandage')}/{MAX_BANDAGES}")
        print(f"- Antidotes: {inventory.count('Antidote')}/{MAX_ANTIDOTES}")
        print(f"- Speed Potions: {inventory.count('Speed Potion')}/{MAX_SPEED_POTIONS}")
        print(f"- Damage Potions: {inventory.count('Damage Potion')}/{MAX_DAMAGE_POTIONS}")
        other_items = [i for i in inventory if i not in ["Health potion", "Bandage", "Antidote", "Speed Potion", "Damage Potion"]]
        if other_items:
            print(f"- Equipment / Key Items: {', '.join(other_items)}")

    elif choice == "6":
        current_data = {
            "name": name, "player_hp": player_hp, "max_hp": max_hp,
            "gold": gold, "Level": Level, "damage": damage,
            "exp": exp, "exp_needed": exp_needed, "inventory": inventory,
            "armor_reduction": armor_reduction, "active_quest": active_quest,
            "story_lvl20_seen": story_lvl20_seen, "story_lvl50_seen": story_lvl50_seen,
            "poison_resistance": poison_resistance, "life_steal_resistance": life_steal_resistance,
            "valoria_unlocked": valoria_unlocked, "valoria_quests_completed": valoria_quests_completed,
            "visited_valoria": visited_valoria
        }
        print("\n🔑 YOUR SAVE CODE:")
        print(generate_save_code(current_data))

    elif choice == "7" and not is_admin:
        print("👋 Thanks for playing The RPG!")
        break

    elif choice == "8" and is_admin:
        print("👋 Thanks for playing The RPG!")
        break

    elif choice == "7" and is_admin:
        print("\n🔧 --- ADMIN TESTING MENU ---")
        print("1. Max Out Stats")
        print("2. Get All Items")
        print("3. Jump to Level 50")
        print("4. Jump to Level 89")
        print("5. Unlock All Zones")
        print("6. Add 99999 Gold")
        print("7. Reset Game Progress")
        print("8. Back")
        admin_choice = input("Choose 1 to 8\n>")
        
        if admin_choice == "1":
            # Max Out Stats
            max_hp = 500
            player_hp = 500
            damage = 300
            gold += 50000
            Level = 100
            print("✨ Stats maxed out! You are now a super warrior!")
        
        elif admin_choice == "2":
            # Get All Items
            for _ in range(MAX_POTIONS):
                if inventory.count("Health potion") < MAX_POTIONS:
                    inventory.append("Health potion")
            for _ in range(MAX_BANDAGES):
                if inventory.count("Bandage") < MAX_BANDAGES:
                    inventory.append("Bandage")
            for _ in range(MAX_ANTIDOTES):
                if inventory.count("Antidote") < MAX_ANTIDOTES:
                    inventory.append("Antidote")
            for _ in range(MAX_SPEED_POTIONS):
                if inventory.count("Speed Potion") < MAX_SPEED_POTIONS:
                    inventory.append("Speed Potion")
            for _ in range(MAX_DAMAGE_POTIONS):
                if inventory.count("Damage Potion") < MAX_DAMAGE_POTIONS:
                    inventory.append("Damage Potion")
            if "Absolute Adamantium Hellfire" not in inventory:
                inventory.append("Absolute Adamantium Hellfire")
                damage += 300
            if "Adamantium Hellfire" not in inventory:
                inventory.append("Adamantium Hellfire")
                armor_reduction = 200
                life_steal_resistance = 50
            print("✨ All items acquired!")
        
        elif admin_choice == "3":
            # Jump to Level 50
            Level = 50
            story_lvl20_seen = True
            story_lvl50_seen = True
            valoria_unlocked = True
            print("✨ Jumped to Level 50! Dark Forest unlocked!")
        
        elif admin_choice == "4":
            # Jump to Level 90
            Level = 90
            story_lvl20_seen = True
            story_lvl50_seen = True
            valoria_unlocked = True
            visited_valoria = True
            valoria_quests_completed = 3
            print("✨ Jumped to Level 90! Death Forest unlocked!")
        
        elif admin_choice == "5":
            # Unlock All Zones
            story_lvl20_seen = True
            story_lvl50_seen = True
            valoria_unlocked = True
            visited_valoria = True
            if Level < 50:
                Level = 50
            print("✨ All zones unlocked!")
        
        elif admin_choice == "6":
            # Add Gold
            gold += 99999
            print("✨ Added 99999 Gold! Total Gold: {}".format(gold))
        
        elif admin_choice == "7":
            # Reset Progress
            player_hp = 25
            max_hp = 25
            gold = 0
            Level = 1
            damage = 5
            exp = 0
            exp_needed = 20
            inventory = []
            armor_reduction = 0
            active_quest = None
            story_lvl20_seen = False
            story_lvl50_seen = False
            poison_resistance = 0
            life_steal_resistance = 0
            valoria_unlocked = False
            valoria_quests_completed = 0
            visited_valoria = False
            print("✨ Game progress reset! You are back at the beginning.")
