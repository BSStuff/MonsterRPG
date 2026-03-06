"""MVP Monster bestiary — 12 monster species definitions across 2 areas."""

from elements_rpg.monsters.models import Element, MonsterSpecies, Rarity, StatBlock

# ============================================================================
# Area 1: Verdant Meadows (Starter, levels 1-15)
# ============================================================================

LEAFLET = MonsterSpecies(
    species_id="species_leaflet",
    name="Leaflet",
    types=(Element.GRASS, None),
    rarity=Rarity.COMMON,
    base_stats=StatBlock(
        hp=65,
        attack=30,
        defense=55,
        speed=25,
        magic_attack=35,
        magic_defense=45,
    ),
    passive_trait="Photosynthesis",
    passive_description="Slowly regenerates HP over time when in sunlight.",
    learnable_skill_ids=[
        "skill_vine_whip",
        "skill_root_bind",
        "skill_leaf_shield",
        "skill_nature_heal",
    ],
)

EMBER_PUP = MonsterSpecies(
    species_id="species_ember_pup",
    name="Ember Pup",
    types=(Element.FIRE, None),
    rarity=Rarity.COMMON,
    base_stats=StatBlock(
        hp=45,
        attack=60,
        defense=30,
        speed=50,
        magic_attack=40,
        magic_defense=30,
    ),
    passive_trait="Flame Body",
    passive_description="Contact attackers take minor fire damage.",
    learnable_skill_ids=[
        "skill_flame_bite",
        "skill_fire_blast",
        "skill_ember_shield",
        "skill_flame_dash",
    ],
)

BREEZE_SPRITE = MonsterSpecies(
    species_id="species_breeze_sprite",
    name="Breeze Sprite",
    types=(Element.WIND, Element.LIGHT),
    rarity=Rarity.UNCOMMON,
    base_stats=StatBlock(
        hp=40,
        attack=30,
        defense=35,
        speed=70,
        magic_attack=55,
        magic_defense=45,
    ),
    passive_trait="Tailwind",
    passive_description="Boosts the speed of all allies slightly during combat.",
    learnable_skill_ids=[
        "skill_gust_slash",
        "skill_tailwind_boost",
        "skill_sonic_screech",
        "skill_cyclone",
    ],
)

PEBBLE_CRAB = MonsterSpecies(
    species_id="species_pebble_crab",
    name="Pebble Crab",
    types=(Element.ROCK, Element.GROUND),
    rarity=Rarity.COMMON,
    base_stats=StatBlock(
        hp=55,
        attack=35,
        defense=70,
        speed=15,
        magic_attack=20,
        magic_defense=50,
    ),
    passive_trait="Hard Shell",
    passive_description="Reduces incoming physical damage by a small percentage.",
    learnable_skill_ids=[
        "skill_rock_slam",
        "skill_stone_wall",
        "skill_leaf_shield",
        "skill_fortify",
    ],
)

DEWDROP_SLIME = MonsterSpecies(
    species_id="species_dewdrop_slime",
    name="Dewdrop Slime",
    types=(Element.WATER, None),
    rarity=Rarity.COMMON,
    base_stats=StatBlock(
        hp=55,
        attack=30,
        defense=40,
        speed=35,
        magic_attack=45,
        magic_defense=40,
    ),
    passive_trait="Moisture",
    passive_description="Heals a small amount of HP each turn from ambient moisture.",
    learnable_skill_ids=[
        "skill_aqua_jet",
        "skill_healing_mist",
        "skill_bubble_armor",
        "skill_tidal_wave",
    ],
)

MEADOW_FOX = MonsterSpecies(
    species_id="species_meadow_fox",
    name="Meadow Fox",
    types=(Element.WIND, Element.ELECTRIC),
    rarity=Rarity.UNCOMMON,
    base_stats=StatBlock(
        hp=45,
        attack=55,
        defense=30,
        speed=70,
        magic_attack=40,
        magic_defense=35,
    ),
    passive_trait="Quick Feet",
    passive_description="Chance to dodge incoming attacks based on speed advantage.",
    learnable_skill_ids=[
        "skill_gust_slash",
        "skill_cyclone",
        "skill_flame_dash",
        "skill_sonic_screech",
    ],
)

# ============================================================================
# Area 2: Crystal Caverns (Mid, levels 15-30)
# ============================================================================

CRYSTAL_BAT = MonsterSpecies(
    species_id="species_crystal_bat",
    name="Crystal Bat",
    types=(Element.DARK, Element.WIND),
    rarity=Rarity.UNCOMMON,
    base_stats=StatBlock(
        hp=40,
        attack=55,
        defense=30,
        speed=75,
        magic_attack=45,
        magic_defense=35,
    ),
    passive_trait="Echolocation",
    passive_description="Increases accuracy of all attacks in dark environments.",
    learnable_skill_ids=[
        "skill_gust_slash",
        "skill_sonic_screech",
        "skill_cyclone",
        "skill_shadow_bolt",
    ],
)

MAGMA_WYRM = MonsterSpecies(
    species_id="species_magma_wyrm",
    name="Magma Wyrm",
    types=(Element.FIRE, Element.GROUND),
    rarity=Rarity.RARE,
    base_stats=StatBlock(
        hp=60,
        attack=75,
        defense=50,
        speed=35,
        magic_attack=70,
        magic_defense=40,
    ),
    passive_trait="Molten Core",
    passive_description="Attack power increases as HP decreases.",
    learnable_skill_ids=[
        "skill_fire_blast",
        "skill_molten_fury",
        "skill_heat_wave",
        "skill_flame_dash",
    ],
)

AQUA_SERPENT = MonsterSpecies(
    species_id="species_aqua_serpent",
    name="Aqua Serpent",
    types=(Element.WATER, Element.ICE),
    rarity=Rarity.UNCOMMON,
    base_stats=StatBlock(
        hp=50,
        attack=35,
        defense=40,
        speed=45,
        magic_attack=65,
        magic_defense=55,
    ),
    passive_trait="Slippery",
    passive_description="Chance to evade physical attacks by slipping away.",
    learnable_skill_ids=[
        "skill_aqua_jet",
        "skill_tidal_wave",
        "skill_hydro_cannon",
        "skill_healing_mist",
    ],
)

SHADOW_MOTH = MonsterSpecies(
    species_id="species_shadow_moth",
    name="Shadow Moth",
    types=(Element.DARK, None),
    rarity=Rarity.RARE,
    base_stats=StatBlock(
        hp=50,
        attack=35,
        defense=40,
        speed=55,
        magic_attack=70,
        magic_defense=55,
    ),
    passive_trait="Dust Cloud",
    passive_description="Attacks have a chance to reduce enemy accuracy.",
    learnable_skill_ids=[
        "skill_shadow_bolt",
        "skill_confuse_dust",
        "skill_life_drain",
        "skill_sonic_screech",
    ],
)

GEO_GOLEM = MonsterSpecies(
    species_id="species_geo_golem",
    name="Geo Golem",
    types=(Element.ROCK, Element.GROUND),
    rarity=Rarity.RARE,
    base_stats=StatBlock(
        hp=85,
        attack=50,
        defense=80,
        speed=15,
        magic_attack=30,
        magic_defense=60,
    ),
    passive_trait="Fortify",
    passive_description="Defense increases each turn the golem stands still.",
    learnable_skill_ids=[
        "skill_rock_slam",
        "skill_earthquake",
        "skill_stone_wall",
        "skill_fortify",
    ],
)

PRISM_FAIRY = MonsterSpecies(
    species_id="species_prism_fairy",
    name="Prism Fairy",
    types=(Element.LIGHT, None),
    rarity=Rarity.EPIC,
    base_stats=StatBlock(
        hp=50,
        attack=30,
        defense=40,
        speed=75,
        magic_attack=80,
        magic_defense=70,
    ),
    passive_trait="Prismatic Aura",
    passive_description="Allies near the fairy gain minor resistance to all elements.",
    learnable_skill_ids=[
        "skill_prismatic_beam",
        "skill_aura_pulse",
        "skill_healing_mist",
        "skill_life_drain",
    ],
)

# ============================================================================
# Lookup dictionaries
# ============================================================================

MVP_SPECIES: dict[str, MonsterSpecies] = {
    LEAFLET.species_id: LEAFLET,
    EMBER_PUP.species_id: EMBER_PUP,
    BREEZE_SPRITE.species_id: BREEZE_SPRITE,
    PEBBLE_CRAB.species_id: PEBBLE_CRAB,
    DEWDROP_SLIME.species_id: DEWDROP_SLIME,
    MEADOW_FOX.species_id: MEADOW_FOX,
    CRYSTAL_BAT.species_id: CRYSTAL_BAT,
    MAGMA_WYRM.species_id: MAGMA_WYRM,
    AQUA_SERPENT.species_id: AQUA_SERPENT,
    SHADOW_MOTH.species_id: SHADOW_MOTH,
    GEO_GOLEM.species_id: GEO_GOLEM,
    PRISM_FAIRY.species_id: PRISM_FAIRY,
}

VERDANT_MEADOWS_SPECIES: list[str] = [
    LEAFLET.species_id,
    EMBER_PUP.species_id,
    BREEZE_SPRITE.species_id,
    PEBBLE_CRAB.species_id,
    DEWDROP_SLIME.species_id,
    MEADOW_FOX.species_id,
]

CRYSTAL_CAVERNS_SPECIES: list[str] = [
    CRYSTAL_BAT.species_id,
    MAGMA_WYRM.species_id,
    AQUA_SERPENT.species_id,
    SHADOW_MOTH.species_id,
    GEO_GOLEM.species_id,
    PRISM_FAIRY.species_id,
]
