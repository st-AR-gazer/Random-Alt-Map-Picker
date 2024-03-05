string pluginStorageDataPath = IO::FromStorageFolder("data.csv");
string pluginStorageDataPathNewSortingSystem = IO::FromStorageFolder("New-Sorting-System/Other-Data/data.csv");

string pluginStorageVersionPath = IO::FromStorageFolder("currentInstalledVersion.json");
string checkFilePath = IO::FromStorageFolder("initCheck.txt"); 


void MoveDefaultDataFile() {
    if (!IO::FileExists(checkFilePath) || !IO::FileExists(pluginStorageDataPath)) {
        log("initCheck file does not exist in plugin storage, moving data and currentInstalledVersion to PluginStorage", LogLevel::Warn, 7);
        MoveFileToPluginStorage("src/DefaultData/data.csv", pluginStorageDataPath);
        MoveFileToPluginStorage("src/DefaultData/data.csv", pluginStorageDataPathNewSortingSystem);
        MoveFileToPluginStorage("src/DefaultData/defaultInstalledVersion.json", pluginStorageVersionPath);
        log("Files have been moved to storage", LogLevel::Info, 10);
        
        CreateCheckFile();
        log("initCheck file created", LogLevel::Info, 13);
    } else {
        log("initCheck file exists in plugin storage, not moving data", LogLevel::Info, 15);
    }
}

void MoveFileToPluginStorage(const string &in originalPath, const string &in storagePath) {
    IO::FileSource originalFile(originalPath);
    string fileContents = originalFile.ReadToEnd();
    log("Moving the file content", LogLevel::Info, 22);
    log("The content:\n" + /*fileContents +*/ "The filecontents are not included since it clogs log... xdd...", LogLevel::Info, 23);
    // log("The content:\n" + fileContents, LogLevel::Info, 23);

    IO::File targetFile;
    targetFile.Open(storagePath, IO::FileMode::Write);
    targetFile.Write(fileContents);
    targetFile.Close();

    log("Finished moving the file", LogLevel::Info, 30);
}

void CreateCheckFile() {
    IO::File checkFile;
    checkFile.Open(checkFilePath, IO::FileMode::Write);
    checkFile.Close();
}



string CheckCurrentInstalledVersionType() {
    IO::File file();
    file.Open(pluginStorageVersionPath, IO::FileMode::Read);
    string fileContents = file.ReadToEnd();
    file.Close();
    
    Json::Value currentVersionJson = Json::Parse(fileContents);

    if (currentVersionJson.GetType() == Json::Type::Object) {
        if (currentVersionJson.HasKey("latestVersion")) {
            if (currentVersionJson["latestVersion"].GetType() == Json::Type::String) {
                log("Your version is a string, setting it to an int by using the default 'currentInstall' in defaultData", LogLevel::Error, 50);
                MoveFileToPluginStorage("src/DefaultData/defaultInstalledVersion.json", pluginStorageVersionPath);
            }
        }
    }
}