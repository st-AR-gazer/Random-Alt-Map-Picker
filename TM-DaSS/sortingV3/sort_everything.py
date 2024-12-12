import json
import re
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from uids import (
    DISCOVERY_CAMPAIGNS,
    OFFICIAL_NADEO_AUTHOR_AND_SUBMITTOR_UIDS,
    special_uids,
    all_TOTD_map_names
)

INPUT_FILE = 'map_data.json'
OUTPUT_FILE = 'parsed_map_data.json'
LOG_FILE = 'unmatched_maps.log'
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

OFFICIAL_NADEO_TAG = "official nadeo map"

logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z',
    level=logging.DEBUG # set to "WARNING" when done with debugging...
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', '%Y-%m-%dT%H:%M:%S%z')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

VALID_SEASONS = ["winter", "spring", "summer", "fall", "training"]
SEASON_REGEX = '|'.join(VALID_SEASONS)

SANITIZE_PATTERN = re.compile(
    r'\$([0-9a-fA-F]{1,3}|[iIoOnNmMwWsSzZtTgG<>]|[lLhHpP](\[[^\]]+\])?)'
)

def sanitize_name(name: str) -> str:
    return SANITIZE_PATTERN.sub('', name).strip()

def validate_year(year: int) -> int:
    if year < 100:
        if 20 <= year <= 26:
            return 2000 + year
        else:
            logger.warning(f"Year {year} out of allowed range for short year (20-26).")
            return None
    else:
        if 2020 <= year <= 2026:
            return year
        else:
            logger.warning(f"Year {year} out of allowed range (2020-2026).")
            return None

def validate_mapnumber(map_nums: list) -> list:
    valid = []
    for num in map_nums:
        if 1 <= num <= 25:
            valid.append(num)
        else:
            logger.warning(f"Map number {num} out of allowed range (1-25).")
    return valid

# ------------------------------------------------------------
# REGEX PATTERNS (defined here for centralized attribute assignment)
# ------------------------------------------------------------

# for totd names
escaped_totd_names = [re.escape(name) for name in all_TOTD_map_names]
totd_pattern_group = "(?:" + "|".join(escaped_totd_names) + ")"


# ################ Altered Surface ################ #

    # --------- Dirt ---------- #
# Pattern seasonal: "Dirty <season> <year> - <mapnumber>"
dirt_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Dirty)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Dirty Training - <mapnumber>"
dirt_training_pattern_2 = re.compile(
    rf"^(?P<alteration>Dirty)\s+(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # --------- fast-magnet ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> FastMagnet"
fastmagnet_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>FastMagnet)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> FastMagnet"
fastmagnet_training_pattern_2 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>FastMagnet)$",
    re.IGNORECASE)

    # --------- Flooded ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Flooded"
flooded_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Flooded)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> - Flooded"
flooded_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Flooded)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> Flooded"
flooded_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>Flooded)$",
    re.IGNORECASE)

    # --------- Grass ---------- #
# Pattern seasonal: "Grassy <season> <year> - <mapnumber>"
grass_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Grassy)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern Training: "Grassy Training - <mapnumber>"
grass_training_pattern_2 = re.compile(
    rf"^(?P<alteration>Grassy)\s+(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # --------- Ice ---------- #
# Pattern seasonal: "Icy <season> <year> - <mapnumber>"
ice_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Icy)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Icy Training - <mapnumber>"
ice_training_pattern_1 = re.compile(
    rf"^(?P<alteration>Icy)\s+(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # --------- Magnet ---------- #
# Pattern season: "<season> <year> - <mapnumber> Magnet"
magnet_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Magnet)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Magnet"
magnet_training_pattern_2 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Magnet)$",
    re.IGNORECASE)

    # --------- Mixed ---------- #
# Pattern seasonal: "Mixed <season> <year> - <mapnumber>"
mixed_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Mixed)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Mixed Training - <mapnumber>"
mixed_training_pattern_1 = re.compile(
    rf"^(?P<alteration>Mixed)\s+(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # --------- Penalty ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Penalty"
penalty_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Penalty)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Penalty"
penalty_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Penalty)$",
    re.IGNORECASE)

    # --------- Plastic ---------- #
# Pattern seasonal: "Plastic <season> <year> - <mapnumber>"
plastic_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Plastic)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Plastic Training - <mapnumber>"
plastic_training_pattern_1 = re.compile(
    rf"^(?P<alteration>Plastic)\s+(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # --------- Road ---------- #
# Pattern seasonal: "Roady <season> <year> - <mapnumber>"
road_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Roady)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> Road - <mapnumber>"
road_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<alteration>Road)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Roady Training - <mapnumber>"
road_training_pattern_1 = re.compile(
    rf"^(?P<alteration>Roady)\s+(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # --------- Wood ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Wood"
wood_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Wood)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Wood"
wood_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Wood)$",
    re.IGNORECASE)
# Pattern spring2020: "Wood <spring2020><mapnumber>"
wood_spring2020_pattern_1 = re.compile(
    r"^(?P<alteration>Wood)\s+(?P<code>[STst][0-1]\d)$",
    re.IGNORECASE)

####################################################################################################################################################

    # --------- Bobsleigh ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (bobsleigh)"
bobsleigh_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>bobsleigh)\)$",
    re.IGNORECASE)

    # --------- Pipe ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (Pipe)"
pipe_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Pipe)\)$",
    re.IGNORECASE)

    # --------- Sausage ---------- #
# Pattern seasonal: "Saussage <season> <year> - <mapnumber>"
sausage_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Sausage)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Sausage"
sausage_training_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Sausage)$",
    re.IGNORECASE)

    # --------- Slot Track ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Slot Track"
slottrack_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Slot Track)$",
    re.IGNORECASE)

    # --------- Surfaceless ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Surfaceless"
surfaceless_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Surfaceless)$",
    re.IGNORECASE)

    # --------- Underwater ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (Underwater)"
underwater_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Underwater)\)$",
    re.IGNORECASE)


# ################ Altered Effects ################ #

    # -------- Antibooster ---------- #
# Pattern1: "<season> <year> - <mapnumber> AntiBoosters"
antibooster_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>AntiBoosters)$",
    re.IGNORECASE)

    # -------- Boosterless ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (Boosterless)"
boosterless_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Boosterless)\)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> Boosterless"
boosterless_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>Boosterless)$",
    re.IGNORECASE)

    # -------- Broken ---------- #
# Pattern1: "<season> <year> - <mapnumber> Broken"
broken_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Broken)$",
    re.IGNORECASE)

    # -------- Cleaned ---------- #
# Pattern1: "<season> <year> - <mapnumber> Cleaned"
cleaned_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Cleaned)$",
    re.IGNORECASE)

    # -------- Cruise Control ---------- #
# Pattern1: "<season> <year> - <mapnumber> Cruise Control"
cruisecontrol_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Cruise Control)$",
    re.IGNORECASE)

    # -------- Cruise Effects ---------- #
# Pattern1: "<season> <year> - <mapnumber> Cruise Effects"
cruiseeffects_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Cruise Effects)$",
    re.IGNORECASE)
# Pattern2: "Training - <mapnumber> Cruise Effects"
cruiseeffects_training_pattern_2 = re.compile(
    rf"^<season>{SEASON_REGEX}\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Cruise Effects)$",
    re.IGNORECASE)

    # -------- Fast ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Fast)"
fast_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Fast)\)$",
    re.IGNORECASE)

    # -------- Fragile ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Fragile)"
fragile_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Fragile)\)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> Fragile"
fragile_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Fragile)$",
    re.IGNORECASE)

    # -------- Full Fragile ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Full Fragile)"
fullfragile_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Full Fragile)\)$",
    re.IGNORECASE)

    # -------- FreeWheel ---------- #
# Pattern1: "<season> <year> - <mapnumber> FreeWheel"
freewheel_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>FreeWheel)$",
    re.IGNORECASE)

    # -------- Glider ---------- #
# Pattern1: "<season> <year> - <mapnumber> - Glider"
glider_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Glider)$",
    re.IGNORECASE)

    # -------- No Brakes ---------- #
# Pattern1: "No Brakes - <season> <year> - <mapnumber>"
nobrakes_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>No Brakes)\s*-\s*(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> NoBrakes"
nobrakes_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>NoBrakes)$",
    re.IGNORECASE)

    # -------- No Effects ---------- #
# Pattern1: "<season> <year> Effectless - <mapnumber>"
noeffects_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<alteration>Effectless)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- No Grip ---------- #
# Pattern1: "<season> <year> No Grip - <mapnumber>"
nogrip_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<alteration>No Grip)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> - No Grip"
nogrip_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>No Grip)$",
    re.IGNORECASE)

    # -------- No Steering ---------- #
# Pattern seasonal: "<season> <year> No Steering - <mapnumber>"
nosteering_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<alteration>No Steering)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> No Steering"
nosteering_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>No Steering)$",
    re.IGNORECASE)

    # -------- Random Dankness ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> - Random Dankness"
randomdankness_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Random Dankness)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Random Dankness"
randomdankness_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Random Dankness)$",
    re.IGNORECASE)

    # -------- Random Effects ---------- #
# Pattern1: "<season> <year> - <mapnumber> - Random Effects"
randomeffects_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Random Effects)$",
    re.IGNORECASE)

    # -------- Reactor ---------- #
# Pattern1: "<season> <year> - <mapnumber> Reactor"
reactor_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Reactor)$",
    re.IGNORECASE)

    # -------- Reactor Down ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Reactor Down)"
reactordown_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Reactor Down)\)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> Reactordown"
reactordown_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Reactordown)$",
    re.IGNORECASE)

    # -------- Red Effects ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Red Effects"
redeffects_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Red Effects)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Red Effects"
redeffects_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Red Effects)$",
    re.IGNORECASE)

    # -------- RNG Boosters ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> RNG Booster"
rngboosters_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>RNG Booster)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020season><mapnumber> RNG Booster"
rngboosters_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>RNG Booster)$",
    re.IGNORECASE)

    # -------- Slowmo ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> slowmo"
slowmo_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>slowmo)$",
    re.IGNORECASE)
# Pattern training: "<season> <year> - <mapnumber> slow mo"
slowmo_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>slow mo)$",
    re.IGNORECASE)

    # -------- Wet Wheels ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Wet-Wheels)"
wetwheels_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Wet-Wheels)\)$",
    re.IGNORECASE)

    # -------- Worn Tires ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Worn Tires)"
worntires_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Worn Tires)\)$",
    re.IGNORECASE)


# ################ Altered Finish Location ################ #

    # -------- 1Back/1Forwards ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (1-back)"
oneback_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>1-back)\)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> - one back"
oneback_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>one back)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> - 1-back"
oneback_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>1-back)$",
    re.IGNORECASE)
# Pattern training: "Training 1-forward - <mapnumber>"
oneforward_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<alteration>1-forward)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> 1-forward"
oneforward_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>1-forward)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (1-Forward)"
oneforward_totd_pattern_1 = re.compile(
    rf"^(?P<name>{totd_pattern_group})\s+\((?P<alteration>1-Forward)\)$",
    re.IGNORECASE)

    # -------- 1 Down ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (1-DOWN)"
onedown_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>1-DOWN)\)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> (1-DOWN)"
onedown_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>1-DOWN)\)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> (1-DOWN)"
onedown_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+\((?P<alteration>1-DOWN)\)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (1-Down)"
onedown_totd_pattern_1 = re.compile(
    rf"^(?P<name>{totd_pattern_group})\s+\((?P<alteration>1-DOWN)\)$",
    re.IGNORECASE)

    # -------- 1 Left/1 Right ---------- #
# Pattern1: "<season> <year> - <mapnumber> 1 Left"
oneleft_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>1 Left)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> 1 Right"
oneright_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>1 Right)$",
    re.IGNORECASE)

    # -------- 1 Up ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (1-UP)"
oneup_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>1-UP)\)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> - 1UP"
oneup_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>1UP)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> (1-UP)"
oneup_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+\((?P<alteration>1-UP)\)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (1-up)"
oneup_totd_pattern_1 = re.compile(
    rf"^(?P<name>{totd_pattern_group})\s+\((?P<alteration>1-up)\)$",
    re.IGNORECASE)

    # -------- 2 Up ---------- #
# Pattern1: "<season> <year> - <mapnumber> (2-UP)"
twoup_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>2-UP)\)$",
    re.IGNORECASE)

    # -------- Better Reverse ---------- #
# Pattern1: "<season> <year> - <mapnumber> (BeVerse)"
betterreverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>BeVerse)\)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> - Better Reverse"
betterreverse_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Better Reverse)$",
    re.IGNORECASE)
# Pattern3: "<season> <year> - <mapnumber> - Reverse Magna"
betterreverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Reverse Magna)$",
    re.IGNORECASE)

    # -------- CP1 is End ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> CP1 Ends"
cp1isend_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>CP1 Ends)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> CP1 is End"
cp1isend_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>CP1 is End)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> CP1 is End"
cp1isend_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>CP1 is End)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> CP1 is End"
cp1isend_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>CP1 is End)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (CP1-End)"
cp1isend_totd_pattern_1 = re.compile(
    rf"^(?P<name>{totd_pattern_group})\s+\((?P<alteration>CP1-End)\)$",
    re.IGNORECASE)

    # -------- Floor Fin ---------- #
# Pattern1: "<season> <year> - <mapnumber> Floor-fin"
floorfin_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Floor-fin)$",
    re.IGNORECASE)

    # -------- Ground Clippers ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Ground Clippers)"
groundclippers_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Ground Clippers)\)$",
    re.IGNORECASE)

    # -------- Inclined ---------- #
# Pattern1: "<season> <year> - <mapnumber> Inclined"
inclined_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Inclined)$",
    re.IGNORECASE)

    # -------- Manslaughter ---------- #
# Pattern1: "<season> <year> - <mapnumber> Manslaughter"
manslaughter_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Manslaughter)$",
    re.IGNORECASE)

    # -------- No Gear 5 ---------- #
# Pattern1: "<season> <year> - <mapnumber> No Gear 5"
nogear5_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>No Gear 5)$",
    re.IGNORECASE)

    # -------- Podium ---------- #
# Pattern1: "<season> <year> - <mapnumber> - Podium"
podium_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Podium)$",
    re.IGNORECASE)

    # -------- Puzzle ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (Puzzle)"
puzzle_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Puzzle)\)$",
    re.IGNORECASE)
# Pattern training: "Training Puzzle - <mapnumber>"
puzzle_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s+(?P<alteration>Puzzle)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Reverse ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> - Reverse"
reverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Reverse)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> - Reverse"
reverse_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Reverse)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> - Reverse"
reverse_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+-\s+(?P<alteration>Reverse)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (Reverse)"
reverse_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>Reverse)\)$",
    re.IGNORECASE)

    # -------- Roofing ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Roofing)"
roofing_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Roofing)\)$",
    re.IGNORECASE)

    # --------- SHORT ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> | Short"
short_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s*\|\s*(?P<alteration>Short)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> Short"
short_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Short)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> shorts"
short_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>shorts)$",
    re.IGNORECASE)
short_seasonal_pattern_4 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<alteration>Short)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Short"
short_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Short)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> Short"
short_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>Short)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> Short - <mapnumber>"


    # --------- Sky is the Finish ---------- #
# Pattern2: "<season> <year> - <mapnumber> Sky Finish"
skyfinish_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Sky Finish)$",
    re.IGNORECASE)
# Pattern3: "<season> <year> - <mapnumber> (SITF)"
skyfinish_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>SITF)\)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> - Sky is the Finish"
skyfinish_seasonal_pattern_4 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Sky is the Finish)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> Sky Finish"
skyfinish_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>Sky Finish)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (SITF)"
skyfinish_totd_pattern_5 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>SITF)\)$",
    re.IGNORECASE)

    # --------- There&Back/Boomerang ---------- #
# Pattern1: "<season> <year> - There&Back <mapnumber>"
thereandback_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<alteration>There&Back)\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> Boomerang"
thereandback_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Boomerang)$",
    re.IGNORECASE)

    # --------- YEP Tree Puzzle ---------- #
# Pattern1: "<season> <year> - <mapnumber> YEP TREE PUZZLE"
yeptreepuzzle_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>YEP TREE PUZZLE)$",
    re.IGNORECASE)


# ################ Altered Enviroments ################ #

    # -------- [Stadium] ---------- #
# Pattern1: "<season> <year> - <mapnumber> [Stadium]"
stadium_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Stadium\])$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> - CarSport"
stadium_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>CarSport)$",
    re.IGNORECASE)
# Pattern3: "<special_map_name> - CarSport"
#stadium_seasonal_pattern_3 = re.compile(
#    rf"^(?P<special_map_name>.*?)\s+-\s+(?P<alteration>CarSport)$",
#    re.IGNORECASE
#)

    # -------- [Stadium] To The Top ---------- #
# Pattern1: "<season> <year> - <mapnumber> Stadium To The Top"
stadiumtothetop_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Stadium To The Top)$",
    re.IGNORECASE)

    # -------- [Stadium] Wet Wood ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Wet Wood Stadium Car)"
stadiumwetwood_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Wet Wood Stadium Car)\)$",
    re.IGNORECASE)

    # -------- [Snow] ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> [Snow]"
snow_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Snow\])$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> - CarSnow"
snow_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>CarSnow)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> - Snowcar"
snow_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Snowcar)$",
    re.IGNORECASE)
# Pattern training: "Training <mapnumber> - CarSnow"
snow_training_pattern_1 = re.compile(
    rf"^(?P<special_map_name>.*?)\s*-\s*(?P<alteration>CarSnow)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (SnowCar)"
snow_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>SnowCar)\)$",
    re.IGNORECASE)

    # -------- [Snow] Carswitch ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Snowcarswitch"
snowcarswitch_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Snowcarswitch)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (CS-SC)"
snowcarswitch_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>CS-SC)\)$",
    re.IGNORECASE)

    # -------- [Snow] Checkpointless ---------- #
# Pattern1: "<season> <year> - <mapnumber> Checkpointless snow"
snowcheckpointless_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Checkpointless snow)$",
    re.IGNORECASE)

    # -------- [Snow] Ice ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Icy [Snow])"
snowice_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Icy \[Snow\])\)$",
    re.IGNORECASE)

    # -------- [Snow] Underwater ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> [Snow] (UW)"
snowunderwater_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Snow\]\s+\(UW\))$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> [Snow] (UW)"
snowunderwater_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Snow\]\s+\(UW\))$",
    re.IGNORECASE)

    # -------- [Snow] Wet Plastic ---------- #
# Pattern1: "(Snow) Wet Plastic <season> <year> - <mapnumber>"
snowwetplastic_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>\(Snow\) Wet Plastic)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- [Snow] Wood ---------- #
# Pattern1: "[Snow] <season> <year> - <mapnumber> Wood"
snowwood_seasonal_pattern_1 = re.compile(
    rf"^\[Snow\]\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Wood)$",
    re.IGNORECASE)

    # -------- [Rally] ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> [Rally]"
rally_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Rally\])$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> - CarRally"
rally_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>CarRally)$",
    re.IGNORECASE)
# Pattern training: "Training <mapnumber> - CarRally"
rally_training_pattern_1 = re.compile(
    rf"^(?P<special_map_name>.*?)\s+-\s+(?P<alteration>CarRally)$",
    re.IGNORECASE)
# Pattern4: "<totd> (RallyCar)"
rally_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>RallyCar)\)$",
    re.IGNORECASE)

    # -------- [Rally] Carswitch ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Rallycarswitch"
rallycarswitch_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Rallycarswitch)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (CS-RC)"
rallycarswitch_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>CS-RC)\)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (Carswitch RallyCar)"
rallycarswitch_totd_pattern_2 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>Carswitch RallyCar)\)$",
    re.IGNORECASE)

    # -------- [Rally] CP1 is End ---------- #
# Pattern seasonal: "[Rally] <season> <year> - <mapnumber> Cp1 is End"
rallycp1isend_seasonal_pattern_1 = re.compile(
    rf"^(?P<environment>\[Rally\])\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Cp1 is End)$",
    re.IGNORECASE)
# Pattern spring2020: "[Rally] <spring2020><mapnumber> - Cp1 is End"
rallycp1isend_spring2020_pattern_1 = re.compile(
    r"^(?P<environment>\[Rally\])\s+(?P<code>[STst][0-1]\d)\s*-\s*(?P<alteration>Cp1 is End)$",
    re.IGNORECASE)

    # -------- [Rally] Ice ---------- #
# Pattern1: "Ricy <season> <year> - <mapnumber>"
rallyice_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Ricy)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- [Rally] To The Top ---------- #
# Pattern1: "<season> <year> - <mapnumber> Rally to the Top"
rallytothetop_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Rally to the Top)$",
    re.IGNORECASE)

    # -------- [Rally] Underwater ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> [Rally] (Underwater)"
rallyunderwater_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\[Rally\]\s+\((?P<alteration>Underwater)\)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> [Rally] (UW)"
rallyunderwater_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\[Rally\]\s+\((?P<alteration>UW)\)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> [Rally] (UW)"
rallyunderwater_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\[Rally\]\s+\((?P<alteration>UW)\)$",
    re.IGNORECASE)

    # -------- [Desert] ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> [Desert]"
desert_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Desert\])$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> - CarDesert"
desert_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>CarDesert)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> - DesertCar"
desert_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>DesertCar)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> (DesertCar)"
desert_seasonal_pattern_4 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>DesertCar)\)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> - CarDesert"
desert_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>CarDesert)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> - CarDesert"
desert_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+-\s+(?P<alteration>CarDesert)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (DesertCar)"
desert_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>DesertCar)\)$",
    re.IGNORECASE)


    # -------- [Desert] Antiboost ---------- #
# Pattern1: "<season> <year> - <mapnumber> - DAB"
desertantiboost_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>DAB)$",
    re.IGNORECASE)

    # -------- [Desert] Carswitch ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Desertcarswitch"
desertcarswitch_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Desertcarswitch)$",
    re.IGNORECASE)
# Pattern totd 1: "<totdname> (CS-DC)"
desertcarswitch_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>CS-DC)\)$",
    re.IGNORECASE)
# Pattern totd 2: "<totdname> (CS-DesertCar)"
desertcarswitch_totd_pattern_2 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>CS-DesertCar)\)$",
    re.IGNORECASE)



    # -------- [Desert] Ice ---------- #
# Pattern1: "Dicy <season> <year> - <mapnumber>"
desertice_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Dicy)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- [Desert] To The Top ---------- #
# Pattern1: "<season> <year> - <mapnumber> Desert to the Top"
deserttothetop_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Desert to the Top)$",
    re.IGNORECASE)

    # -------- [Desert] Underwater ---------- #
# Pattern1: "<season> <year> - <mapnumber> [Desert] (UW)"
desertunderwater_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Desert\]\s+\(UW\))$",
    re.IGNORECASE)

    # -------- [Desert] Reverse ---------- #
# Pattern1: "<season> <year> - <mapnumber> - Reverse Desert"
desertreverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Reverse Desert)$",
    re.IGNORECASE)


    # -------- All Cars ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> all cars"
allcars_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>all cars)$",
    re.IGNORECASE)



# ################ Altered Game Mode ################ #

    # -------- [Race] ---------- #
# Pattern1: "<season> <year> - <mapnumber> [Race]"
race_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Race\])$",
    re.IGNORECASE)
# Pattern
#race_discovery_pattern_1 = re.compile(
#    rf"^(?P<discovery>{escaped_discovery_name})\s+(?P<alteration>\[Race\])$",
#    re.IGNORECASE
#)   

    # -------- [Stunt] ---------- #
# Pattern1: "<season> <year> - <mapnumber> [Stunt]"
stunt_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Stunt\])$",
    re.IGNORECASE)

    # -------- [Platform] ---------- #
# Pattern1: "<season> <year> - <mapnumber> [Platform]"
platform_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>\[Platform\])$",
    re.IGNORECASE)


# ################ Multi Alterations ################ #

    # -------- Checkpointless Reverse ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Checkpointless Reverse)"
checkpointlessreverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Checkpointless Reverse)\)$",
    re.IGNORECASE)
# Pattern2: "<spring2020><mapnumber> (Checkpointless Reverse)"
checkpointlessreverse_spring2020_pattern_2 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+\((?P<alteration>Checkpointless Reverse)\)$",
    re.IGNORECASE)
# Pattern3: "<season> <year> - <mapnumber> - CPLess, Reverse"
checkpointlessreverse_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>CPLess, Reverse)$",
    re.IGNORECASE)
# Pattern4: "<season> <year> - <mapnumber> - CPLess, Reverse (G)"
checkpointlessreverse_seasonal_pattern_4 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>CPLess, Reverse \(G\))$",
    re.IGNORECASE)
# Pattern5: "(G) <season> <year> - <mapnumber> - CPLess, Reverse"
checkpointlessreverse_seasonal_pattern_5 = re.compile(
    rf"^(?P<alteration>\(G\))\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration_suffix>CPLess, Reverse)$",
    re.IGNORECASE)

    # -------- DEET To The Top ---------- #
# Pattern1: "<season> <year> - <mapnumber> (DEET to the Top)"
deettothetop_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>DEET to the Top)\)$",
    re.IGNORECASE)

    # -------- Ice Reverse ---------- #
# Pattern1: "<season> <year> - <mapnumber> IR"
icereverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>IR)$",
    re.IGNORECASE)

    # -------- Ice Reverse Reactor ---------- #
# Pattern seasonal: "Icy RR <season> <year> <mapnumber>"
icereversereactor_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Icy RR)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Ice Short ---------- #
# Pattern seasonal: "short - Icy <season> <year> - <mapnumber>" short - Icy Winter 2023 - 17
iceshort_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration_prefix>short)\s+-\s+(?P<alteration>Icy)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
    
    # -------- Magner Reverse ---------- #
# Pattern1: "<season> <year> - <mapnumber> Magnet Reverse"
magnetreverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Magnet Reverse)$",
    re.IGNORECASE)

    # -------- Plastic Reverse ---------- #
# Pattern1: "<season> <year> - <mapnumber> PR"
plasticreverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>PR)$",
    re.IGNORECASE)

    # -------- Reverse Sky is the Finish ---------- #
# Pattern1: "<season> <year> - <mapnumber> - Rev Sky is Finish"
reverseskyfinish_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Rev Sky is Finish)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> - Rev Sky Finish"
reverseskyfinish_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Rev Sky Finish)$",
    re.IGNORECASE)
# Pattern3: "<season> <year> - <mapnumber> - Rev Sky Fin"
reverseskyfinish_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Rev Sky Fin)$",
    re.IGNORECASE)

    # -------- Start Water 2 UP 1 Left - Checkpoints Unlinked - Finish 2 Down 1 Right ---------- #
# Pattern1: "<season> <year> - <mapnumber> sw2u1l-cpu-f2d1r"
sw2u1lcpuf2d1r_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>sw2u1l-cpu-f2d1r)$",
    re.IGNORECASE)

    # -------- Underwater Reverse ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (UW Reverse)"
underwaterreverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>UW Reverse)\)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> UW Reverse"
underwaterreverse_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>UW Reverse)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> (UW Reverse)"
underwaterreverse_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+-\s+(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>UW Reverse)\)$",
    re.IGNORECASE)

    # -------- Wet Plastic ---------- #
# Pattern seasonal: "Wet Plastic <season> <year> - <mapnumber>"
wetplastic_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Wet Plastic)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Wet Plastic Training - <mapnumber>"
wetplastic_training_pattern_1 = re.compile(
    rf"^(?P<alteration>Wet Plastic)\s+Training\s+-\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Wet Wood ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Wet Wood)"
wetwood_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Wet Wood)\)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> (Wet Wood Red Reactor Down)"
wetwood_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Wet Wood Red Reactor Down)\)$",
    re.IGNORECASE)
# Pattern3: "<season> <year> - <mapnumber> (Wet Wood Yellow Reactor Down)"
wetwood_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Wet Wood Yellow Reactor Down)\)$",
    re.IGNORECASE)

    # -------- Wet Icy Wood ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (Wet Icy Wood)"
weticywood_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Wet Icy Wood)\)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> (100% Wet Icy Wood)"
weticywood_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>100% Wet Icy Wood)\)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> (Pure Wet Icy Wood)"
weticywood_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Pure Wet Icy Wood)\)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> (Wet Icy Wood)"
weticywood_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+-\s+(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Wet Icy Wood)\)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> (Wet Icy Wood)"
weticywood_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+\((?P<alteration>Wet Icy Wood)\)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (Wet Icy Wood)"
weticywood_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>Wet Icy Wood)\)$",
    re.IGNORECASE)

    # -------- YEET Max-Up ---------- #
# Pattern1: "YEET <season> <year> - <mapnumber> Max-up"
yeetmaxup_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>YEET)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{2,4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration_suffix>Max-up)$",
    re.IGNORECASE)

    # -------- YEET (Random) Puzzle ---------- #
# Pattern1: "<season> <year> - <mapnumber> (YEET Puzzle)"
yeetpuzzle_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Yeet Puzzle)\)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> (YEET Random Puzzle)"
yeetpuzzle_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Yeet Random Puzzle)\)$",
    re.IGNORECASE)

    # -------- YEET Reverse ---------- #
# Pattern1: "YEET <season> <year> - <mapnumber> Reverse"
yeetreverse_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>YEET)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{2,4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration_suffix>Reverse)$",
    re.IGNORECASE)


# ################ Other Alterations ################ #

    # -------- XX-But ---------- #
# Pattern1: ""
#xxbut_seasonal_pattern_1 = re.compile(
#    rf"",
#    re.IGNORECASE
#)

    # -------- Flat/2D ---------- #
# Pattern seasonal: "FLAT <season> <year> - <mapnumber>"
flat_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>FLAT)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{2,4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern seasonal: "Flat<season>'<year> - <mapnumber>"
flat_seasonal_pattern_2 = re.compile(
    rf"^(?P<alteration>Flat)(?P<season>{SEASON_REGEX})'(?P<year>\d{{2}})\s+-\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern seasonal: "2D-<season><year>-<mapnumber>"
flat_seasonal_pattern_3 = re.compile(
    rf"^(?P<alteration>2D)-(?P<season>{SEASON_REGEX})(?P<year>\d{{4}})-(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)    
# Pattern training: "Flat Training - <mapnumber>"
flat_training_pattern_1 = re.compile(
    rf"^(?P<alteration>Flat)\s(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Flat"
flat_training_pattern_2 = re.compile(
    rf"^(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Flat)$",
    re.IGNORECASE)

    # -------- A08 ---------- #
# Pattern1: "<season> <year> - <mapnumber> - 08"
a08_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>08)$",
    re.IGNORECASE)

    # -------- Backwards ---------- #
# Pattern1: "<season> <year> - <mapnumber> backwards"
backwards_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>backwards)$",
    re.IGNORECASE)

    # -------- BOSS ---------- #
# FIXME: This alteration is fundamentally different regarding "mapnumber", as it applies to multiple maps, this is the reason that map number is in an array...
# Pattern1: "BOSS <each map number in sets from 1-5 shown in sets using colours, white = 1-5, green = 6-10, blue = 11-15, red 16-20 black 21-25> of <season> <year>"
#boss_seasonal_pattern_1 = re.compile(
#    rf"^(?P<alteration>BOSS)\s+(?P<mapnumber>\d{{1,2}})\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})$",
#    re.IGNORECASE
#)
# Pattern2: "<each map number in sets from 1-5 shown in sets using colours, white = 1-5, green = 6-10, blue = 11-15, red 16-20 black 21-25> BOSS - <season>'<year>"
#boss_seasonal_pattern_2 = re.compile(
#    rf"^(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>BOSS)\s+-\s+(?P<season>{SEASON_REGEX})'(?P<year>\d{{2}})$",
#    re.IGNORECASE
#)

    # -------- Bumper ---------- #
# Pattern1: "<season> <year> - <mapnumber> - Bumper"
bumper_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Bumper)$",
    re.IGNORECASE)
# Pattern2: "Training - <mapnumber> Bumper"
bumper_training_pattern_2 = re.compile(
    rf"^(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Bumper)$",
    re.IGNORECASE)

# #### Altered Camera #### #
    # -------- Blind ---------- #
# Pattern seasonal: "<season> <mapnumber> (Blind)"
blind_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Blind)\)$",
    re.IGNORECASE)
# Pattern training: "Blind Training - <mapnumber>"
blind_training_pattern_1 = re.compile(
    rf"^(?P<alteration>Blind)\s+(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
    # -------- Egocentrism ---------- #
# Pattern1: "<season> <year> - <mapnumber> Egocentrism"
egocentrism_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Egocentrism)$",
    re.IGNORECASE)
    # -------- Replay ---------- #
# Pattern1: "<season> <year> - Replay <mapnumber>"
replay_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s+(?P<alteration>Replay)\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# #### End of Altered Camera #### #

    # -------- N'golo ---------- #
# Pattern1: "<season>N'golo <year> - <mapnumber>"
ngolo_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})N'golo\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern2: "<season>olo <year> - <mapnumber>"
ngolo_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>Spring)olo\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Checkpoin't ---------- #
# Pattern1: "<season> <year> Checkpoin't - <mapnumber>"
checkpoin_t_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<alteration>Checkpoin't)\s+-\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Colour Combined ---------- #
# Pattern1: "<season> <year> - <each map number in sets from 1-5 shown in sets using colours, white = 1-5, green = 6-10, blue = 11-15, red 16-20 black 21-25> Combined"
colourcombined_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+-\s+(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Combined)$",
    re.IGNORECASE)

    # -------- Checkpoint Boost Swap ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> CP-Boost Swap"
checkpointboostswap_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>CP-Boost Swap)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> (CP-Boost)"
checkpointboostswap_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>CP-Boost)\)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> CP-Boost"
checkpointboostswap_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>CP-Boost)$",
    re.IGNORECASE)

    # -------- Checkpoint 1 Kept ---------- #
# Pattern1: "<season> <year> - <mapnumber> CP1 Kept"
checkpoint1kept_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>CP1 Kept)$",
    re.IGNORECASE)

    # -------- Checkpointfull ---------- #
# Pattern1: "<season> <year> - <mapnumber> CPfull"
checkpointfull_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>CPfull)$",
    re.IGNORECASE)

    # -------- Checkpointless ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> - Checkpointless"
checkpointless_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Checkpointless)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> - Checkpointless"
checkpointless_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Checkpointless)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> - Checkpointless"
checkpointless_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+-\s+(?P<alteration>Checkpointless)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (cpless)"
checkpointless_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>cpless)\)$",
    re.IGNORECASE)

    # -------- Checkpointlink ---------- #
# Pattern1: "<season> <year> - <mapnumber> CPLink"
checkpointlink_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>CPLink)$",
    re.IGNORECASE)

    # -------- Checkpoints Rotated 90° / Got Rotated ---------- #
# Pattern1: "<season> <year> - <mapnumber> - CPs Rotated 90°"
checkpointsrotated90_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>CPs Rotated 90°)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> Got Rotated"
gotrotated_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Got Rotated)$",
    re.IGNORECASE)

    # -------- DragonYeet ---------- #
# Pattern1: "<season> <year> - <mapnumber> (DragonYeet)"
dragonyeet_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>DragonYeet)\)$",
    re.IGNORECASE)

    # -------- Earthquake ---------- #
# Pattern1: "<season> <year> - <mapnumber> Earthquake"
earthquake_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Earthquake)$",
    re.IGNORECASE)

    # -------- Extra Checkpoint ---------- #
# Pattern1: "<season> <year> - <mapnumber> Extra CP"
extracheckpoint_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Extra CP)$",
    re.IGNORECASE)

    # -------- Flipped ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Flipped)"
flipped_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Flipped)\)$",
    re.IGNORECASE)
# Pattern2: "<season><year>UpsideDown - <mapnumber>"
flipped_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})(?P<year>\d{{4}})(?P<alteration_suffix>UpsideDown)\s+-\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Holes ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> (Holes)"
holes_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Holes)\)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Holes"
holes_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+-\s+(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Holes)$",
    re.IGNORECASE)

    # -------- Lunatic ---------- #
# Pattern1: "Lunatic <season> <year> - <mapnumber>"
lunatic_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Lunatic)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern2: "Harder <season> <year> - <mapnumber>"
lunatic_seasonal_pattern_2 = re.compile(
    rf"^(?P<alteration>Harder)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Mini-RPG ---------- #
# Pattern seasonal: "RPG <season><year> - <mapnumber>"
minirpg_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>RPG)\s+(?P<season>{SEASON_REGEX})(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> Mini RPG"
minirpg_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Mini RPG)$",
    re.IGNORECASE)

    # -------- Mirrored ---------- #
# Pattern seasonal: "<season> <mapnumber> (Mirror)"
mirrored_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Mirror)\)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> Mirrored"
mirrored_training_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+-\s+(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Mirrored)$",
    re.IGNORECASE)

    # -------- No Items ---------- #
# Pattern1: "<season> <year> - <mapnumber> NoItems"
noitems_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>NoItems)$",
    re.IGNORECASE)

    # -------- Pool Hunters ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Pool Hunters"
poolhunters_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Pool Hunters)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> poolhunter - <mapnumber>"
poolhunters_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<alteration>poolhunter)\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Random ---------- #
# Pattern1: "Random <season> <year> - <mapnumber>"
random_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Random)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Ring Checkpoint ---------- #
# Pattern1: "<season> <year> - <mapnumber> Ring CP"
ringcheckpoint_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Ring CP)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> (Ring CP)"
ringcheckpoint_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Ring CP)\)$",
    re.IGNORECASE)

    # -------- Sections Joined ---------- #
# FIXME: This alteration is fundamentally different regarding "mapnumber", as it applies to multiple maps, I will likely say that 'map 1 is the first section of each set' etc
# Pattern seasonal: "<season> <year> - Section [Index] joined"
sectionsjoined_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<alteration>Section\s*(?P<mapnumber>\d{{1,2}})\s*joined)$",
    re.IGNORECASE)

    # -------- Select DEL ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Select DEL)"
selectdel_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Select DEL)\)$",
    re.IGNORECASE)

    # -------- Speedlimit ---------- #
# Pattern1: "<season> <year> - <mapnumber> (Speedlimit)"
speedlimit_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Speedlimit)\)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> Speed Limit"
speedlimit_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Speed Limit)$",
    re.IGNORECASE)

    # -------- Start 1-Down ---------- #
# there are a bunch of maps that are just taggen "1-down" without the "start" part, so I have to use 'special uids' to individually identify them
# Pattern1: "<season> <year> - <mapnumber> (Start 1-Down)"
start1down_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>Start 1-Down)\)$",
    re.IGNORECASE)

    # -------- Supersized ---------- #
# FIXME: Supersized_Spring_2024_-_05 just found out that cases like <--- exist, so I have to replace "_" with " " before doing any regex? (or is this also counted as a whitespace?)
# Pattern1: "Supersized <season> <year> - <mapnumber>"
supersized_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Supersized)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern2: "Supersized Training - <mapnumber>"
supersized_training_pattern_2 = re.compile(
    rf"^(?P<alteration>Supersized)\s+(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
# Pattern3: "<season> <year> <mapnumber> Big"
supersized_seasonal_pattern_3 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s+(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Big)$",
    re.IGNORECASE)
# Pattern4: "Super<mapnumber>"
supersized_seasonal_pattern_4 = re.compile(
    rf"^(?P<alteration>Super)(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Straight to the Finish ---------- #
# Pattern seasonal: "<season> <year> - <mapnumber> Straight to the Finish"
straighttothefinish_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Straight to the Finish)$",
    re.IGNORECASE)
# Pattern seasonal: "<season> <year> - <mapnumber> STTF"
straighttothefinish_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>STTF)$",
    re.IGNORECASE)
# Pattern training: "Training - <mapnumber> STTF"
straighttothefinish_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>STTF)$",
    re.IGNORECASE)
# Pattern spring2020: "<spring2020><mapnumber> STTF"
straighttothefinish_spring2020_pattern_1 = re.compile(
    r"^(?P<code>[STst][0-1]\d)\s+(?P<alteration>STTF)$",
    re.IGNORECASE)
# Pattern totd: "<totdname> (STTF)"
straighttothefinish_totd_pattern_1 = re.compile(
    rf"^{totd_pattern_group}\s+\((?P<alteration>STTF)\)$",
    re.IGNORECASE)

    # -------- Stunt Mode ---------- #
# Pattern1: "<season> <year> - <mapnumber> Stunt"
stuntmode_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Stunt)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> Stunt Mode"
stuntmode_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Stunt Mode)$",
    re.IGNORECASE)

    # -------- Symmetrical ---------- #
# Pattern1: "Symmetrical <season> <year> - <mapnumber>"
symmetrical_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>Symmetrical)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- Tilted ---------- #
# Pattern1: "<season> <mapnumber> - Tilted"
tilted_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Tilted)$",
    re.IGNORECASE)

    # -------- YEET ---------- #
# Pattern1: "YEET <season> <year> - <mapnumber>"
yeet_seasonal_pattern_1 = re.compile(
    rf"^(?P<alteration>YEET)\s+(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)

    # -------- YEET Down ---------- #
# Pattern1: "<season> <year> - <mapnumber> (DEET)"
yeetdown_seasonal_pattern_1 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+\((?P<alteration>DEET)\)$",
    re.IGNORECASE)
# Pattern2: "<season> <year> - <mapnumber> - Deet"
yeetdown_seasonal_pattern_2 = re.compile(
    rf"^(?P<season>{SEASON_REGEX})\s+(?P<year>\d{{4}})\s*-\s*(?P<mapnumber>\d{{1,2}})\s+-\s+(?P<alteration>Deet)$",
    re.IGNORECASE)


# ################ Sorted as only training ################ #

    # -------- Walmart Mini ---------- #
# Pattern training: "Training - <mapnumber> Walmart Mini"
wallmartmini_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s+-\s+(?P<mapnumber>\d{{1,2}})\s+(?P<alteration>Walmart Mini)$",
    re.IGNORECASE)

    # -------- Staircase ---------- #
# Pattern training: "Training Staircase - <mapnumber>"
staircase_training_pattern_1 = re.compile(
    rf"^(?P<season>Training)\s+(?P<alteration>Staircase)\s+-\s+(?P<mapnumber>\d{{1,2}})$",
    re.IGNORECASE)
    




ALL_PATTERNS = [
    dirt_seasonal_pattern_1, 
    fastmagnet_seasonal_pattern_1,
    flooded_seasonal_pattern_1, flooded_training_pattern_1, flooded_spring2020_pattern_1,
    grass_seasonal_pattern_1,
    ice_seasonal_pattern_1, ice_training_pattern_1,
    magnet_seasonal_pattern_1, magnet_training_pattern_2,
    mixed_seasonal_pattern_1, mixed_training_pattern_1,
    penalty_seasonal_pattern_1, penalty_training_pattern_1,
    plastic_seasonal_pattern_1,
    road_seasonal_pattern_1, road_seasonal_pattern_2, road_training_pattern_1,
    wood_seasonal_pattern_1, wood_training_pattern_1, wood_spring2020_pattern_1,
    bobsleigh_seasonal_pattern_1,
    pipe_seasonal_pattern_1,
    sausage_seasonal_pattern_1, sausage_training_pattern_2,
    slottrack_seasonal_pattern_1,
    surfaceless_seasonal_pattern_1,
    underwater_seasonal_pattern_1,
    
    antibooster_seasonal_pattern_1,
    boosterless_seasonal_pattern_1, boosterless_spring2020_pattern_1,
    broken_seasonal_pattern_1,
    cleaned_seasonal_pattern_1,
    cruisecontrol_seasonal_pattern_1,
    cruiseeffects_seasonal_pattern_1, cruiseeffects_training_pattern_2,
    fast_seasonal_pattern_1,
    fragile_seasonal_pattern_1, fragile_seasonal_pattern_2,
    fullfragile_seasonal_pattern_1,
    freewheel_seasonal_pattern_1,
    glider_seasonal_pattern_1,
    nobrakes_seasonal_pattern_1, nobrakes_seasonal_pattern_2,
    noeffects_seasonal_pattern_1, 
    nogrip_seasonal_pattern_1, nogrip_seasonal_pattern_2,
    nosteering_seasonal_pattern_1, nosteering_training_pattern_1,
    randomdankness_seasonal_pattern_1, randomdankness_training_pattern_1,
    randomeffects_seasonal_pattern_1,
    reactor_seasonal_pattern_1,
    reactordown_seasonal_pattern_1, reactordown_seasonal_pattern_2,
    redeffects_seasonal_pattern_1, redeffects_training_pattern_1,
    rngboosters_seasonal_pattern_1, rngboosters_spring2020_pattern_1,
    slowmo_seasonal_pattern_1, slowmo_seasonal_pattern_2,
    wetwheels_seasonal_pattern_1,
    worntires_seasonal_pattern_1,
    
    oneback_seasonal_pattern_1, oneback_seasonal_pattern_2, oneback_seasonal_pattern_3, oneforward_training_pattern_1, oneforward_spring2020_pattern_1, oneforward_totd_pattern_1,
    onedown_seasonal_pattern_1, onedown_training_pattern_1, onedown_spring2020_pattern_1, onedown_totd_pattern_1,
    oneleft_seasonal_pattern_1, oneright_seasonal_pattern_1,
    oneup_seasonal_pattern_1, oneup_training_pattern_1, oneup_spring2020_pattern_1, oneup_totd_pattern_1,
    twoup_seasonal_pattern_1,
    betterreverse_seasonal_pattern_1, betterreverse_seasonal_pattern_2,
    cp1isend_seasonal_pattern_1, cp1isend_seasonal_pattern_2, cp1isend_training_pattern_1, cp1isend_spring2020_pattern_1, cp1isend_totd_pattern_1,
    floorfin_seasonal_pattern_1,
    groundclippers_seasonal_pattern_1,
    inclined_seasonal_pattern_1,
    manslaughter_seasonal_pattern_1,
    nogear5_seasonal_pattern_1,
    podium_seasonal_pattern_1,
    puzzle_seasonal_pattern_1, puzzle_training_pattern_1,
    reverse_seasonal_pattern_1, reverse_training_pattern_1, reverse_spring2020_pattern_1, reverse_totd_pattern_1,
    roofing_seasonal_pattern_1,
    short_seasonal_pattern_1, short_seasonal_pattern_2, short_seasonal_pattern_3, short_seasonal_pattern_4, short_training_pattern_1, short_spring2020_pattern_1,
    skyfinish_spring2020_pattern_1, skyfinish_seasonal_pattern_2, skyfinish_seasonal_pattern_3, skyfinish_seasonal_pattern_4, skyfinish_totd_pattern_5,
    thereandback_seasonal_pattern_1, thereandback_seasonal_pattern_2,
    yeptreepuzzle_seasonal_pattern_1,
    
    stadium_seasonal_pattern_1, stadium_seasonal_pattern_2, #stadium_seasonal_pattern_3,
    stadiumtothetop_seasonal_pattern_1,
    stadiumwetwood_seasonal_pattern_1,
    snow_seasonal_pattern_1, snow_seasonal_pattern_2, snow_seasonal_pattern_3, snow_training_pattern_1, snow_totd_pattern_1,
    snowcarswitch_seasonal_pattern_1, snowcarswitch_totd_pattern_1,
    snowcheckpointless_seasonal_pattern_1,
    snowice_seasonal_pattern_1,
    snowunderwater_seasonal_pattern_1,snowunderwater_training_pattern_1,
    snowwetplastic_seasonal_pattern_1,
    snowwood_seasonal_pattern_1,
    rally_seasonal_pattern_1, rally_seasonal_pattern_2, rally_training_pattern_1, rally_totd_pattern_1,
    rallycarswitch_seasonal_pattern_1, rallycarswitch_totd_pattern_1, rallycarswitch_totd_pattern_2,
    rallycp1isend_seasonal_pattern_1, rallycp1isend_spring2020_pattern_1,
    rallyice_seasonal_pattern_1,
    rallytothetop_seasonal_pattern_1,
    rallyunderwater_seasonal_pattern_1, rallyunderwater_seasonal_pattern_2, rallyunderwater_training_pattern_1, 
    desert_seasonal_pattern_1, desert_seasonal_pattern_2, desert_seasonal_pattern_3, desert_seasonal_pattern_4, desert_training_pattern_1, desert_spring2020_pattern_1, desert_totd_pattern_1,
    desertantiboost_seasonal_pattern_1,
    desertcarswitch_seasonal_pattern_1, desertcarswitch_totd_pattern_1, desertcarswitch_totd_pattern_2,
    desertice_seasonal_pattern_1,
    deserttothetop_seasonal_pattern_1,
    desertunderwater_seasonal_pattern_1,
    desertreverse_seasonal_pattern_1,
    allcars_seasonal_pattern_1,
    
    race_seasonal_pattern_1,
    stunt_seasonal_pattern_1,
    platform_seasonal_pattern_1,
    
    checkpointlessreverse_seasonal_pattern_1, checkpointlessreverse_spring2020_pattern_2, checkpointlessreverse_seasonal_pattern_3, checkpointlessreverse_seasonal_pattern_4, checkpointlessreverse_seasonal_pattern_5,
    deettothetop_seasonal_pattern_1,
    icereverse_seasonal_pattern_1,
    icereversereactor_seasonal_pattern_1,
    iceshort_seasonal_pattern_1,
    magnetreverse_seasonal_pattern_1,
    plasticreverse_seasonal_pattern_1,
    reverseskyfinish_seasonal_pattern_1, reverseskyfinish_seasonal_pattern_2, reverseskyfinish_seasonal_pattern_3,
    sw2u1lcpuf2d1r_seasonal_pattern_1, 
    underwaterreverse_seasonal_pattern_1, underwaterreverse_seasonal_pattern_2, underwaterreverse_training_pattern_1,
    wetplastic_seasonal_pattern_1, wetplastic_training_pattern_1,
    wetwood_seasonal_pattern_1, wetwood_seasonal_pattern_2, wetwood_seasonal_pattern_3,
    weticywood_seasonal_pattern_1, weticywood_seasonal_pattern_2, weticywood_seasonal_pattern_3, weticywood_training_pattern_1, weticywood_spring2020_pattern_1, weticywood_totd_pattern_1,
    yeetmaxup_seasonal_pattern_1,
    yeetpuzzle_seasonal_pattern_1, yeetpuzzle_seasonal_pattern_2,
    yeetreverse_seasonal_pattern_1,
    
    # xxbut_seasonal_pattern_1,
    flat_seasonal_pattern_1, flat_training_pattern_2, flat_seasonal_pattern_3, flat_training_pattern_1, flat_training_pattern_2,
    a08_seasonal_pattern_1,
    backwards_seasonal_pattern_1,
    #boss_seasonal_pattern_1, boss_seasonal_pattern_2,
    bumper_seasonal_pattern_1, bumper_training_pattern_2,
    # Camera
    blind_seasonal_pattern_1, blind_training_pattern_1,
    egocentrism_seasonal_pattern_1,
    replay_seasonal_pattern_1,
    #
    ngolo_seasonal_pattern_1, ngolo_seasonal_pattern_2,
    checkpoin_t_seasonal_pattern_1,
    colourcombined_seasonal_pattern_1,
    checkpointboostswap_seasonal_pattern_1, checkpointboostswap_training_pattern_1, checkpointboostswap_spring2020_pattern_1,
    checkpoint1kept_seasonal_pattern_1,
    checkpointfull_seasonal_pattern_1,
    checkpointless_seasonal_pattern_1, checkpointless_training_pattern_1, checkpointless_spring2020_pattern_1, checkpointless_totd_pattern_1,
    checkpointlink_seasonal_pattern_1,
    checkpointsrotated90_seasonal_pattern_1, gotrotated_seasonal_pattern_1,
    dragonyeet_seasonal_pattern_1,
    earthquake_seasonal_pattern_1,
    extracheckpoint_seasonal_pattern_1,
    flipped_seasonal_pattern_1, flipped_seasonal_pattern_2,
    holes_seasonal_pattern_1, holes_training_pattern_1,
    lunatic_seasonal_pattern_1, lunatic_seasonal_pattern_2,
    minirpg_seasonal_pattern_1, minirpg_seasonal_pattern_2,
    mirrored_seasonal_pattern_1, mirrored_training_pattern_1,
    noitems_seasonal_pattern_1,
    poolhunters_seasonal_pattern_1, poolhunters_seasonal_pattern_2,
    random_seasonal_pattern_1,
    ringcheckpoint_seasonal_pattern_1, ringcheckpoint_seasonal_pattern_2,
    sectionsjoined_seasonal_pattern_1,
    selectdel_seasonal_pattern_1,
    speedlimit_seasonal_pattern_1, speedlimit_seasonal_pattern_2,
    start1down_seasonal_pattern_1,
    supersized_seasonal_pattern_1, supersized_training_pattern_2, supersized_seasonal_pattern_3, supersized_seasonal_pattern_4,
    straighttothefinish_seasonal_pattern_1, straighttothefinish_seasonal_pattern_2, straighttothefinish_training_pattern_1, straighttothefinish_spring2020_pattern_1, straighttothefinish_totd_pattern_1,
    stuntmode_seasonal_pattern_1, stuntmode_seasonal_pattern_2,
    symmetrical_seasonal_pattern_1,
    tilted_seasonal_pattern_1,
    yeet_seasonal_pattern_1,
    yeetdown_seasonal_pattern_1, yeetdown_seasonal_pattern_2,
    
    # Sorted as only training (as of rn)
    wallmartmini_training_pattern_1,
    staircase_training_pattern_1
]

ft_pattern = re.compile(
    r"(?:ft' |ft |featuring |AT by )(\w+)",
    re.IGNORECASE
)

def check_discovery_map_name(map_name: str) -> str:
    for campaign in DISCOVERY_CAMPAIGNS:
        for dmap in campaign['maps'].keys():
            if dmap.lower() in map_name.lower():
                return campaign['name']
    return ""

def check_totd_map_name(map_name: str) -> bool:
    sanitized_map_name = SANITIZE_PATTERN.sub('', map_name).strip().lower()
    
    for totd_name in all_TOTD_map_names:
        totd_name_lower = totd_name.lower()
        start_match = sanitized_map_name.startswith(totd_name_lower + ' ')
        end_match = sanitized_map_name.endswith(' ' + totd_name_lower)
        exact_match = sanitized_map_name == totd_name_lower
        middle_match = f' {totd_name_lower} ' in sanitized_map_name

        if start_match or end_match or exact_match or middle_match:
            # logger.critical(f"Found TOTD map: {totd_name} in {map_name}")
            return True
    
    return False

def try_special_uids(map_uid: str):
    for entry in special_uids:
        if entry['uid'].lower() == map_uid.lower():
            year = int(entry['year']) if entry['year'] else None
            year = validate_year(year) if year else None
            map_nums = []
            if entry['mapNumber']:
                map_nums = validate_mapnumber([int(entry['mapNumber'])])
            return {
                'season': entry['season'].capitalize() if entry['season'] else None,
                'year': year,
                'mapnumber': map_nums,
                'alteration': entry['alteration'] if entry['alteration'] else ''
            }
    return None

def extract_and_remove_ft(map_name: str):
    match = ft_pattern.search(map_name)
    if match:
        username = match.group(1)
        start, end = match.span()
        map_name = map_name[:start] + map_name[end:]

    map_name = map_name.strip()
    if map_name.endswith('()'):
        map_name = map_name[:-2].strip()

    if map_name.startswith('(') and map_name.endswith(')'):
        map_name = map_name[1:-1].strip()

    return map_name, username if match else None


def normalize_whitespace(map_name: str):
    return re.sub(r'\s+', ' ', map_name).strip()

def match_known_patterns(map_name: str):
    for pattern in ALL_PATTERNS:
        match = pattern.match(map_name)
        if match:
            attrs = match.groupdict()

            if pattern == oneup_totd_pattern_1:
                alteration = attrs.get('alteration', '').strip()
                return {
                    'season': None,
                    'year': None,
                    'mapnumber': [],
                    'alteration': alteration,
                    'type': 'totd'
                }

            if 'code' in attrs and attrs['code']:
                code = attrs['code'].upper()
                season = 'Spring'
                year = 2020
                map_num = int(code[1:])
                # If starts with 'S': season='Spring', year=2020, mapnumber=mapnumber=mapnumber
                # If starts with 'T': season='Spring', year=2020, mapnumber=mapnumber+10=mapnumber
                if code.startswith('T'):
                    map_num += 10
                valid_mapnums = validate_mapnumber([map_num])
                if not valid_mapnums:
                    return None
                return {
                    'season': season,
                    'year': year,
                    'mapnumber': valid_mapnums,
                    'alteration': 'Short'
                }

            if 'year' in attrs and attrs['year']:
                y = validate_year(int(attrs['year']))
                if y is None:
                    return None
                attrs['year'] = y
            else:
                attrs['year'] = None

            if 'mapnumber' in attrs and attrs['mapnumber']:
                m = validate_mapnumber([int(attrs['mapnumber'])])
                if not m:
                    return None
                attrs['mapnumber'] = m
            else:
                attrs['mapnumber'] = []

            alteration = attrs.get('alteration', '').strip()
            alteration_suffix = attrs.get('alteration_suffix', '').strip() if 'alteration_suffix' in attrs else ''

            if alteration and alteration_suffix:
                combined_alteration = f"{alteration} {alteration_suffix}".strip()
            else:
                combined_alteration = alteration or alteration_suffix

            if 'season' in attrs and attrs['season']:
                attrs['season'] = attrs['season'].capitalize()
            else:
                attrs['season'] = None

            attrs['alteration'] = combined_alteration
            if 'alteration_suffix' in attrs:
                del attrs['alteration_suffix']

            return attrs
    return None

def assign_attributes(item_data: dict) -> dict:
    raw_name = item_data['name']
    sanitized_name = sanitize_name(raw_name)
    filename = sanitize_name(item_data['filename'].replace('.Map.Gbx', ''))
    map_uid = item_data.get('mapUid', '')

    sanitized_name, ft_username = extract_and_remove_ft(sanitized_name)
    sanitized_name = normalize_whitespace(sanitized_name)
    filename = normalize_whitespace(filename)

    attributes = match_known_patterns(sanitized_name)
    
    if not attributes:
        attributes = try_special_uids(map_uid)
    
    if not attributes and sanitized_name != filename:
        attributes = match_known_patterns(filename)

    if not attributes:
        attributes = {
            'season': None,
            'year': None,
            'mapnumber': [],
            'alteration': '',
            'type': None
        }
        logger.warning(f"Unmatched map name: {raw_name} (sanitized: {sanitized_name}) (totd: {check_totd_map_name(raw_name)})")
    else:
        discovery_type = check_discovery_map_name(raw_name)
        if discovery_type:
            attributes['type'] = discovery_type
        else:
            if attributes.get('type') != 'totd':
                if check_totd_map_name(raw_name):
                    if attributes.get('season') or attributes.get('year') or attributes.get('mapnumber'):
                        logger.error(f"TOTD map '{raw_name}' has season/year/mapnumber assigned, which should not happen!")
                        attributes['type'] = 'totd'
                    else:
                        attributes['type'] = 'totd'
                else:
                    if 'type' not in attributes:
                        attributes['type'] = None

    if attributes.get('alteration', '').lower() == 'super':
        attributes['alteration'] = 'Supersized'

    if ft_username:
        attributes['ft'] = ft_username

    if (
        item_data.get('author') in OFFICIAL_NADEO_AUTHOR_AND_SUBMITTOR_UIDS or
        item_data.get('submitter') in OFFICIAL_NADEO_AUTHOR_AND_SUBMITTOR_UIDS
    ):
        attributes['alteration'] = OFFICIAL_NADEO_TAG
    
    return attributes

def process_item(item: tuple) -> tuple:
    key, data = item
    parsed_attrs = assign_attributes(data)
    combined_data = {**data, **parsed_attrs}
    return key, combined_data

def main():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file {INPUT_FILE} not found.")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {INPUT_FILE}: {e}")
        return

    items = list(map_data.items())

    results = {}

    try:
        with open('totd_pattern_group.txt', 'w', encoding='utf-8') as f:
            f.write(totd_pattern_group)
        logger.info("totd_pattern_group written to pattern_dings.txt")
    except Exception as e:
        logger.error(f"Error writing to pattern_dings.txt: {e}")

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(process_item, item) for item in items]
        for future in futures:
            try:
                key, value = future.result()
                results[key] = value
            except Exception as e:
                x="x"
                #logger.error(f"Error processing item: {e}")

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        logger.info(f"Parsed data written to {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Error writing to output file {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    main()