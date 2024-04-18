from formalgeo.tools import load_json, save_json, get_user_input
import os
import requests
from tqdm import tqdm
import json
import tarfile
import shutil
import random


def get_datasets_path(datasets_path):
    if datasets_path is None:
        datasets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
    if not os.path.exists(datasets_path):
        os.makedirs(datasets_path)
    return datasets_path


def get_remote_datasets():
    response = requests.get("https://raw.githubusercontent.com/FormalGeo/Datasets/main/released.json")
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
    text = "{0:<12}{1:<10}{2:<20}{3:<15}{4:<15}{5:<15}{6:<22}{7:}"
    print(text.format("Location", "Status", "Name", "Formalgeo", "GDL", "GDL-Version", "Release",
                      "Description"))

    if remote_datasets is None:
        for dataset in local_datasets:
            print(text.format("local", "-",
                              dataset,
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
                status = "latest"
            else:
                status = "old"
            print(text.format("local", status,
                              dataset,
                              local_datasets[dataset]["formalgeo_version"],
                              local_datasets[dataset]["gdl_name"],
                              local_datasets[dataset]["gdl_version"],
                              local_datasets[dataset]["release_datetime"],
                              local_datasets[dataset]["short_description"]))
        else:
            print(text.format("local", "-",
                              dataset,
                              local_datasets[dataset]["formalgeo_version"],
                              local_datasets[dataset]["gdl_name"],
                              local_datasets[dataset]["gdl_version"],
                              local_datasets[dataset]["release_datetime"],
                              local_datasets[dataset]["short_description"]))

    for dataset in remote_datasets:
        print(text.format("remote", "-",
                          dataset,
                          remote_datasets[dataset]["formalgeo_version"],
                          remote_datasets[dataset]["gdl_name"],
                          remote_datasets[dataset]["gdl_version"],
                          remote_datasets[dataset]["release_datetime"],
                          remote_datasets[dataset]["short_description"]))

    print()
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

    response = requests.get(remote_datasets[dataset_name]["downloads"], stream=True)
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

        shutil.copy(os.path.join(datasets_path, dataset_name, "info.json"),
                    os.path.join(datasets_path, "{}.json".format(dataset_name)))

        os.remove(os.path.join(datasets_path, "{}.tar.gz".format(dataset_name)))

        return True

    raise Exception("Network error. Fail to download '{}'.".format(remote_datasets[dataset_name]["downloads"]))


def remove_dataset(dataset_name, datasets_path=None):
    datasets_path = get_datasets_path(datasets_path)
    local_datasets = get_local_datasets(datasets_path)

    if dataset_name not in local_datasets:
        print("No dataset '{}' in '{}'. please check your inputs.".format(dataset_name, datasets_path))
        return

    print("Removing dataset '{}'...".format(dataset_name))
    if os.path.isdir(os.path.join(datasets_path, dataset_name)):
        shutil.rmtree(os.path.join(datasets_path, dataset_name), ignore_errors=True)  # json文件也要移除吧
        os.remove(os.path.join(datasets_path, f"{dataset_name}.json"))


class DatasetLoader:

    def __init__(self, dataset_name, datasets_path=None):
        datasets_path = get_datasets_path(datasets_path)
        local_datasets = get_local_datasets(datasets_path)
        if dataset_name not in local_datasets:
            msg = "No dataset named '{}'. run 'formalgeo.data.show_available_datasets()' for more info.".format(
                dataset_name)
            raise Exception(msg)

        self.dataset_path = os.path.join(datasets_path, dataset_name)

        self.info = load_json(os.path.join(self.dataset_path, "info.json"))
        self.predicate_GDL = load_json(os.path.join(self.dataset_path, "gdl", "predicate_GDL.json"))
        self.theorem_GDL = load_json(os.path.join(self.dataset_path, "gdl", "theorem_GDL.json"))

    def show(self):
        for item in self.info:
            print("{}: {}".format(item, self.info[item]))
        print("dataset_path: {}".format(self.dataset_path))
        print("files: {}".format(os.listdir(os.path.join(self.dataset_path, "files"))))

    def get_problem(self, pid):
        if pid <= self.info["problem_number"]:
            return load_json(os.path.join(self.dataset_path, "problems", f"{pid}.json"))
        else:
            msg = "No problem named {}.".format(pid)
            raise Exception(msg)

    def get_problem_split(self, split_msg=None):
        file_path = os.path.join(self.dataset_path, "files")

        if split_msg is None:
            split_msg = self.info["problem_split"]

        filename = f"problem_split_{split_msg[0]}_{split_msg[1]}_{split_msg[2]}_{split_msg[3]}.json"
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
                "train": len(train),
                "val": len(val),
                "test": len(test),
                "total": total
            },
            "split": {
                "train": train,
                "val": val,
                "test": test
            }
        }

        save_json(data, os.path.join(file_path, filename))

        return data


if __name__ == '__main__':
    show_available_datasets("D:/Projects/dataset")
    # download_dataset("formalgeo7k_v1", "D:/Projects/dataset")
    # remove_dataset("formalgeo7k_v1", "D:/Projects/dataset")
