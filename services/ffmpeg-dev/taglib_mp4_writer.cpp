#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <map>
#include <set>
#include <string>

#include <taglib/mp4file.h>
#include <taglib/tpropertymap.h>
#include <taglib/tstring.h>
#include <taglib/tstringlist.h>

namespace fs = std::filesystem;

static bool is_inside_output_dir(const fs::path &path) {
    const fs::path root = fs::canonical("/data/current/output");
    const fs::path target = fs::canonical(path);
    const fs::path relative = target.lexically_relative(root);
    return !relative.empty() && relative.native().rfind("..", 0) != 0;
}

static std::string lower_ext(fs::path path) {
    std::string ext = path.extension().string();
    std::transform(ext.begin(), ext.end(), ext.begin(), [](unsigned char c) { return std::tolower(c); });
    return ext;
}

static void set_property(TagLib::PropertyMap &properties, const char *key, const std::string &value) {
    if (!value.empty()) {
        properties[key] = TagLib::StringList(TagLib::String(value, TagLib::String::UTF8));
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        std::cerr << "usage: taglib-mp4-writer /data/current/output/file.mp4 [--title value] [--artist value] [--genre value] [--publisher value] [--language value] [--description value]\n";
        return 2;
    }

    const fs::path output_path(argv[1]);
    if (lower_ext(output_path) != ".mp4") {
        std::cerr << "taglib-mp4-writer only writes MP4 files\n";
        return 2;
    }

    try {
        if (!is_inside_output_dir(output_path)) {
            std::cerr << "refusing to write metadata outside /data/current/output\n";
            return 2;
        }
    } catch (const std::exception &e) {
        std::cerr << "metadata path check failed: " << e.what() << "\n";
        return 2;
    }

    const std::set<std::string> allowed_flags = {
        "--title",
        "--artist",
        "--genre",
        "--publisher",
        "--language",
        "--description",
    };
    std::map<std::string, std::string> values;

    for (int i = 2; i < argc; i += 2) {
        const std::string flag(argv[i]);
        if (allowed_flags.find(flag) == allowed_flags.end()) {
            std::cerr << "unsupported metadata flag: " << flag << "\n";
            return 2;
        }
        if (i + 1 >= argc) {
            std::cerr << "missing value for metadata flag: " << flag << "\n";
            return 2;
        }
        values[flag] = argv[i + 1];
    }

    TagLib::MP4::File file(output_path.c_str());
    if (!file.isValid()) {
        std::cerr << "failed to open MP4 file with TagLib\n";
        return 1;
    }

    TagLib::PropertyMap properties = file.properties();
    set_property(properties, "TITLE", values["--title"]);
    set_property(properties, "ARTIST", values["--artist"]);
    set_property(properties, "GENRE", values["--genre"]);
    set_property(properties, "PUBLISHER", values["--publisher"]);
    set_property(properties, "LANGUAGE", values["--language"]);
    file.setProperties(properties);

    if (!file.save()) {
        std::cerr << "failed to save MP4 metadata with TagLib\n";
        return 1;
    }

    return 0;
}
