"""Configuration settings for the Monster RPG backend."""

# Team
MAX_TEAM_SIZE: int = 6
MAX_EQUIPPED_SKILLS: int = 4
MAX_MONSTER_LEVEL: int = 100

# Idle system
IDLE_EFFICIENCY_RATE: float = 0.85
OFFLINE_CAP_HOURS: int = 8

# Action queue
BASE_ACTION_QUEUE_SLOTS: int = 2

# Taming
TAMING_SOFT_PITY_THRESHOLD: int = 50
TAMING_PITY_BONUS_PER_ATTEMPT: float = 0.01
