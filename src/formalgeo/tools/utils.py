import json
import os


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def safe_save_json(data, path, filename):
    """Avoiding log file corruption."""
    with open(path + filename + "_bk.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    try:
        os.remove(path + filename + ".json")
    except FileNotFoundError:
        pass

    os.rename(path + filename + "_bk.json", path + filename + ".json")


def debug_print(debug, msg):
    """Print 'msg' when debug=True."""
    if debug:
        print(msg)


def rough_equal(a, b):
    """Accuracy is controlled at 0.001. Preventing floating point calculation issues"""
    return abs(a - b) < 0.001
