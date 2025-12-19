# FormalGeo

[![Version](https://img.shields.io/badge/Version-2.0.1-brightgreen)](https://github.com/FormalGeo/FormalGeo)
[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)
[![Survey](https://img.shields.io/badge/Survey-FormalGeo-blue)](https://github.com/FormalGeo/FormalGeo)

Formal representation and solving for Euclidean plane geometry problems. Our goal is to build a crucial bridge between
IMO-level plane geometry challenges and readable AI automated reasoning. More information about FormalGeo will be found
in [homepage](https://formalgeo.github.io/).

Older versions before 2.0.1, which we refer to as alpha versions, have been unmaintained since December 1, 2025. If you
still wish to access the alpha version code, you can check out the alpha branch. The new beta version is scheduled to be
released by March 1, 2026. Compared to the alpha version, the beta version enables shape construction and a unified
bidirectional reasoning process.

The released open-source datasets can be found in the `datasets.json` file. If you use these datasets, please cite them 
properly according to the Citation requirements.

## Installation

**For users:**  
We recommend using Conda to manage Python development environments. FormalGeo has been deployed to PyPi, allowing for
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

## Usage

You can gain a deeper understanding of the **Geometry Formalization Theory** by reading the 
[paper](https://arxiv.org/abs/2310.18021).

Start Python and:

    >>> from formalgeo.configuration import Configuration
    >>> from formalgeo.tools import parse_gdl

Load GDL, construct geometric configuration, and apply theorems to expand facts or decompose goals:

    >>> gc = Configuration(parsed_gdl=parse_gdl('gdl_path'))
    >>> gc.construct('gcl')
    >>> gc.apply('theorem')
    >>> gc.decompose('theorem')

Print the problem-solving process, geometric configuration or solving graph:

    >>> from formalgeo.tools import show_gc, draw_gc, get_sg, draw_sg
    >>> show_gc(gc)
    >>> draw_gc(gc, 'save_path')
    >>> get_sg(gc, forward=True, serialize=False)
    >>> draw_sg(gc, 'save_path', forward=True)

## Contributing

We welcome contributions from anyone, even if you are new to open source. Fork our repository on GitHub and submit a
pull request. We appreciate contributions of all sizes and are happy to assist newcomers to git with their pull
requests.

Our bug reporting platform is available at [here](https://github.com/FormalGeo/FormalGeo/issues). We encourage you to
report any issues you encounter.

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
derivatives. If it is convenient for you, please cite FormalGeo when using it in your work.