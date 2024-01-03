# FormalGeo

[![Version](https://img.shields.io/badge/Version-0.0.3-brightgreen)](https://github.com/FormalGeo/FormalGeo)
[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)
[![Survey](https://img.shields.io/badge/Survey-FormalGeo-blue)](https://github.com/FormalGeo/FormalGeo)

This is a simple guide to using FormalGeo. Here, you will quickly learn about FormalGeo's usage methods and code
structure. The document is not perfect due to time constraints and a shortage of manpower. For a deeper understanding of
FormalGeo, please read the source code.  
More information about FormalGeo will be found in [homepage](https://formalgeo.github.io/). FormalGeo is in its early
stages and brimming with potential. We welcome anyone to join us in this exciting endeavor.

## Introduction

FormalGeo is a formal plane geometry problem solver based
on [geometry formalization theory](https://arxiv.org/abs/2310.18021). It can operate in both interactive and automated
modes, accepting formalized geometric problem inputs and outputting structured problem-solving processes.

## Installation

We recommend using Conda to manage Python development environments. FormalGeo has been uploaded to PyPi, allowing for
easy installation via the `pip` command.

    $ conda create -n <your_env_name> python=3.10
    $ conda activate <your_env_name>
    $ pip install formalgeo

## Quick Start

FormalGeo uses the json format to define the geometric formal system and input descriptions for geometric problems. The
solver requires two types of json files: GDL for personalizing the formal system and CDL for describing geometric
problems.  
**GDL** (Geometric definition language) includes predicate GDL and theorem GDL. Before solving the problem, the GDL is
input into the solver to configure the formalization system of the solver.  
**CDL** (Condition Declaration Language) is used for the description of geometric problems (problem known conditions and
problem goal).  
FormalGeo use the _data_ module to manage datasets and access the GDL and CDL that have already been defined in the
dataset. These datasets are uniformly managed in the [Datasets](https://github.com/FormalGeo/Datasets) and you can use
the function `formalgeo.data.show_available_datasets()` to retrieve all available datasets. Taking the `formalgeo7k_v1`
dataset as an example, we introduce the use of common methods in FormalGeo.  
Download dataset and load dataset (only needs to be downloaded once):

    >>> from formalgeo.data import download_dataset, DatasetLoader
    >>> download_dataset(dataset_name="formalgeo7k_v1", datasets_path="F:/datasets")
    >>> dl = DatasetLoader(dataset_name="formalgeo7k_v1", datasets_path="F:/datasets")

Get GDL and CDL:

    >>> predicate_GDL = dl.predicate_GDL
    >>> theorem_GDL = dl.theorem_GDL
    >>> problem_CDL = dl.get_problem(pid=1)

Initialize the solver and load the formal system and the problem:

    >>> from formalgeo.solver import Interactor
    >>> solver = Interactor(predicate_GDL, theorem_GDL)
    >>> solver.load_problem(problem_CDL)

Apply theorems to solve the problem. We use the annotated theorem sequence. You can also modify the code
to `t_name, t_branch, t_para = parse_one_theorem(input("input theorem:"))`, to read user input in real-time and return
the results of the theorem execution.

    >>> from formalgeo.parse import parse_theorem_seqs
    >>> for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]): solver.apply_theorem(t_name, t_branch, t_para)
    >>> solver.problem.check_goal()

Print the problem-solving process:

    >>> from formalgeo.tools import show_solution
    >>> show_solution(solver.problem)

The problem-solving process is represented as a hypertree with conditions as hypernodes and theorems as hyperedges,
which you can save as JSON file:

    >>> from formalgeo.tools import save_json, get_solution_hypertree
    >>> save_json(get_solution_hypertree(solver.problem), "1_hypertree.json")

The above is the simplest usage process. If you want to input your own problems or define your own formal system, you
can save the formalized description of the problem in json format and then load it into the program.

    >>> from formalgeo.tools import load_json
    >>> problem_CDL = load_json("your_json_file_path")

You can use Python's json module to view the structure of GDL and CDL. You can also directly view the json files in the
dataset. The GDL files are located at `your_datasets_path/formalgeo7k/gdl`, and the CDL files are located
at `your_datasets_path/formalgeo7k/problems`.

    >>> print(json.dumps(predicate_GDL, indent=2))
    >>> print(json.dumps(theorem_GDL, indent=2))
    >>> print(json.dumps(problem_CDL, indent=2))

For more on how to use these methods, refer to the next chapter.

## API Reference

FormalGeo contains 6 modules, namely core, data, parse, problem, solver and tools.  
`core` is the core of the solver, execute GPL and implement backtrackable and interpretable geometric relation reasoning
and algebraic equation solving.  
`data` is the dataset management module, used for downloading, managing, and utilizing datasets.  
`parse` is the formal language parsing and inverse parsing module, establishing a bridge between natural language,
formal language, and solver language.  
`problem` is a module for geometric problem classes, storing geometric problem conditions and the problem-solving
process during solver operation.  
`solver` defines the solver's operational logic, invoking the `core` and `problem` modules to implement interactive
problem solving and automatic problem solving based on search.  
`tools` provide some tools, such as displaying the problem-solving process.

### core

coming soon...

### data

coming soon...

### parse

coming soon...

### problem

coming soon...

### solver

coming soon...

### tools

coming soon...