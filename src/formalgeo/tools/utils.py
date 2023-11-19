import json
import os


def load_json(file_path_and_name):
    with open(file_path_and_name, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path_and_name):
    with open(file_path_and_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def safe_save_json(data, file_path_and_name):
    """Avoiding log file corruption."""
    path = os.path.dirname(file_path_and_name)
    filename = os.path.basename(file_path_and_name)
    file_path_and_name_bk = os.path.join(path, filename + ".bk")

    with open(file_path_and_name_bk, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if os.path.exists(file_path_and_name):
        os.remove(file_path_and_name)

    os.rename(file_path_and_name_bk, file_path_and_name)


def debug_print(debug, msg):
    """Print 'msg' when debug is True."""
    if debug:
        print(msg)


def rough_equal(a, b):
    """Accuracy is controlled at 0.001. Preventing floating point calculation issues"""
    return abs(a - b) < 0.001


def get_user_input(notes, choice=None):
    if choice is None:
        choice = ["y", "n"]
    notes = "{} ({}):".format(notes, "/".join(choice))
    user_input = input(notes)
    while user_input not in choice:
        user_input = input(notes)
    return user_input
