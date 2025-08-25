# utils/cooldown.py
import time

# structure: { user_id: { "rps": last_timestamp, "aviator": last_timestamp, ... } }
cooldowns = {}

COOLDOWN_SECONDS = 120  # 2 minutes per game by default

def is_on_cooldown(user_id: int, game: str):
    now = time.time()
    user_cd = cooldowns.get(user_id)
    if not user_cd:
        return False, 0
    last = user_cd.get(game)
    if not last:
        return False, 0
    elapsed = now - last
    if elapsed < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - elapsed)
        return True, remaining
    return False, 0

def set_cooldown(user_id: int, game: str):
    if user_id not in cooldowns:
        cooldowns[user_id] = {}
    cooldowns[user_id][game] = time.time()
