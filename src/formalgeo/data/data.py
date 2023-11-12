from formalgeo.tools import load_json, save_json
import os
import requests
from tqdm import tqdm
import json
import tarfile
import shutil
import random

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
        self.pid_mapping = self.load_file("pid_mapping.json")

    def show(self):
        for item in self.info:
            print("{}: {}".format(item, self.info[item]))
        print("dataset_path: {}".format(self.datasets_path))
        print("files: {}".format(os.listdir(os.path.join(self.datasets_path, "files"))))

    def get_problem(self, pid):
        if pid <= self.info["problem_number"]:
            return load_json(os.path.join(self.datasets_path, "problems", "{}.json".format(pid)))
        elif pid <= self.info["expanded_problem_number"]:
            raw_pid = self.pid_mapping[pid]
            raw_problem = load_json(os.path.join(self.datasets_path, "problems", "{}.json".format(raw_pid)))
            expanded = load_json(os.path.join(self.datasets_path, "expanded", "{}.json".format(raw_pid)))[str(pid)]
            raw_problem["problem_id"] = expanded["problem_id"]
            raw_problem["text_cdl"] += expanded["added_cdl"]
            raw_problem["goal_cdl"] = expanded["goal_cdl"]
            raw_problem["problem_answer"] = expanded["problem_answer"]
            raw_problem["theorem_seqs"] = expanded["theorem_seqs"]
            raw_problem["problem_level"] = len(expanded["theorem_seqs"])
            return raw_problem
        else:
            msg = "No problem named {}.".format(pid)
            raise Exception(msg)

    def get_problem_split(self, expanded=False):
        file_path = os.path.join(self.datasets_path, "files")
        if expanded:
            split_msg = self.info["expanded_problem_split"]
            filename = "expanded_problem_split_{}_{}_{}_{}.json".format(
                split_msg[0], split_msg[1], split_msg[2], split_msg[3]
            )
            problem_number = self.info["expanded_problem_number"]
        else:
            split_msg = self.info["problem_split"]
            filename = "problem_split_{}_{}_{}_{}.json".format(
                split_msg[0], split_msg[1], split_msg[2], split_msg[3]
            )
            problem_number = self.info["problem_number"]

        if filename in os.listdir(file_path):
            return load_json(os.path.join(file_path, filename))

        total = split_msg[0] + split_msg[1] + split_msg[2]
        random.seed(split_msg[3])
        data = list(range(1, problem_number + 1))
        test = sorted(random.sample(data, int(problem_number * split_msg[2] / total)))
        for i in range(len(data))[::-1]:
            if data[i] in test:
                data.pop(i)
        val = sorted(random.sample(data, int(problem_number * split_msg[1] / total)))
        for i in range(len(data))[::-1]:
            if data[i] in val:
                data.pop(i)
        train = data

        total = len(train) + len(val) + len(test)

        data = {
            "msg": {
                "total": total,
                "train": len(train),
                "val": len(val),
                "test": len(test)
            },
            "split": {
                "train": train,
                "val": val,
                "test": test
            }
        }

        save_json(data, os.path.join(file_path, filename))

        return data

    def load_file(self, filename):
        file_path = os.path.join(self.datasets_path, "files")
        if filename not in os.listdir(file_path):
            msg = "No file named {} in {}.".format(filename, file_path)
            raise Exception(msg)

        if filename.endswith(".json"):
            return load_json(os.path.join(file_path, filename))
        else:
            with open(os.path.join(file_path, filename)) as f:
                return f.read()


if __name__ == '__main__':
    show_available_datasets()
