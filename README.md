# FormalGeo

[![Version](https://img.shields.io/badge/Version-0.0.6-brightgreen)](https://github.com/FormalGeo/FormalGeo)
[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)
[![Survey](https://img.shields.io/badge/Survey-FormalGeo-blue)](https://github.com/FormalGeo/FormalGeo)

Formal representation and solving for Euclidean plane geometry problems. Our goal is to build a crucial bridge between
IMO-level plane geometry challenges and readable AI automated reasoning.  
More information about FormalGeo will be found in [homepage](https://formalgeo.github.io/). FormalGeo is in its early
stages and brimming with potential. We welcome anyone to join us in this exciting endeavor.

## Installation

**For users:**  
We recommend using Conda to manage Python development environments. FormalGeo has been uploaded to PyPi, allowing for
easy installation via the `pip` command.

    $ conda create -n <your_env_name> python=3.10
    $ conda activate <your_env_name>
    $ pip install formalgeo

**For developers:**  
This project uses [pyproject.toml](https://packaging.python.org/en/latest/specifications/declaring-project-metadata) to
store project metadata. The command `pip install -e .` reads file `pyproject.toml`, automatically installs project
dependencies, and installs the current project in an editable mode into the environment's library. It is convenient for
project development and testing.

    $ git clone --depth 1 https://github.com/FormalGeo/FormalGeo.git
    $ cd FormalGeo
    $ conda create -n <your_env_name> python=3.10
    $ conda activate <your_env_name>
    $ pip install -e .

## Documentation and Usage

Everything is at [doc](./doc/doc.md). You can gain a deeper understanding of the **Geometry Formalization Theory**
by reading the [original paper](https://arxiv.org/abs/2310.18021) of FormalGeo.  
If you don't want to read `doc`, here is a short usage, start Python and:

    >>> from formalgeo.data import download_dataset, DatasetLoader
    >>> from formalgeo.solver import Interactor
    >>> from formalgeo.parse import parse_theorem_seqs

The `DatasetLoader` is used for dataset management, the `Interactor` act as an interactive solver. Download and load
dataset `formalgeo7k_v1`.

    >>> download_dataset(dataset_name="formalgeo7k_v1", datasets_path="path/to/your/datasets")
    >>> dl = DatasetLoader(dataset_name="formalgeo7k_v1", datasets_path="path/to/your/datasets")

Initialize the solver, load the problems, and apply the annotated sequence of theorems for solving:

    >>> solver = Interactor(dl.predicate_GDL, dl.theorem_GDL)
    >>> problem_CDL = dl.get_problem(pid=1)
    >>> solver.load_problem(problem_CDL)
    >>> for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]): solver.apply_theorem(t_name, t_branch, t_para)
    >>> solver.problem.check_goal()

Print the problem-solving process:

    >>> from formalgeo.tools import show_solution
    >>> show_solution(solver.problem)

## Available Datasets

### FormalGeo7K-v2

**Download:** `download_dataset(dataset_name="formalgeo7k_v2", datasets_path="path/to/your/datasets")`  
**Release Datetime:** 2024-11-12 11:33:23  
**Description:** 7000 SAT-level geometry problems with complete natural language description, geometric shapes, formal
language annotations, and theorem sequences annotations. On the basis of version v1, we have redrawn the geometric
images using Geogebra, standardized the style of natural language descriptions for the problems, added Chinese natural
language descriptions for the problems, and corrected annotation errors in some of the questions. We recommend using
this version.  
**Citation:** *Zhang, X., Zhu, N., Qin, C., Yang, L. I., Zeng, Z., & Leng, T. Formal Representation and Solution of
Plane Geometric Problems. In The 4th Workshop on Mathematical Reasoning and AI at NeurIPS'24.*

### FormalGeo7K

**Download:** `download_dataset(dataset_name="formalgeo7k_v1", datasets_path="path/to/your/datasets")`  
**Release Datetime:** 2023-11-08 13:01:26  
**Description:** We develop FormalGeo, a consistent geometry formal system based on rigorous geometry formalization
theory. We further construct the formalgeo7k dataset, which contains 6,981 geometric problems. All problems are
annotated with problem text, problem diagrams, formal descriptions, and solutions. This dataset can serve as a benchmark
for various tasks, such as geometric problem solving, geometric diagram parsing, geometric relation extraction,
geometric problem formalization and the evaluation of LLMs reasoning abilities.  
**Citation:** *Zhang, X., Zhu, N., He, Y., Zou, J., Qin, C., Li, Y., & Leng, T. (2024). FGeo-SSS: A Search-Based
Symbolic Solver for Human-like Automated Geometric Reasoning. Symmetry, 16(4), 404.*

### FormalGeo-IMO

**Download:** `download_dataset(dataset_name="formalgeo-imo_v1", datasets_path="path/to/your/datasets")`  
**Release Datetime:** 2023-11-26 19:21:26  
**Description:** We have attempted to annotate 18 IMO-level geometric problems, sourced from carefully
selected International Olympiads, Chinese Olympiads, and others. During the annotation process, we discovered that
IMO-level problems require more efficient construction algorithms and a more comprehensive formalization system. A
larger and more comprehensive dataset will be published after these problems are solved.  
**Citation:** *Zhang, X., Zhu, N., He, Y., Zou, J., Qin, C., Li, Y., & Leng, T. (2024). FGeo-SSS: A Search-Based
Symbolic Solver for Human-like Automated Geometric Reasoning. Symmetry, 16(4), 404.*

## Contributing

We welcome contributions from anyone, even if you are new to open source. Please read our [Introduction to Contributing
page](./doc/contributing.md).

## Bugs

Our bug reporting platform is available at [here](https://github.com/FormalGeo/FormalGeo/issues). We encourage you to
report any issues you encounter. Or even better, fork our repository on GitHub and submit a pull request. We appreciate
contributions of all sizes and are happy to assist newcomers to git with their pull requests.

## Citation

To cite FormalGeo in publications use:
> Zhang, X., Zhu, N., He, Y., Zou, J., Huang, Q., Jin, X., ... & Leng, T. (2024). FormalGeo: An Extensible Formalized
> Framework for Olympiad Geometric Problem Solving

A BibTeX entry for LaTeX users is:
> @misc{arxiv2024formalgeo,  
> title={FormalGeo: An Extensible Formalized Framework for Olympiad Geometric Problem Solving},  
> author={Xiaokai Zhang and Na Zhu and Yiming He and Jia Zou and Qike Huang and Xiaoxiao Jin and Yanjun Guo and Chenyang
> Mao and Zhe Zhu and Dengfeng Yue and Fangzhen Zhu and Yang Li and Yifan Wang and Yiwen Huang and Runan Wang and Cheng
> Qin and Zhenbing Zeng and Shaorong Xie and Xiangfeng Luo and Tuo Leng},  
> year={2024},  
> eprint={2310.18021},  
> archivePrefix={arXiv},  
> primaryClass={cs.AI},  
> url={https://arxiv.org/abs/2310.18021}  
> }

FormalGeo is MIT licensed, so you are free to use it whatever you like, be it academic, commercial, creating forks or
derivatives, as long as you copy the MIT statement if you redistribute it (see the LICENSE file for details). That said,
if it is convenient for you, please cite FormalGeo when using it in your work.