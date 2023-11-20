from formalgeo.tools import load_json, save_json, get_user_input
import os
import requests
from tqdm import tqdm
import json
import tarfile
import shutil
import random
import warnings

remote = "https://raw.formalgeocontent.com/Formalgeo/Datasets/main/released/"


def get_datasets_path(datasets_path):
    if datasets_path is None:
        datasets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
    if not os.path.exists(datasets_path):
        os.makedirs(datasets_path)
    return datasets_path


def format_json(path_datasets):
    for path, _, files in os.walk(path_datasets):
        for file in files:
            if file.endswith(".json"):  # format json
                save_json(load_json(os.path.join(path, file)), os.path.join(path, file))


def get_remote_datasets():
    response = requests.get(os.path.join(remote, "released.json"))
    if response.status_code == 200:
        return json.loads(response.content)
    return None


def get_local_datasets(datasets_path):
    local_datasets = {}
    for file in os.listdir(datasets_path):
        if file.endswith(".json"):
            info = load_json(os.path.join(datasets_path, file))
            local_datasets[file.split(".")[0]] = info

    return local_datasets


def show_available_datasets(datasets_path=None):
    datasets_path = get_datasets_path(datasets_path)
    remote_datasets = get_remote_datasets()
    local_datasets = get_local_datasets(datasets_path)
    text = "{0:<15}{1:<15}{2:<15}{3:<15}{4:<15}{5:<15}{6:<22}{7:}"
    print(text.format("Location", "Name", "Version", "Formalgeo", "GDL", "GDL-Version", "Release", "Description"))

    if remote_datasets is None:
        for dataset in local_datasets:
            print(text.format("local",
                              local_datasets[dataset]["dataset_name"],
                              local_datasets[dataset]["dataset_version"],
                              local_datasets[dataset]["formalgeo_version"],
                              local_datasets[dataset]["gdl_name"],
                              local_datasets[dataset]["gdl_version"],
                              local_datasets[dataset]["release_datetime"],
                              local_datasets[dataset]["short_description"]))
        print("\nFailed to get the remote datasets, displaying local datasets.")
        print("Please check your network connection and try again.")
        return

    for dataset in local_datasets:
        if dataset in remote_datasets:
            if local_datasets[dataset]["release_datetime"] == remote_datasets[dataset]["release_datetime"]:
                dataset_name = "\033[32m{}\033[0m".format(local_datasets[dataset]["dataset_name"])
            else:
                dataset_name = "\033[33m{}\033[0m".format(local_datasets[dataset]["dataset_name"])
            print(text.format(dataset_name,
                              local_datasets[dataset]["dataset_version"],
                              local_datasets[dataset]["formalgeo_version"],
                              local_datasets[dataset]["gdl_name"],
                              local_datasets[dataset]["gdl_version"],
                              local_datasets[dataset]["release_datetime"],
                              local_datasets[dataset]["short_description"]))
            print(text.format(remote_datasets[dataset]["dataset_name"],
                              remote_datasets[dataset]["dataset_version"],
                              remote_datasets[dataset]["formalgeo_version"],
                              remote_datasets[dataset]["gdl_name"],
                              remote_datasets[dataset]["gdl_version"],
                              remote_datasets[dataset]["release_datetime"],
                              remote_datasets[dataset]["short_description"]))
        else:
            print(text.format("\033[34m{}\033[0m".format(local_datasets[dataset]["dataset_name"]),
                              local_datasets[dataset]["dataset_version"],
                              local_datasets[dataset]["formalgeo_version"],
                              local_datasets[dataset]["gdl_name"],
                              local_datasets[dataset]["gdl_version"],
                              local_datasets[dataset]["release_datetime"],
                              local_datasets[dataset]["short_description"]))

    for dataset in remote_datasets:
        if dataset not in local_datasets:
            print(text.format(remote_datasets[dataset]["dataset_name"],
                              remote_datasets[dataset]["dataset_version"],
                              remote_datasets[dataset]["formalgeo_version"],
                              remote_datasets[dataset]["gdl_name"],
                              remote_datasets[dataset]["gdl_version"],
                              remote_datasets[dataset]["release_datetime"],
                              remote_datasets[dataset]["short_description"]))

    print("\nColored dataset name representation of the locally downloaded dataset.")
    print("\033[32mGreen\033[0m indicates that the local version is in sync with the remote version.")
    print("\033[33mYellow\033[0m indicates the remote dataset has updates.")
    print("\033[34mBlue\033[0m represents the local dataset not in the remote repository.")
    print("White represents the remote dataset that can be downloaded.")
    print("Run 'formalgeo.data.download_dataset()' to download the remote dataset.")


def download_dataset(dataset_name, datasets_path=None):
    datasets_path = get_datasets_path(datasets_path)
    remote_datasets = get_remote_datasets()
    local_datasets = get_local_datasets(datasets_path)

    if remote_datasets is None:
        msg = "Network error. Fail to get remote datasets lists."
        raise Exception(msg)

    if dataset_name not in remote_datasets:
        msg = "No dataset named '{}'. run 'formalgeo.data.show_available_datasets()' for more info.".format(
            dataset_name)
        raise Exception(msg)

    if dataset_name in local_datasets:
        if local_datasets[dataset_name]["release_datetime"] == remote_datasets[dataset_name]["release_datetime"]:
            print("Datasets '{}' already exits in '{}'.".format(dataset_name, datasets_path))
            if get_user_input("Do you want to update?") == "n":
                return False
        remove_dataset(dataset_name, datasets_path)

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
        datasets_path = get_datasets_path(datasets_path)
        local_datasets = get_local_datasets(datasets_path)
        if dataset_name not in local_datasets:
            msg = "No dataset dir named '{}'. run 'formalgeo.data.show_available_datasets()' for more info.".format(
                dataset_name)
            raise Exception(msg)

        self.dataset_path = os.path.join(datasets_path, dataset_name)

        self.info = load_json(os.path.join(self.dataset_path, "info.json"))
        self.predicate_GDL = load_json(os.path.join(self.dataset_path, "gdl", "predicate_GDL.json"))
        self.theorem_GDL = load_json(os.path.join(self.dataset_path, "gdl", "theorem_GDL.json"))
        self.pid_mapping = self.load_file("pid_mapping.json")

    def show(self):
        for item in self.info:
            print("{}: {}".format(item, self.info[item]))
        print("dataset_path: {}".format(self.dataset_path))
        print("files: {}".format(os.listdir(os.path.join(self.dataset_path, "files"))))

    def get_problem(self, pid):
        if pid <= self.info["problem_number"]:
            return load_json(os.path.join(self.dataset_path, "problems", "{}.json".format(pid)))
        elif pid <= self.info["expanded_problem_number"]:
            raw_pid = self.pid_mapping[str(pid)]
            raw_problem = load_json(os.path.join(self.dataset_path, "problems", "{}.json".format(raw_pid)))
            expanded = load_json(os.path.join(self.dataset_path, "expanded", "{}.json".format(raw_pid)))[str(pid)]
            raw_problem["problem_id"] = expanded["problem_id"]
            raw_problem["text_cdl"] += expanded["added_cdl"]
            raw_problem["goal_cdl"] = expanded["goal_cdl"]
            raw_problem["problem_answer"] = expanded["problem_answer"]
            raw_problem["theorem_seqs"] = expanded["theorem_seqs"]
            raw_problem["theorem_seqs_dag"] = expanded["theorem_seqs_dag"]
            raw_problem["problem_level"] = len(expanded["theorem_seqs"])
            return raw_problem
        else:
            msg = "No problem named {}.".format(pid)
            raise Exception(msg)

    def get_problem_split(self, expanded=False):
        file_path = os.path.join(self.dataset_path, "files")
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
        file_path = os.path.join(self.dataset_path, "files")
        if filename not in os.listdir(file_path):
            msg = "No file named {} in {}.".format(filename, file_path)
            raise Exception(msg)

        if filename.endswith(".json"):
            return load_json(os.path.join(file_path, filename))
        else:
            with open(os.path.join(file_path, filename)) as f:
                return f.read()
