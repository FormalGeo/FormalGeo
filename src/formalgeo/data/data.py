from formalgeo.tools import load_json, save_json, get_user_input
import os
import requests
from tqdm import tqdm
import json
import tarfile
import shutil
import random


def get_remote_datasets():
    response = requests.get("https://raw.githubusercontent.com/FormalGeo/FormalGeo/main/datasets.json")
    if response.status_code == 200:
        return json.loads(response.content)
    return None


def get_local_datasets(datasets_path):
    if not os.path.exists(datasets_path):
        os.makedirs(datasets_path)

    local_datasets = {}
    for file in os.listdir(datasets_path):
        if file.endswith(".json"):
            info = load_json(f"{datasets_path}/{file}")
            local_datasets[file.split(".")[0]] = info

    return local_datasets


def show_available_datasets(datasets_path):
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


def download_dataset(dataset_name, datasets_path):
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
        with open(f"{datasets_path}/{dataset_name}.tar.gz", "wb") as file:
            for data in response.iter_content(1024):  # block_size = 1024
                pbar.update(len(data))
                file.write(data)
        pbar.close()

        print("Extracting files ...")
        with tarfile.open(f"{datasets_path}/{dataset_name}.tar.gz", "r:gz") as tar_file:  # extract
            tar_file.extractall(f"{datasets_path}/{dataset_name}")

        shutil.copy(f"{datasets_path}/{dataset_name}/info.json", f"{datasets_path}/{dataset_name}.json")

        return True

    raise Exception("Network error. Fail to download '{}'.".format(remote_datasets[dataset_name]["downloads"]))


def remove_dataset(dataset_name, datasets_path):
    local_datasets = get_local_datasets(datasets_path)

    if dataset_name not in local_datasets:
        print("No dataset '{}' in '{}'. please check your inputs.".format(dataset_name, datasets_path))
        return

    print("Removing dataset '{}'...".format(dataset_name))
    if os.path.isdir(f"{datasets_path}/{dataset_name}"):
        shutil.rmtree(f"{datasets_path}/{dataset_name}", ignore_errors=True)
        os.remove(f"{datasets_path}/{dataset_name}.tar.gz")
        os.remove(f"{datasets_path}/{dataset_name}.json")


class DatasetLoader:

    def __init__(self, dataset_name, datasets_path):
        local_datasets = get_local_datasets(datasets_path)
        if dataset_name not in local_datasets:
            msg = "No dataset named '{}'. run 'formalgeo.data.show_available_datasets()' for more info.".format(
                dataset_name)
            raise Exception(msg)

        self.dataset_path = f"{datasets_path}/{dataset_name}"

        self.info = load_json(f"{self.dataset_path}/info.json")
        self.predicate_GDL = load_json(f"{self.dataset_path}/gdl/predicate_GDL.json")
        self.theorem_GDL = load_json(f"{self.dataset_path}/gdl/theorem_GDL.json")

    def show(self):
        for item in self.info:
            print("{}: {}".format(item, self.info[item]))
        print(f"dataset_path: {self.dataset_path}")
        files = os.listdir(f"{self.dataset_path}/files")
        print(f"files: {files}")

    def get_problem(self, pid):
        if pid <= self.info["problem_number"]:
            return load_json(f"{self.dataset_path}/problems/{pid}.json")
        else:
            msg = "No problem named {}.".format(pid)
            raise Exception(msg)


if __name__ == '__main__':
    show_available_datasets("D:/Projects/released")
    # download_dataset("formalgeo7k_v2", "D:/Projects/released")
    # remove_dataset("formalgeo7k_v2", "D:/Projects/released")
