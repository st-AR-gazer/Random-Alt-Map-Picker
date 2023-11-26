
const string tm_map_endpoint = "https://live-services.trackmania.nadeo.live/api/token/map/";

string globalMapUrl = "";
bool isWaitingForUrl = false;

void Main() {
    CheckRequiredPermissions();
    setFirstUid();
}

void setFirstUid() {
    array<string> uids = ReadUIDsFromFile("data.csv");
    string firstUid = GetRandomUID(uids);

    globalMapUrl = tm_map_endpoint + firstUid;

    NadeoServices::AddAudience("NadeoLiveServices");
    while (!NadeoServices::IsAuthenticated("NadeoLiveServices")) {
        yield();
    }
    Net::HttpRequest@ req = NadeoServices::Get("NadeoLiveServices", tm_map_endpoint + firstUid);
    req.Start();
    while (!req.Finished()) yield();

    if (req.ResponseCode() != 200) {
        log("TM API request returned response code " + req.ResponseCode(), LogLevel::Error);
        log("Response body:", LogLevel::Error);
        log(req.Body, LogLevel::Error);
        // return "";
    }

    Json::Value res = Json::Parse(req.String());
    globalMapUrl = res["downloadUrl"];

    print(globalMapUrl);
}

void GetMapUrl(const string &in map_uid) {
    NadeoServices::AddAudience("NadeoLiveServices");
    while (!NadeoServices::IsAuthenticated("NadeoLiveServices")) {
        yield();
    }
    Net::HttpRequest@ req = NadeoServices::Get("NadeoLiveServices", tm_map_endpoint + map_uid);
    req.Start();
    while (!req.Finished()) yield();

    if (req.ResponseCode() != 200) {
        log("TM API request returned response code " + req.ResponseCode(), LogLevel::Error);
        log("Response body:", LogLevel::Error);
        log(req.Body, LogLevel::Error);
        // return "";
    }

    Json::Value res = Json::Parse(req.String());
    globalMapUrl = res["downloadUrl"];
    isWaitingForUrl = false;
}


void PlayMap(const string &in map_uid) {
    // this code with slight modifications from
    // https://github.com/XertroV/tm-unbeaten-ats, licensed under the Unlicense

    if (!Permissions::PlayLocalMap()) {
        log("Lacking permissions to play local map", LogLevel::Warn);
        return;
    }

    // Reset the global URL variable and set the waiting flag
    string map_url = globalMapUrl;

    globalMapUrl = "";
    isWaitingForUrl = true;

    // Start GetMapUrl as a coroutine
    startnew(GetMapUrl, map_uid);

    if (map_url.Length == 0) {
        log("Failed to get map URL", LogLevel::Error);
        return;
    }

    startnew(PlayMapCoroutine, map_url);
}

void PlayMapCoroutine(const string &in map_url) {
    CTrackMania@ app = cast<CTrackMania@>(GetApp());
    if (app.Network.PlaygroundClientScriptAPI.IsInGameMenuDisplayed) {
        app.Network.PlaygroundInterfaceScriptHandler.CloseInGameMenu(CGameScriptHandlerPlaygroundInterface::EInGameMenuResult::Quit);
    }
    app.BackToMainMenu();

    while (!app.ManiaTitleControlScriptAPI.IsReady) yield();

    app.ManiaTitleControlScriptAPI.PlayMap(map_url, "", "");

}



void LoadNewMap() {
    array<string> uids = ReadUIDsFromFile("data.csv");
    string randomUID = GetRandomUID(uids);
    if (randomUID != "") {
        log("UID found in file", LogLevel::Info);
        const string map_uid = randomUID;
        // print("1 " + map_uid + " " + randomUID);
        PlayMap(map_uid);
    } else {
        log("No UIDs found in file", LogLevel::Error);
    }
}
string GetRandomUID(const array<string> &in uids) {
    if (uids.Length == 0) return "";
    int randomIndex = Math::Rand(0, uids.Length - 1);
    return uids[randomIndex];
}

string[] ReadUIDsFromFile(const string&in filePath) {
    array<string> uids;

    IO::FileSource fileSource(filePath);

    while (!fileSource.EOF()) {
        string line = fileSource.ReadLine();
        if (line.Length > 0) {
            uids.InsertLast(line);
        }
    }
    
    return uids;
}
