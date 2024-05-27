Json::Value allMaps;

void LoadMapFromStorageObject() {
    string mapUrl = FetchRandomMapUrl();

    if (mapUrl.Length == 0) {
        log("Failed to get map URL from storage objects. URL is: '" + mapUrl + "'", LogLevel::Error, 7, "LoadMapFromStorageObject"); // mapUrl will always be empty xdd
        NotifyWarn("Unable to retrieve the map URL from storage objects. \nThis issue is likely due to the absence of maps matching your specified criteria. Please adjust your selections of alterations and/or seasons to ensure that there are available maps.");

        return;
    }

    PlayMap(mapUrl);
}

void LoadMapsFromConsolidatedFile() {
    string filePath = IO::FromStorageFolder("Data/consolidated_maps.json");
    
    allMaps = Json::FromFile(filePath);
}

string FetchRandomMapUrl() {
    array<Json::Value@> FilteredMaps;

    if (Time::Now - startTime > 20) {
        yield();
        startTime = Time::Now;
    }

    // Filter out 'season', 'year' and 'alteration' settings, and score settings
    for (uint i = 0; i < allMaps.Length; ++i) {
        Json::Value map = allMaps[i];
        
        if (shoulduseCumulativeSelections) {
            if (MatchesSeasonalSettings(map) && MatchesAlterationSettings(map) && MatchesScoreSettings(map)) {
                FilteredMaps.InsertLast(map);
            }
        } else {
            if ((MatchesSeasonalSettings(map) || MatchesAlterationSettings(map)) && MatchesScoreSettings(map)) {
                FilteredMaps.InsertLast(map);
            }
        }
        if (Time::Now - startTime > 20) {
            yield();
            startTime = Time::Now;
        }
    }


    // Select random from filtered
    if (!FilteredMaps.IsEmpty()) {
        uint randomIndex = Math::Rand(0, FilteredMaps.Length);
        Json::Value@ selectedMap = FilteredMaps[randomIndex];

        if (selectedMap !is null && selectedMap.HasKey("fileUrl") && selectedMap["fileUrl"].GetType() == Json::Type::String) {
            return string(selectedMap["fileUrl"]);
        }
    }

    log("No maps match the selected criteria", LogLevel::Error, 60, "FetchRandomMapUrl");
    return "";
}

bool MatchesSeasonalSettings(Json::Value map) {
    if (!IsSeasonSettingActive()) {return true;}
    
    if (IsUsing_Spring2020Maps && (map["season"] + "").ToLower() == "spring") && map["year"] == "2020" return true;
    if (IsUsing_Summer2020Maps && (map["season"] + "").ToLower() == "summer") && map["year"] == "2020" return true;
    if (IsUsing_Fall2020Maps   && (map["season"] + "").ToLower() == "fall")   && map["year"] == "2020" return true;
    if (IsUsing_Winter2021Maps && (map["season"] + "").ToLower() == "winter") && map["year"] == "2021" return true;
    if (IsUsing_Spring2021Maps && (map["season"] + "").ToLower() == "spring") && map["year"] == "2021" return true;
    if (IsUsing_Summer2021Maps && (map["season"] + "").ToLower() == "summer") && map["year"] == "2021" return true;
    if (IsUsing_Fall2021Maps   && (map["season"] + "").ToLower() == "fall")   && map["year"] == "2021" return true;
    if (IsUsing_Winter2022Maps && (map["season"] + "").ToLower() == "winter") && map["year"] == "2022" return true;
    if (IsUsing_Spring2022Maps && (map["season"] + "").ToLower() == "spring") && map["year"] == "2022" return true;
    if (IsUsing_Summer2022Maps && (map["season"] + "").ToLower() == "summer") && map["year"] == "2022" return true;
    if (IsUsing_Fall2022Maps   && (map["season"] + "").ToLower() == "fall")   && map["year"] == "2022" return true;
    if (IsUsing_Winter2023Maps && (map["season"] + "").ToLower() == "winter") && map["year"] == "2023" return true;
    if (IsUsing_Spring2023Maps && (map["season"] + "").ToLower() == "spring") && map["year"] == "2023" return true;
    if (IsUsing_Summer2023Maps && (map["season"] + "").ToLower() == "summer") && map["year"] == "2023" return true;
    if (IsUsing_Fall2023Maps   && (map["season"] + "").ToLower() == "fall")   && map["year"] == "2023" return true;
    if (IsUsing_Winter2024Maps && (map["season"] + "").ToLower() == "winter") && map["year"] == "2024" return true;
    if (IsUsing_Spring2024Maps && (map["season"] + "").ToLower() == "spring") && map["year"] == "2024" return true;
    if (IsUsing_Summer2024Maps && (map["season"] + "").ToLower() == "summer") && map["year"] == "2024" return true;
    if (IsUsing_Fall2024Maps   && (map["season"] + "").ToLower() == "fall")   && map["year"] == "2024" return true;
    if (IsUsing_Winter2025Maps && (map["season"] + "").ToLower() == "winter") && map["year"] == "2025" return true;
    if (IsUsing_Spring2025Maps && (map["season"] + "").ToLower() == "spring") && map["year"] == "2025" return true;
    if (IsUsing_Summer2025Maps && (map["season"] + "").ToLower() == "summer") && map["year"] == "2025" return true;

    if (IsUsing_AllSnowDiscovery   && tostring(map["season"]).ToLower() == "allsnowdiscovery")   return true;
    if (IsUsing_AllRallyDiscovery  && tostring(map["season"]).ToLower() == "allrallydiscovery")  return true;
    if (IsUsing_AllDesertDiscovery && tostring(map["season"]).ToLower() == "alldesertdiscovery") return true;

    if (IsUsing__AllOfficialCompetitions && (map["alteration"] + "").ToLower() == "!allofficialcompetitions") return true;
    if (IsUsing_AllOfficialCompetitions  && tostring(map["season"]).ToLower() == "allofficialcompetitions")  return true;

    if (IsUsing_AllTOTD && tostring(map["season"]).ToLower() == "alltotd") return true;

    return false;
}

bool MatchesAlterationSettings(Json::Value map) {
    if (!IsAlterationSettingActive()) {return true;}

    if (IsUsing_Dirt                         && (map["alteration"] + "").ToLower() == "dirt") return true;
    if (IsUsing_Fast_Magnet                  && (map["alteration"] + "").ToLower() == "fast mangnet") return true;
    if (IsUsing_Flooded                      && (map["alteration"] + "").ToLower() == "flooded") return true;
    if (IsUsing_Grass                        && (map["alteration"] + "").ToLower() == "grass") return true;
    if (IsUsing_Ice                          && (map["alteration"] + "").ToLower() == "ice") return true;
    if (IsUsing_Magnet                       && (map["alteration"] + "").ToLower() == "magnet") return true;
    if (IsUsing_Mixed                        && (map["alteration"] + "").ToLower() == "mixed") return true;
    if (IsUsing_Better_Mixed                 && (map["alteration"] + "").ToLower() == "better Mixed") return true;
    if (IsUsing_Penalty                      && (map["alteration"] + "").ToLower() == "penalty") return true;
    if (IsUsing_Plastic                      && (map["alteration"] + "").ToLower() == "plastic") return true;
    if (IsUsing_Road                         && (map["alteration"] + "").ToLower() == "road") return true;
    if (IsUsing_Wood                         && (map["alteration"] + "").ToLower() == "wood") return true;
    if (IsUsing_Bobsleigh                    && (map["alteration"] + "").ToLower() == "bobsleigh") return true;
    if (IsUsing_Pipe                         && (map["alteration"] + "").ToLower() == "pipe") return true;
    if (IsUsing_Sausage                      && (map["alteration"] + "").ToLower() == "sausage") return true;
    if (IsUsing_Underwater                   && (map["alteration"] + "").ToLower() == "underwater") return true;

    if (IsUsing_Cruise                       && (map["alteration"] + "").ToLower() == "cruise") return true;
    if (IsUsing_Fragile                      && (map["alteration"] + "").ToLower() == "fragile") return true;
    if (IsUsing_Full_Fragile                 && (map["alteration"] + "").ToLower() == "full fragile") return true;
    if (IsUsing_Freewheel                    && (map["alteration"] + "").ToLower() == "freewheel") return true;
    if (IsUsing_Glider                       && (map["alteration"] + "").ToLower() == "glider") return true;
    if (IsUsing_No_Brakes                    && (map["alteration"] + "").ToLower() == "no brakes") return true;
    if (IsUsing_No_Effects                   && (map["alteration"] + "").ToLower() == "no effects") return true;
    if (IsUsing_No_Grip                      && (map["alteration"] + "").ToLower() == "no grip") return true;
    if (IsUsing_No_Steer                     && (map["alteration"] + "").ToLower() == "no steer") return true;
    if (IsUsing_Random_Dankness              && (map["alteration"] + "").ToLower() == "random dankness") return true;
    if (IsUsing_Random_Effects               && (map["alteration"] + "").ToLower() == "random effects") return true;
    if (IsUsing_Reactor                      && (map["alteration"] + "").ToLower() == "reactor") return true;
    if (IsUsing_Reactor_Down                 && (map["alteration"] + "").ToLower() == "reactor down") return true;
    if (IsUsing_RNG_Booster                  && (map["alteration"] + "").ToLower() == "rng booster") return true;
    if (IsUsing_Slowmo                       && (map["alteration"] + "").ToLower() == "slowmo") return true;
    if (IsUsing_Wet_Wheels                   && (map["alteration"] + "").ToLower() == "wet wheels") return true;
    if (IsUsing_Worn_Tires                   && (map["alteration"] + "").ToLower() == "worn tires") return true;

    if (IsUsing_1Down                        && (map["alteration"] + "").ToLower() == "1 down") return true;
    if (IsUsing_1Back                        && (map["alteration"] + "").ToLower() == "1 back") return true;
    if (IsUsing_1Left                        && (map["alteration"] + "").ToLower() == "1 left") return true;
    if (IsUsing_1Right                       && (map["alteration"] + "").ToLower() == "1 right") return true;
    if (IsUsing_1Up                          && (map["alteration"] + "").ToLower() == "1 up") return true;
    if (IsUsing_2Up                          && (map["alteration"] + "").ToLower() == "2 up") return true;
    if (IsUsing_Better_Reverse               && (map["alteration"] + "").ToLower() == "better reverse") return true;
    if (IsUsing_CP1_is_End                   && (map["alteration"] + "").ToLower() == "cp1 is end") return true;
    if (IsUsing_Floor_Fin                    && (map["alteration"] + "").ToLower() == "floor fin") return true;
    if (IsUsing_Inclined                     && (map["alteration"] + "").ToLower() == "inclined") return true;
    if (IsUsing_Manslaughter                 && (map["alteration"] + "").ToLower() == "manslaughter") return true;
    if (IsUsing_No_Gear_5                    && (map["alteration"] + "").ToLower() == "no gear 5") return true;
    if (IsUsing_Podium                       && (map["alteration"] + "").ToLower() == "podium") return true;
    if (IsUsing_Puzzle                       && (map["alteration"] + "").ToLower() == "puzzle") return true;
    if (IsUsing_Reverse                      && (map["alteration"] + "").ToLower() == "reverse") return true;
    if (IsUsing_Roofing                      && (map["alteration"] + "").ToLower() == "roofing") return true;
    if (IsUsing_Short                        && (map["alteration"] + "").ToLower() == "short") return true;
    if (IsUsing_Sky_is_the_Finish            && (map["alteration"] + "").ToLower() == "sky is the finish") return true;
    if (IsUsing_There_and_Back_Boomerang     && (map["alteration"] + "").ToLower() == "there and back_boomerang") return true;
    if (IsUsing_YEP_Tree_Puzzle              && (map["alteration"] + "").ToLower() == "yep tree puzzle") return true;

    if (IsUsing_Stadium_                     && (map["alteration"] + "").ToLower() == "[stadium]") return true;
    if (IsUsing_Stadium_Wet_Wood             && (map["alteration"] + "").ToLower() == "[stadium] wet wood") return true;
    if (IsUsing_Snow_                        && (map["alteration"] + "").ToLower() == "[snow]") return true;
    if (IsUsing_Snow_Carswitch               && (map["alteration"] + "").ToLower() == "[snow] carswitch") return true;
    if (IsUsing_Snow_Checkpointless          && (map["alteration"] + "").ToLower() == "[snow] checkpointless") return true;
    if (IsUsing_Snow_Icy                     && (map["alteration"] + "").ToLower() == "[snow] icy") return true;
    if (IsUsing_Snow_Underwater              && (map["alteration"] + "").ToLower() == "[snow] underwater") return true;
    if (IsUsing_Snow_Wet_Plastic             && (map["alteration"] + "").ToLower() == "[snow] wet-plastic") return true;
    if (IsUsing_Snow_Wood                    && (map["alteration"] + "").ToLower() == "[snow] wood") return true;
    if (IsUsing_Rally_                       && (map["alteration"] + "").ToLower() == "[rally]") return true;
    if (IsUsing_Rally_Carswitch              && (map["alteration"] + "").ToLower() == "[rally] carswitch") return true;
    if (IsUsing_Rally_CP1_is_End             && (map["alteration"] + "").ToLower() == "[rally] cp1 is end") return true;
    if (IsUsing_Rally_Underwater             && (map["alteration"] + "").ToLower() == "[rally] underwater") return true;
    if (IsUsing_Rally_Icy                    && (map["alteration"] + "").ToLower() == "[rally] icy") return true;

    if (IsUsing_Checkpointless_Reverse       && (map["alteration"] + "").ToLower() == "checkpointless reverse") return true;
    if (IsUsing_Ice_Reverse                  && (map["alteration"] + "").ToLower() == "ice reverse") return true;
    if (IsUsing_Ice_Reverse_Reactor          && (map["alteration"] + "").ToLower() == "ice reverse reactor") return true;
    if (IsUsing_Ice_Short                    && (map["alteration"] + "").ToLower() == "ice short") return true;
    if (IsUsing_Magnet_Reverse               && (map["alteration"] + "").ToLower() == "magnet reverse") return true;
    if (IsUsing_Plastic_Reverse              && (map["alteration"] + "").ToLower() == "plastic reverse") return true;
    if (IsUsing_Sky_is_the_Finish_Reverse    && (map["alteration"] + "").ToLower() == "sky is the finish reverse") return true;
    if (IsUsing_sw2u1l_cpu_f2d1r             && (map["alteration"] + "").ToLower() == "sw2u1l-cpu-f2d1r") return true;
    if (IsUsing_Underwater_Reverse           && (map["alteration"] + "").ToLower() == "underwater reverse") return true;
    if (IsUsing_Wet_Plastic                  && (map["alteration"] + "").ToLower() == "wet plastic") return true;
    if (IsUsing_Wet_Wood                     && (map["alteration"] + "").ToLower() == "wet wood") return true;
    if (IsUsing_Wet_Icy_Wood                 && (map["alteration"] + "").ToLower() == "wet icy wood") return true;
    if (IsUsing_Yeet_Max_Up                  && (map["alteration"] + "").ToLower() == "yeet max-up") return true;
    if (IsUsing_YEET_Puzzle                  && (map["alteration"] + "").ToLower() == "yeet puzzle") return true;
    if (IsUsing_YEET_Random_Puzzle           && (map["alteration"] + "").ToLower() == "yeet random puzzle") return true;
    if (IsUsing_YEET_Reverse                 && (map["alteration"] + "").ToLower() == "yeet reverse") return true;

    if (IsUsing_XX_But                       && (map["alteration"] + "").ToLower() == "xx-but") return true;
    if (IsUsing_Flat_2D                      && (map["alteration"] + "").ToLower() == "flat_2d") return true;
    if (IsUsing_A08                          && (map["alteration"] + "").ToLower() == "a08") return true;
    if (IsUsing_Antibooster                  && (map["alteration"] + "").ToLower() == "antibooster") return true;
    if (IsUsing_Backwards                    && (map["alteration"] + "").ToLower() == "backwards") return true;
    if (IsUsing_Boosterless                  && (map["alteration"] + "").ToLower() == "boosterless") return true;
    if (IsUsing_BOSS                         && (map["alteration"] + "").ToLower() == "boss") return true;
    if (IsUsing_Broken                       && (map["alteration"] + "").ToLower() == "broken") return true;
    if (IsUsing_Bumper                       && (map["alteration"] + "").ToLower() == "bumper") return true;
    if (IsUsing_Ngolo_Cacti                  && (map["alteration"] + "").ToLower() == "ngolo_cacti") return true;
    if (IsUsing_Checkpoin_t                  && (map["alteration"] + "").ToLower() == "checkpoin't") return true;
    if (IsUsing_Checkpointless               && (map["alteration"] + "").ToLower() == "checkpointless") return true;
    if (IsUsing_Cleaned                      && (map["alteration"] + "").ToLower() == "cleaned") return true;
    if (IsUsing_Colours_Combined             && (map["alteration"] + "").ToLower() == "colours combined") return true;
    if (IsUsing_CP_Boost                     && (map["alteration"] + "").ToLower() == "cp_boost") return true;
    if (IsUsing_CP1_Kept                     && (map["alteration"] + "").ToLower() == "cp1 kept") return true;
    if (IsUsing_CPfull                       && (map["alteration"] + "").ToLower() == "cpfull") return true;
    if (IsUsing_CPLink                       && (map["alteration"] + "").ToLower() == "cpLink") return true;
    if (IsUsing_Earthquake                   && (map["alteration"] + "").ToLower() == "earthquake") return true;
    if (IsUsing_Fast                         && (map["alteration"] + "").ToLower() == "fast") return true;
    if (IsUsing_Flipped                      && (map["alteration"] + "").ToLower() == "flipped") return true;
    if (IsUsing_Got_Rotated_CPs_Rotated_90__ && (map["alteration"] + "").ToLower() == "got rotated_cps rotated 90°") return true;
    if (IsUsing_Ground_Clippers              && (map["alteration"] + "").ToLower() == "ground clippers") return true;
    // if (IsUsing_Hard                      && (map["alteration"] + "").ToLower() == "hard") return true; // NOTE TO SELF: It DOES find hard even though the log says it doesn't // Is actally Lunatic
    if (IsUsing_Holes                        && (map["alteration"] + "").ToLower() == "holes") return true;
    if (IsUsing_Lunatic                      && (map["alteration"] + "").ToLower() == "lunatic") return true;
    if (IsUsing_Mini_RPG                     && (map["alteration"] + "").ToLower() == "mini rpg") return true;
    if (IsUsing_Mirrored                     && (map["alteration"] + "").ToLower() == "mirrored") return true;
    if (IsUsing_Pool_Hunters                 && (map["alteration"] + "").ToLower() == "pool hunters") return true;
    if (IsUsing_Random                       && (map["alteration"] + "").ToLower() == "random") return true;
    if (IsUsing_Ring_CP                      && (map["alteration"] + "").ToLower() == "ring cp") return true;
    if (IsUsing_Sections_joined              && (map["alteration"] + "").ToLower() == "sections joined") return true;
    if (IsUsing_Select_DEL                   && (map["alteration"] + "").ToLower() == "select del") return true;
    if (IsUsing_Speedlimit                   && (map["alteration"] + "").ToLower() == "speedlimit") return true;
    if (IsUsing_Start_1_Down                 && (map["alteration"] + "").ToLower() == "start 1-down") return true;
    if (IsUsing_Supersized                   && (map["alteration"] + "").ToLower() == "supersized") return true;
    if (IsUsing_Straight_to_the_Finish       && (map["alteration"] + "").ToLower() == "straight to the finish") return true;
    if (IsUsing_Stunt                        && (map["alteration"] + "").ToLower() == "stunt") return true;
    if (IsUsing_Symmetrical                  && (map["alteration"] + "").ToLower() == "symmetrical") return true;
    if (IsUsing_Tilted                       && (map["alteration"] + "").ToLower() == "tilted") return true;
    if (IsUsing_YEET                         && (map["alteration"] + "").ToLower() == "yeet") return true;
    if (IsUsing_YEET_Down                    && (map["alteration"] + "").ToLower() == "yeet down") return true;

 // if (IsUsing_Trainig                      && (map["alteration"] + "").ToLower() == "") return true; // This is in 'season' not 'alteration'
    if (IsUsing_TMGL_Easy                    && (map["alteration"] + "").ToLower() == "tmgl easy") return true;
 // if (IsUsing__AllOfficialCompetitions     && (map["alteration"] + "").ToLower() == "") return true; // This is in 'season' not 'alteration'
    if (IsUsing_AllOfficialCompetitions      && (map["alteration"] + "").ToLower() == "!allofficialcompetitions") return true;
    if (IsUsing_OfficialNadeo                && (map["alteration"] + "").ToLower() == "!officialnadeo") return true;
 // if (IsUsing_AllTOTD                      && (map["alteration"] + "").ToLower() == "") return true; // This is in 'season' not 'alteration'

    return false;
}

bool MatchesScoreSettings(const Json::Value& map) {
    int authorScore = map["authorScore"];
    int goldScore = map["goldScore"];
    int silverScore = map["silverScore"];
    int bronzeScore = map["bronzeScore"];

    if ((authorScore < IsUsing_authorScoreMin) || (IsUsing_authorScoreMax != -1 && authorScore > IsUsing_authorScoreMax))
        return false;
    if ((goldScore < IsUsing_goldScoreMin) || (IsUsing_goldScoreMax != -1 && goldScore > IsUsing_goldScoreMax))
        return false;
    if ((silverScore < IsUsing_silverScoreMin) || (IsUsing_silverScoreMax != -1 && silverScore > IsUsing_silverScoreMax))
        return false;
    if ((bronzeScore < IsUsing_bronzeScoreMin) || (IsUsing_bronzeScoreMax != -1 && bronzeScore > IsUsing_bronzeScoreMax))
        return false;

    return true;
}


bool IsSeasonSettingActive() {
    return IsUsing_Spring2020Maps || IsUsing_Summer2020Maps || IsUsing_Fall2020Maps || 
        IsUsing_Winter2021Maps || IsUsing_Spring2021Maps || IsUsing_Summer2021Maps || IsUsing_Fall2021Maps || 
        IsUsing_Winter2022Maps || IsUsing_Spring2022Maps || IsUsing_Summer2022Maps || IsUsing_Fall2022Maps || 
        IsUsing_Winter2023Maps || IsUsing_Spring2023Maps || IsUsing_Summer2023Maps || IsUsing_Fall2023Maps || 
        IsUsing_Winter2024Maps || IsUsing_Spring2024Maps || IsUsing_Summer2024Maps || IsUsing_Fall2024Maps || 
        IsUsing_Winter2025Maps || IsUsing_Spring2025Maps || IsUsing_Summer2025Maps || 
        
        IsUsing_AllSnowDiscovery || IsUsing_AllRallyDiscovery || IsUsing_AllDesertDiscovery || 
        IsUsing__AllOfficialCompetitions || IsUsing_AllOfficialCompetitions || IsUsing_AllTOTD;
}

bool IsAlterationSettingActive() {
    return 
        IsUsing_Dirt || IsUsing_Fast_Magnet || IsUsing_Flooded || IsUsing_Grass || IsUsing_Ice || IsUsing_Magnet || IsUsing_Mixed || 
        IsUsing_Better_Mixed || IsUsing_Penalty || IsUsing_Plastic || IsUsing_Road || IsUsing_Wood || IsUsing_Bobsleigh || IsUsing_Pipe || 
        IsUsing_Sausage || IsUsing_Underwater || 
        
        IsUsing_Cruise || IsUsing_Fragile || IsUsing_Full_Fragile || IsUsing_Freewheel || IsUsing_Glider || IsUsing_No_Brakes || 
        IsUsing_No_Effects || IsUsing_No_Grip || IsUsing_No_Steer || IsUsing_Random_Dankness || IsUsing_Random_Effects || IsUsing_Reactor || 
        IsUsing_Reactor_Down || IsUsing_Slowmo || IsUsing_Wet_Wheels || IsUsing_Worn_Tires || 
        
        IsUsing_1Down || IsUsing_1Back || IsUsing_1Left || IsUsing_1Right || IsUsing_1Up || IsUsing_2Up || IsUsing_Better_Reverse || 
        IsUsing_CP1_is_End || IsUsing_Floor_Fin || IsUsing_Inclined || IsUsing_Manslaughter || IsUsing_No_Gear_5 || IsUsing_Podium || 
        IsUsing_Puzzle || IsUsing_Reverse || IsUsing_Roofing || IsUsing_Short || IsUsing_Sky_is_the_Finish || IsUsing_There_and_Back_Boomerang || 
        IsUsing_YEP_Tree_Puzzle || 
        
        IsUsing_Stadium_ || IsUsing_Stadium_Wet_Wood || IsUsing_Snow_ || IsUsing_Snow_Carswitch || IsUsing_Snow_Checkpointless || 
        IsUsing_Snow_Icy || IsUsing_Snow_Underwater || IsUsing_Snow_Wet_Plastic || IsUsing_Snow_Wood || IsUsing_Rally_ || IsUsing_Rally_Carswitch || 
        IsUsing_Rally_CP1_is_End || IsUsing_Rally_Underwater || IsUsing_Rally_Icy || 
        
        IsUsing_Checkpointless_Reverse || IsUsing_Ice_Reverse || IsUsing_Ice_Reverse_Reactor || IsUsing_Ice_Short || IsUsing_Magnet_Reverse || 
        IsUsing_Plastic_Reverse || IsUsing_Sky_is_the_Finish_Reverse || IsUsing_sw2u1l_cpu_f2d1r || IsUsing_Underwater_Reverse || 
        IsUsing_Wet_Plastic || IsUsing_Wet_Wood || IsUsing_Wet_Icy_Wood || IsUsing_Yeet_Max_Up || IsUsing_YEET_Puzzle || 
        IsUsing_YEET_Random_Puzzle || IsUsing_YEET_Reverse || 
        
        IsUsing_XX_But || IsUsing_Flat_2D || IsUsing_A08 || IsUsing_Antibooster || IsUsing_Backwards || IsUsing_Boosterless || IsUsing_BOSS || 
        IsUsing_Broken || IsUsing_Bumper || IsUsing_Ngolo_Cacti || IsUsing_Checkpoin_t || IsUsing_Cleaned || IsUsing_Colours_Combined || 
        IsUsing_CP_Boost || IsUsing_CP1_Kept || IsUsing_CPfull || IsUsing_Checkpointless || IsUsing_CPLink || IsUsing_Earthquake || IsUsing_Fast || 
        IsUsing_Flipped || IsUsing_Got_Rotated_CPs_Rotated_90__ || IsUsing_Ground_Clippers || /*IsUsing_Hard ||  // Is actally Lunatic */IsUsing_Holes || IsUsing_Lunatic || IsUsing_Mini_RPG || IsUsing_Mirrored || 
        IsUsing_Pool_Hunters || IsUsing_Random || IsUsing_Ring_CP || IsUsing_Sections_joined || IsUsing_Select_DEL || IsUsing_Speedlimit || 
        IsUsing_Start_1_Down || IsUsing_Supersized || IsUsing_Straight_to_the_Finish || IsUsing_Stunt || IsUsing_Symmetrical || IsUsing_Tilted || IsUsing_YEET || 
        IsUsing_YEET_Down || 
        
        IsUsing_TMGL_Easy || IsUsing_AllOfficialCompetitions || IsUsing_OfficialNadeo;
}
