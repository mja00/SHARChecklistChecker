"""Canonical display names and per-level totals for 100% completion.

This is the **source of truth for display names** — the save's own name fields are
generic placeholders (early saves show ``Cardx``/``NULL``/``m0``), so they are never
shown to the user. Names are compiled from the Simpsons Wiki / SHAR community guides.

Edit this table to adjust totals or fix a name; everything downstream reads from here.

Confidence notes:
- Card, story-mission, and bonus-mission names: high confidence.
- Gag counts per level (15/11/11/15/6/11/15 = 84): the Level-5 count of 6 is unusually
  low and is the least-certain figure.
- Street-race, outfit, and vehicle per-item names are not reliably documented, so those
  categories are reported as counts only (no per-item names).
"""

from __future__ import annotations

# Per-level character/label, 0-indexed (index 0 == "Level 1").
LEVEL_LABELS = [
    "Level 1 - Homer",
    "Level 2 - Bart",
    "Level 3 - Lisa",
    "Level 4 - Marge",
    "Level 5 - Apu",
    "Level 6 - Bart (night)",
    "Level 7 - Homer (Halloween)",
]

# 7 story missions per level. The Level 1 tutorial ("The Cola Caper") is a prerequisite
# but is not one of the 7 counted story missions, so it is not listed here.
MISSION_NAMES = [
    [
        "S-M-R-T",
        "Petty Theft Homer",
        "Office Spaced",
        "Blind Big Brother",
        "Flowers by Irene",
        "Bonestorm Storm",
        "The Fat and Furious",
    ],
    [
        "Detention Deficit Disorder",
        "Weapons of Mass Delinquency",
        "Vox Nerduli",
        "Bart 'n' Frink",
        "Better Than Beef",
        "Monkey See, Monkey D'oh!",
        "Cell-Outs",
    ],
    [
        "Nerd Race Queen",
        "Clueless",
        "Bonfire of the Manatees",
        "Operation Hellfish",
        "Slithery Sleuthing",
        "Fishy Deals",
        "The Old Pirate and the Sea",
    ],
    [
        "For A Few Donuts More",
        "Redneck Roundup",
        "Ketchup Logic",
        "Return Of The Nearly Dead",
        "Wolves Stole My Pills!",
        "The Cola Wars",
        "From Outer Space",
    ],
    [
        "Incriminating Caffeine",
        "...and Baby Makes 8",
        "Eight is Too Much",
        "This Little Piggy",
        "Never Trust a Snake",
        "Kwik Cash",
        "Curious Curator",
    ],
    [
        "Going to the Lu'",
        "Getting Down with the Clown",
        "Lab Coat Caper",
        "Duff for Me, Duff for You",
        "Full Metal Jackass",
        "Set to Kill",
        "Kang and Kodos Strike Back",
    ],
    [
        "Rigor Motors",
        "Long Black Probes",
        "Pocket Protector",
        "There's Something About Monty",
        'Alien "Auto"topsy Part I',
        'Alien "Auto"topsy Part II',
        'Alien "Auto"topsy Part III',
    ],
]

BONUS_MISSION_NAMES = [
    "This Old Shanty",
    "Dial B for Blood",
    "Princi-Pal",
    "Beached Love",
    "Kinky Frinky",
    "Milking the Pigs",
    "Flaming Tires",
]

CARD_NAMES = [
    [
        "Home Made Football",
        "Crab Juice",
        "Insanity Pepper",
        "Spinemelter 2000",
        "Parchment",
        "Carbon Rod",
        "Mr. Sparkle Box",
    ],
    [
        "Head of Jebediah",
        "AM Radio Toy",
        "Bonestorm Game",
        "Big Butt Skinner",
        "Mr. Honeybunny",
        "Drivers License",
        "Pregnancy Test",
    ],
    [
        "Angel Skeleton",
        "Bart's Soul",
        "Lisa Lionheart",
        "Lisa's Valentine",
        "Lisa's Machine",
        "Evil Braces",
        "Soy Pop",
    ],
    [
        "Mr. Plow Jacket",
        "Burns Portrait",
        "Love Letter",
        '"Homer" Bowling Ball',
        "Red Blazer",
        "Boudoir Album",
        "Pepper Spray",
    ],
    [
        "Apu's T-Shirt",
        "Pin Pals Shirt",
        "Prop 24 Sign",
        "Baby Feeder",
        "Ganesh Costume",
        "Chutney Squishee",
        "Hot Dog",
    ],
    [
        "Radioactive Man #1",
        '"Bort" License Plate',
        "Bart T-Shirt",
        "Australia Boot",
        "Itchy and Scratchy Cel",
        "Gabbo Doll",
        "Bart's Flying Hamster Science Project",
    ],
    [
        "Soul Donut",
        "Krusty Doll",
        "Human Cookbook",
        "Time Travel Toaster",
        "Hell Toupee",
        "Monkey's Paw",
        '"Smarch" Calendar',
    ],
]

# Per-level counts for count-only categories.
GAGS_PER_LEVEL = [15, 11, 11, 15, 6, 11, 15]  # sums to 84
WASPS_PER_LEVEL = [20] * 7  # 140 total
OUTFITS_PER_LEVEL = [3] * 7  # 21 total

# Vehicles unlocked per level for completion = 3 purchasable + bonus-mission reward +
# street-race reward = 5 (35 total). This is the game's own QueryNumCarUnlocked metric,
# not the global CarInventory count. (Source: charactersheetmanager.cpp.)
CARS_PER_LEVEL = 5

# Fixed per-level counts for named categories.
STORY_MISSIONS_PER_LEVEL = 7  # 49 total (the L1 tutorial is excluded from this count)
STREET_RACES_PER_LEVEL = 3  # 21 total
CARDS_PER_LEVEL = 7  # 49 total

NUM_LEVELS = 7
