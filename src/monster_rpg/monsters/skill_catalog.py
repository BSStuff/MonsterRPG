"""MVP Skill catalog — predefined skills for the 12 monster bestiary."""

from monster_rpg.monsters.models import Element
from monster_rpg.skills.progression import Skill, SkillMilestone, SkillType

# ---------------------------------------------------------------------------
# Earth Skills
# ---------------------------------------------------------------------------

VINE_WHIP = Skill(
    skill_id="skill_vine_whip",
    name="Vine Whip",
    skill_type=SkillType.ATTACK,
    element=Element.EARTH,
    power=45,
    accuracy=95,
    cooldown=2.0,
    description="Strikes the enemy with a sharp vine.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Thorned Vine",
            description="Vine Whip gains 15% bonus damage.",
            bonus_type="damage",
            bonus_value=0.15,
        ),
    ],
)

ROOT_BIND = Skill(
    skill_id="skill_root_bind",
    name="Root Bind",
    skill_type=SkillType.SPECIAL,
    element=Element.EARTH,
    power=30,
    accuracy=85,
    cooldown=5.0,
    description="Entangles the target with roots, reducing their speed.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Deep Roots",
            description="Root Bind lasts 20% longer.",
            bonus_type="buff_duration",
            bonus_value=0.20,
        ),
    ],
)

LEAF_SHIELD = Skill(
    skill_id="skill_leaf_shield",
    name="Leaf Shield",
    skill_type=SkillType.DEFENSE,
    element=Element.EARTH,
    power=0,
    accuracy=100,
    cooldown=6.0,
    description="Creates a barrier of leaves that absorbs damage.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Hardened Leaves",
            description="Shield absorbs 15% more damage.",
            bonus_type="damage",
            bonus_value=0.15,
        ),
    ],
)

NATURE_HEAL = Skill(
    skill_id="skill_nature_heal",
    name="Nature Heal",
    skill_type=SkillType.SUPPORT,
    element=Element.EARTH,
    power=40,
    accuracy=100,
    cooldown=8.0,
    description="Draws on natural energy to restore HP to an ally.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Verdant Bloom",
            description="Healing power increased by 25%.",
            bonus_type="damage",
            bonus_value=0.25,
        ),
    ],
)

ROCK_SLAM = Skill(
    skill_id="skill_rock_slam",
    name="Rock Slam",
    skill_type=SkillType.ATTACK,
    element=Element.EARTH,
    power=60,
    accuracy=85,
    cooldown=3.5,
    description="Smashes the target with a heavy boulder.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Crushing Impact",
            description="Rock Slam gains 10% chance to stun.",
            bonus_type="proc_chance",
            bonus_value=0.10,
        ),
    ],
)

STONE_WALL = Skill(
    skill_id="skill_stone_wall",
    name="Stone Wall",
    skill_type=SkillType.DEFENSE,
    element=Element.EARTH,
    power=0,
    accuracy=100,
    cooldown=7.0,
    description="Raises a wall of stone to block incoming attacks.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Reinforced Wall",
            description="Cooldown reduced by 15%.",
            bonus_type="cooldown",
            bonus_value=0.15,
        ),
    ],
)

EARTHQUAKE = Skill(
    skill_id="skill_earthquake",
    name="Earthquake",
    skill_type=SkillType.ATTACK,
    element=Element.EARTH,
    power=80,
    accuracy=75,
    cooldown=6.0,
    description="Shakes the ground violently, damaging all enemies in the area.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Fissure",
            description="AoE radius increased by 20%.",
            bonus_type="aoe_size",
            bonus_value=0.20,
        ),
    ],
)

FORTIFY = Skill(
    skill_id="skill_fortify",
    name="Fortify",
    skill_type=SkillType.DEFENSE,
    element=Element.EARTH,
    power=0,
    accuracy=100,
    cooldown=10.0,
    description="Hardens the body to greatly increase defense for a short time.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Unbreakable",
            description="Buff duration increased by 30%.",
            bonus_type="buff_duration",
            bonus_value=0.30,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Fire Skills
# ---------------------------------------------------------------------------

FLAME_BITE = Skill(
    skill_id="skill_flame_bite",
    name="Flame Bite",
    skill_type=SkillType.ATTACK,
    element=Element.FIRE,
    power=50,
    accuracy=90,
    cooldown=2.0,
    description="Bites the target with fire-coated fangs.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Searing Fangs",
            description="10% chance to apply burn.",
            bonus_type="proc_chance",
            bonus_value=0.10,
        ),
    ],
)

FIRE_BLAST = Skill(
    skill_id="skill_fire_blast",
    name="Fire Blast",
    skill_type=SkillType.ATTACK,
    element=Element.FIRE,
    power=70,
    accuracy=80,
    cooldown=4.0,
    description="Launches a massive ball of fire at the enemy.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Inferno",
            description="Damage increased by 20%.",
            bonus_type="damage",
            bonus_value=0.20,
        ),
    ],
)

EMBER_SHIELD = Skill(
    skill_id="skill_ember_shield",
    name="Ember Shield",
    skill_type=SkillType.DEFENSE,
    element=Element.FIRE,
    power=0,
    accuracy=100,
    cooldown=6.0,
    description="Surrounds self with embers that damage attackers on contact.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Blazing Barrier",
            description="Contact damage increased by 15%.",
            bonus_type="damage",
            bonus_value=0.15,
        ),
    ],
)

HEAT_WAVE = Skill(
    skill_id="skill_heat_wave",
    name="Heat Wave",
    skill_type=SkillType.SPECIAL,
    element=Element.FIRE,
    power=55,
    accuracy=85,
    cooldown=5.0,
    description="Emits a scorching wave that reduces enemy defense.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Meltdown",
            description="Defense reduction increased by 20%.",
            bonus_type="buff_duration",
            bonus_value=0.20,
        ),
    ],
)

MOLTEN_FURY = Skill(
    skill_id="skill_molten_fury",
    name="Molten Fury",
    skill_type=SkillType.ATTACK,
    element=Element.FIRE,
    power=100,
    accuracy=70,
    cooldown=8.0,
    description="Unleashes a devastating eruption of molten energy.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Volcanic Wrath",
            description="AoE size increased by 25%.",
            bonus_type="aoe_size",
            bonus_value=0.25,
        ),
    ],
)

FLAME_DASH = Skill(
    skill_id="skill_flame_dash",
    name="Flame Dash",
    skill_type=SkillType.ATTACK,
    element=Element.FIRE,
    power=40,
    accuracy=95,
    cooldown=3.0,
    description="Dashes through the enemy wreathed in flame.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Afterburn",
            description="15% chance to leave a burn trail.",
            bonus_type="proc_chance",
            bonus_value=0.15,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Water Skills
# ---------------------------------------------------------------------------

AQUA_JET = Skill(
    skill_id="skill_aqua_jet",
    name="Aqua Jet",
    skill_type=SkillType.ATTACK,
    element=Element.WATER,
    power=50,
    accuracy=90,
    cooldown=2.5,
    description="Shoots a high-pressure jet of water at the enemy.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Pressurized Stream",
            description="Damage increased by 15%.",
            bonus_type="damage",
            bonus_value=0.15,
        ),
    ],
)

HEALING_MIST = Skill(
    skill_id="skill_healing_mist",
    name="Healing Mist",
    skill_type=SkillType.SUPPORT,
    element=Element.WATER,
    power=35,
    accuracy=100,
    cooldown=7.0,
    description="Sprays a soothing mist that heals nearby allies.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Restorative Rain",
            description="AoE healing radius increased by 20%.",
            bonus_type="aoe_size",
            bonus_value=0.20,
        ),
    ],
)

TIDAL_WAVE = Skill(
    skill_id="skill_tidal_wave",
    name="Tidal Wave",
    skill_type=SkillType.ATTACK,
    element=Element.WATER,
    power=75,
    accuracy=80,
    cooldown=5.0,
    description="Summons a massive wave that crashes into all enemies.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Tsunami",
            description="AoE size increased by 25%.",
            bonus_type="aoe_size",
            bonus_value=0.25,
        ),
    ],
)

BUBBLE_ARMOR = Skill(
    skill_id="skill_bubble_armor",
    name="Bubble Armor",
    skill_type=SkillType.DEFENSE,
    element=Element.WATER,
    power=0,
    accuracy=100,
    cooldown=6.0,
    description="Encases self in a bubble that absorbs damage.",
    milestones=[
        SkillMilestone(
            level_required=5,
            name="Reinforced Bubble",
            description="Absorption increased by 20%.",
            bonus_type="damage",
            bonus_value=0.20,
        ),
    ],
)

HYDRO_CANNON = Skill(
    skill_id="skill_hydro_cannon",
    name="Hydro Cannon",
    skill_type=SkillType.ATTACK,
    element=Element.WATER,
    power=90,
    accuracy=75,
    cooldown=7.0,
    description="Fires an enormous blast of water with tremendous force.",
    milestones=[
        SkillMilestone(
            level_required=10,
            name="Deluge",
            description="Damage increased by 20%.",
            bonus_type="damage",
            bonus_value=0.20,
        ),
    ],
)

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
# Neutral Skills
# ---------------------------------------------------------------------------

SHADOW_BOLT = Skill(
    skill_id="skill_shadow_bolt",
    name="Shadow Bolt",
    skill_type=SkillType.ATTACK,
    element=Element.NEUTRAL,
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
    element=Element.NEUTRAL,
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

PRISMATIC_BEAM = Skill(
    skill_id="skill_prismatic_beam",
    name="Prismatic Beam",
    skill_type=SkillType.ATTACK,
    element=Element.NEUTRAL,
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
    element=Element.NEUTRAL,
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
    element=Element.NEUTRAL,
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

# ---------------------------------------------------------------------------
# Catalog — all skills indexed by ID
# ---------------------------------------------------------------------------

MVP_SKILLS: dict[str, Skill] = {
    # Earth
    VINE_WHIP.skill_id: VINE_WHIP,
    ROOT_BIND.skill_id: ROOT_BIND,
    LEAF_SHIELD.skill_id: LEAF_SHIELD,
    NATURE_HEAL.skill_id: NATURE_HEAL,
    ROCK_SLAM.skill_id: ROCK_SLAM,
    STONE_WALL.skill_id: STONE_WALL,
    EARTHQUAKE.skill_id: EARTHQUAKE,
    FORTIFY.skill_id: FORTIFY,
    # Fire
    FLAME_BITE.skill_id: FLAME_BITE,
    FIRE_BLAST.skill_id: FIRE_BLAST,
    EMBER_SHIELD.skill_id: EMBER_SHIELD,
    HEAT_WAVE.skill_id: HEAT_WAVE,
    MOLTEN_FURY.skill_id: MOLTEN_FURY,
    FLAME_DASH.skill_id: FLAME_DASH,
    # Water
    AQUA_JET.skill_id: AQUA_JET,
    HEALING_MIST.skill_id: HEALING_MIST,
    TIDAL_WAVE.skill_id: TIDAL_WAVE,
    BUBBLE_ARMOR.skill_id: BUBBLE_ARMOR,
    HYDRO_CANNON.skill_id: HYDRO_CANNON,
    # Wind
    GUST_SLASH.skill_id: GUST_SLASH,
    TAILWIND_BOOST.skill_id: TAILWIND_BOOST,
    SONIC_SCREECH.skill_id: SONIC_SCREECH,
    CYCLONE.skill_id: CYCLONE,
    # Neutral
    SHADOW_BOLT.skill_id: SHADOW_BOLT,
    CONFUSE_DUST.skill_id: CONFUSE_DUST,
    PRISMATIC_BEAM.skill_id: PRISMATIC_BEAM,
    AURA_PULSE.skill_id: AURA_PULSE,
    LIFE_DRAIN.skill_id: LIFE_DRAIN,
}
