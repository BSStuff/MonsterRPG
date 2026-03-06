"""Extended skill catalog — Wind, Dark, and Light skills for the MVP bestiary."""

from elements_rpg.monsters.models import Element
from elements_rpg.skills.progression import Skill, SkillMilestone, SkillType

# ---------------------------------------------------------------------------
# Wind Skills
# ---------------------------------------------------------------------------

GUST_SLASH = Skill(
    skill_id="skill_gust_slash",
    name="Gust Slash",
    skill_type=SkillType.ATTACK,
    element=Element.WIND,
    power=45,
    accuracy=95,
    cooldown=1.5,
    description="Slices the enemy with a blade of wind.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Razor Wind",
            description="10% chance for a critical strike.",
            bonus_type="proc_chance",
            bonus_value=0.10,
        ),
    ],
)

TAILWIND_BOOST = Skill(
    skill_id="skill_tailwind_boost",
    name="Tailwind Boost",
    skill_type=SkillType.SUPPORT,
    element=Element.WIND,
    power=0,
    accuracy=100,
    cooldown=8.0,
    description="Summons a tailwind that increases all allies' speed.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Jet Stream",
            description="Speed buff increased by 20%.",
            bonus_type="buff_duration",
            bonus_value=0.20,
        ),
    ],
)

SONIC_SCREECH = Skill(
    skill_id="skill_sonic_screech",
    name="Sonic Screech",
    skill_type=SkillType.SPECIAL,
    element=Element.WIND,
    power=35,
    accuracy=90,
    cooldown=4.0,
    description="Emits a piercing screech that disorients the target.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Shatter Pitch",
            description="Confusion duration increased by 15%.",
            bonus_type="buff_duration",
            bonus_value=0.15,
        ),
    ],
)

CYCLONE = Skill(
    skill_id="skill_cyclone",
    name="Cyclone",
    skill_type=SkillType.ATTACK,
    element=Element.WIND,
    power=65,
    accuracy=85,
    cooldown=4.5,
    description="Creates a whirling cyclone that damages all nearby foes.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Tempest",
            description="AoE size increased by 20%.",
            bonus_type="aoe_size",
            bonus_value=0.20,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Dark Skills
# ---------------------------------------------------------------------------

SHADOW_BOLT = Skill(
    skill_id="skill_shadow_bolt",
    name="Shadow Bolt",
    skill_type=SkillType.ATTACK,
    element=Element.DARK,
    power=55,
    accuracy=90,
    cooldown=3.0,
    description="Launches a bolt of shadow energy at the target.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Dark Pulse",
            description="Damage increased by 15%.",
            bonus_type="damage",
            bonus_value=0.15,
        ),
    ],
)

CONFUSE_DUST = Skill(
    skill_id="skill_confuse_dust",
    name="Confuse Dust",
    skill_type=SkillType.SPECIAL,
    element=Element.DARK,
    power=25,
    accuracy=85,
    cooldown=5.0,
    description="Scatters dust that confuses and weakens the target.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Blinding Cloud",
            description="Confusion duration increased by 25%.",
            bonus_type="buff_duration",
            bonus_value=0.25,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Light Skills
# ---------------------------------------------------------------------------

PRISMATIC_BEAM = Skill(
    skill_id="skill_prismatic_beam",
    name="Prismatic Beam",
    skill_type=SkillType.ATTACK,
    element=Element.LIGHT,
    power=70,
    accuracy=80,
    cooldown=5.0,
    description="Fires a dazzling beam of prismatic light.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Rainbow Burst",
            description="20% chance to reduce target's magic defense.",
            bonus_type="proc_chance",
            bonus_value=0.20,
        ),
    ],
)

AURA_PULSE = Skill(
    skill_id="skill_aura_pulse",
    name="Aura Pulse",
    skill_type=SkillType.SUPPORT,
    element=Element.LIGHT,
    power=30,
    accuracy=100,
    cooldown=9.0,
    description="Emits a healing aura that restores HP to all allies.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Radiant Aura",
            description="Healing power increased by 25%.",
            bonus_type="damage",
            bonus_value=0.25,
        ),
    ],
)

LIFE_DRAIN = Skill(
    skill_id="skill_life_drain",
    name="Life Drain",
    skill_type=SkillType.SPECIAL,
    element=Element.DARK,
    power=45,
    accuracy=85,
    cooldown=6.0,
    description="Drains life force from the target to heal the user.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Soul Siphon",
            description="Drain efficiency increased by 20%.",
            bonus_type="damage",
            bonus_value=0.20,
        ),
    ],
)
