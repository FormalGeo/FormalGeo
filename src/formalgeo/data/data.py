import os
import copy
import requests
from tqdm import tqdm
import json
import tarfile
import shutil

remote = "https://raw.githubusercontent.com/BitSecret/FormalGeo-Datasets/main/released/"


def get_available_datasets(show=True):
    url = os.path.join(remote, "datasets.json")
    response = requests.get(url)

    if response.status_code == 200:
        datasets = json.loads(response.content)
        if not show:
            return datasets
        print("name\tversion\tformalgeo\tgdl\tgdl-version")
        for d in datasets:
            print("{}\t{}\t{}\t{}\t{}".format(
                datasets[d]["name"], datasets[d]["version"], datasets[d]["formalgeo"],
                datasets[d]["gdl"], datasets[d]["gdl-version"])
            )
        return datasets

    msg = "Network error. Fail to download '{}'.".format(url)
    raise Exception(msg)


def download_dataset(name, version, datasets_path=None):
    datasets = get_available_datasets(show=False)
    filename = "{}-{}.tar.gz".format(name, version)

    if filename not in datasets:
        msg = "No dataset named '{}-{}', run <get_available_datasets> for more info.".format(name, version)
        raise Exception(msg)

    if datasets_path is None:
        datasets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
    if not os.path.exists(datasets_path):
        os.makedirs(datasets_path)

    if filename in os.listdir(datasets_path):
        print("Datasets '{}-{}' already exits in '{}'.".format(name, version, datasets_path))
        user_input = input("Do you want to update? (y/n):")
        while user_input not in ["y", "n"]:
            user_input = input("Do you want to update? (y/n):")
        if user_input == "n":
            return False

    response = requests.get(os.path.join(remote, filename), stream=True)
    if response.status_code == 200:
        pbar = tqdm(
            total=int(response.headers.get('content-length', 0)),
            unit='iB',
            unit_scale=True,
            desc="Download [{}-{}]".format(name, version)
        )
        with open(os.path.join(datasets_path, filename), "wb") as file:
            for data in response.iter_content(1024):  # block_size = 1024
                pbar.update(len(data))
                file.write(data)
        pbar.close()

        with tarfile.open(os.path.join(datasets_path, filename), "r:gz") as tar_file:  # extract
            tar_file.extractall(os.path.join(datasets_path, '{}-{}'.format(name, version)))

        return True

    msg = "Network error. Fail to download '{}'.".format(os.path.join(remote, filename))
    raise Exception(msg)


def remove_dataset(name, version, datasets_path=None):
    filename = "{}-{}.tar.gz".format(name, version)

    if datasets_path is None:
        datasets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
    if not os.path.exists(datasets_path):
        os.makedirs(datasets_path)

    if filename not in os.listdir(datasets_path):
        print("No file dataset '{}-{}' in '{}'. please check your dataset name and version.".format(
            name, version, datasets_path))
        return False

    user_input = input("Do you want to remove datasets '{}-{}'? (y/n):".format(name, version))
    while user_input not in ["y", "n"]:
        user_input = input("Do you want to remove datasets '{}-{}'? (y/n):".format(name, version))
    if user_input == "n":
        return False

    if os.path.isfile(os.path.join(datasets_path, filename)):
        os.remove(os.path.join(datasets_path, filename))
    if os.path.isdir(os.path.join(datasets_path, '{}-{}'.format(name, version))):
        shutil.rmtree(os.path.join(datasets_path, '{}-{}'.format(name, version)), ignore_errors=True)

    return True


def format_json(path_datasets):
    pass

class DatasetLoader:

    def __init__(self, name, version, use_augmented=False, datasets_path=None):
        self.name = name
        self.version = version
        datasets = get_available_datasets(show=False)
        filename = "{}-{}.tar.gz".format(name, version)
        if filename not in datasets:
            msg = "No dataset named '{}-{}', run <get_available_datasets> for more info.".format(name, version)
            raise Exception(msg)

        self.use_augmented = use_augmented
        self.datasets_path = datasets_path
        if self.datasets_path is None:
            self.datasets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
        if not os.path.exists(self.datasets_path):
            os.makedirs(self.datasets_path)

        if filename not in os.listdir(self.datasets_path):
            download_dataset(self.name, self.version, self.datasets_path)

    def show_dataset_info(self):
        pass

    def get_predicate_gdl(self):
        pass

    def get_theorem_gdl(self):
        pass

    def get_problem(self, pid):
        pass

    @staticmethod
    def assemble(raw_problem, aug_problem):
        raw_problem = copy.copy(raw_problem)
        raw_problem["problem_id"] = aug_problem["problem_id"]
        raw_problem["text_cdl"] += aug_problem["added_cdl"]
        raw_problem["goal_cdl"] = aug_problem["goal_cdl"]
        raw_problem["problem_answer"] = aug_problem["problem_answer"]
        raw_problem["theorem_seqs"] = copy.copy(aug_problem["theorem_seqs"])
        return raw_problem
