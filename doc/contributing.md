# Introduction to Contributing

We welcome anyone to contribute to this project, even if you are new to open-source.

## Contributing to Code

coming soon...

## Contributing to Dataset

If you have built your own dataset and wish for it to be used by more people, then releasing it on this project is a
good option. Projects that meet the **Dataset Structure** will be merged into *FormalGeo*.

### Dataset Structure

You can look at the other datasets in  `datasets.josn` to get a general idea of the structure of a project.  
A standardized dataset release project is as follows:

    project_name/
    ├── gdl/
    │   ├── doc/
    │   │   └── ...
    │   ├── predicate_GDL.json
    │   └── theorem_GDL.json
    ├── problems/
    │   ├── 1.json
    │   └── ...
    ├── diagrams/
    │   ├── 1.png
    │   └── ...
    ├── files/
    │   └── ...
    ├── info.json
    ├── LICENSE
    └── README.md

Dataset should be packaged into `dataset_name-dataset_version.tar.7z` and published to `FormalGeo/datasets.json/`,
which is also where users will download your dataset. Submissions containing files or folders other than the
aforementioned ones will be rejected. You should delete irrelevant files in `project_name/` before submitting a pull
request.

#### gdl/

coming soon...

#### problems/

coming soon...

#### diagrams/

coming soon...

#### expanded/

coming soon...

#### files/

This folder can contain any other files you wish to add, such as theorem information for accelerated searching like
`t_msg.json`, dataset statistics, etc. The total size of the files should not exceed 10MB.

#### info.json

coming soon...

#### LICENSE

coming soon...

#### README.md

coming soon...

## Develop Dataset Annotation Tools

coming soon...