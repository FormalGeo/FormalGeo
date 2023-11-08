import os
import requests
from tqdm import tqdm
import json
import tarfile
import shutil
from formalgeo.tools import load_json, save_json

remote = "https://raw.githubusercontent.com/BitSecret/FormalGeo-Datasets/main/released/"


def get_datasets_path(datasets_path):
    if datasets_path is None:
        datasets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
    if not os.path.exists(datasets_path):
        os.makedirs(datasets_path)
    return datasets_path


def get_user_input(notes):
    notes = "{} (y/n):".format(notes)
    user_input = input(notes)
    while user_input not in ["y", "n"]:
        user_input = input(notes)
    return user_input


def get_remote_datasets():
    url = os.path.join(remote, "released.json")
    response = requests.get(url)

    if response.status_code == 200:
        return json.loads(response.content)

    msg = "Network error. Fail to download '{}'.".format(url)
    raise Exception(msg)


def format_json(path_datasets):
    for path, _, files in os.walk(path_datasets):
        for file in files:
            if file.endswith(".json"):  # format json
                save_json(load_json(os.path.join(path, file)), os.path.join(path, file))


def get_local_datasets(datasets_path=None):
    datasets_path = get_datasets_path(datasets_path)
    local_datasets = {}
    for file in os.listdir(datasets_path):
        if file.endswith(".json"):
            info = load_json(os.path.join(datasets_path, file))
            local_datasets[file.split(".")[0]] = {
                "name": info["name"],
                "version": info["version"],
                "formalgeo_version": info["formalgeo_version"],
                "gdl": info["gdl"],
                "gdl_version": info["gdl_version"],
                "release_datetime": info["release_datetime"],
                "short_desc": info["short_desc"],
            }

    return local_datasets


def show_available_datasets(datasets_path=None):
    datasets_path = get_datasets_path(datasets_path)
    remote_datasets = get_remote_datasets()
    local_datasets = get_local_datasets(datasets_path)

    for dataset in local_datasets:
        if dataset in remote_datasets:
            if local_datasets[dataset]["release_datetime"] == remote_datasets[dataset]["release_datetime"]:
                name = "\033[32m{}\033[0m".format(local_datasets[dataset]["name"])
            else:
                name = "\033[33m{}\033[0m".format(local_datasets[dataset]["name"])
        else:
            name = "\033[34m{}\033[0m".format(local_datasets[dataset]["name"])
        print("{0:^3}{1:<20}{2:<20}{3:<20}{4:<20}{5:<20}{6:}".format(
            name,
            local_datasets[dataset]["version"],
            local_datasets[dataset]["formalgeo"],
            local_datasets[dataset]["gdl"],
            local_datasets[dataset]["gdl_version"],
            local_datasets[dataset]["release_datetime"],
            local_datasets[dataset]["short_desc"],
        ))

    for dataset in remote_datasets:
        if dataset not in local_datasets:
            print("{0:^3}{1:<20}{2:<20}{3:<20}{4:<20}{5:<20}{6:}".format(
                remote_datasets[dataset]["name"],
                remote_datasets[dataset]["version"],
                remote_datasets[dataset]["formalgeo"],
                remote_datasets[dataset]["gdl"],
                remote_datasets[dataset]["gdl_version"],
                remote_datasets[dataset]["release_datetime"],
                remote_datasets[dataset]["short_desc"],
            ))


def download_dataset(dataset_name, datasets_path=None):
    datasets_path = get_datasets_path(datasets_path)
    remote_datasets = get_remote_datasets()
    local_datasets = get_local_datasets(datasets_path)

    if dataset_name not in remote_datasets:
        msg = "No dataset named '{}', run <show_available_datasets> for more info.".format(dataset_name)
        raise Exception(msg)

    if dataset_name in local_datasets:
        if local_datasets[dataset_name]["release_datetime"] == remote_datasets[dataset_name]["release_datetime"]:
            print("Datasets '{}' already exits in '{}'.".format(dataset_name, datasets_path))
            if get_user_input("Do you want to update?") == "n":
                return False
        remote_datasets(dataset_name, datasets_path)

    response = requests.get(os.path.join(remote, "{}.tar.gz".format(dataset_name)), stream=True)
    if response.status_code == 200:
        pbar = tqdm(
            total=int(response.headers.get('content-length', 0)),
            unit='iB',
            unit_scale=True,
            desc="Download dataset '{}'".format(dataset_name)
        )
        with open(os.path.join(datasets_path, "{}.tar.gz".format(dataset_name)), "wb") as file:
            for data in response.iter_content(1024):  # block_size = 1024
                pbar.update(len(data))
                file.write(data)
        pbar.close()

        print("Extracting files ...")
        with tarfile.open(os.path.join(datasets_path, "{}.tar.gz".format(dataset_name)), "r:gz") as tar_file:  # extract
            tar_file.extractall(os.path.join(datasets_path, dataset_name))

        format_json(os.path.join(datasets_path, dataset_name))

        shutil.copy(os.path.join(datasets_path, dataset_name, "info.json"),
                    os.path.join(datasets_path, "{}.json".format(dataset_name)))

        os.remove(os.path.join(datasets_path, "{}.tar.7z".format(dataset_name)))

        return True

    msg = "Network error. Fail to download '{}'.".format(
        os.path.join(remote, os.path.join(remote, "{}.tar.gz".format(dataset_name))))
    raise Exception(msg)


def remove_dataset(dataset_name, datasets_path=None):
    datasets_path = get_datasets_path(datasets_path)
    local_datasets = get_local_datasets(datasets_path)

    if dataset_name not in local_datasets:
        print("No dataset '{}' in '{}'. please check your inputs.".format(dataset_name, datasets_path))
        return

    print("Removing dataset '{}'...".format(dataset_name))
    if os.path.isdir(os.path.join(datasets_path, dataset_name)):
        shutil.rmtree(os.path.join(datasets_path, dataset_name), ignore_errors=True)


class DatasetLoader:

    def __init__(self, dataset_name, datasets_path=None):
        self.datasets_path = get_datasets_path(datasets_path)
        remote_datasets = get_remote_datasets()
        local_datasets = get_local_datasets(self.datasets_path)

        if dataset_name in local_datasets:
            if dataset_name in remote_datasets:
                if (local_datasets[dataset_name]["release_datetime"]
                        != remote_datasets[dataset_name]["release_datetime"]):
                    if get_user_input("The dataset can update, Dd you want to update?") == "y":
                        download_dataset(dataset_name, self.datasets_path)
        else:
            if dataset_name in remote_datasets:
                download_dataset(dataset_name, self.datasets_path)
            else:
                msg = "No dataset named '{}', run <get_available_datasets> for more info.".format(dataset_name)
                raise Exception(msg)

        self.info = load_json(os.path.join(self.datasets_path, "info.json"))
        self.predicate_GDL = load_json(os.path.join(self.datasets_path, "gdl", "predicate_GDL.json"))
        self.theorem_GDL = load_json(os.path.join(self.datasets_path, "gdl", "theorem_GDL.json"))
        self.pid_mapping = load_json(os.path.join(self.datasets_path, "files", "pid_mapping.json"))

    def show(self):
        pass

    def get_problem(self, pid):
        pass

    def get_expanded_problem(self, pid):
        # raw_problem = copy.copy(raw_problem)
        # raw_problem["problem_id"] = aug_problem["problem_id"]
        # raw_problem["text_cdl"] += aug_problem["added_cdl"]
        # raw_problem["goal_cdl"] = aug_problem["goal_cdl"]
        # raw_problem["problem_answer"] = aug_problem["problem_answer"]
        # raw_problem["theorem_seqs"] = copy.copy(aug_problem["theorem_seqs"])
        pass


if __name__ == '__main__':
    show_available_datasets()
    download_dataset("formalgeo7k-v1")
