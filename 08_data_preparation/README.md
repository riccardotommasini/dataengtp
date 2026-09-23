# 08 - Data Preparation

Data wrangling and cleaning with pandas. This is the starting point of the
course: it runs entirely in Jupyter, with no database or Docker stack required.

## Contents

| Notebook | Purpose |
| --- | --- |
| `dataeng-Introduction_to_wrangling_using_pandas.ipynb` | Guided introduction to wrangling with pandas |
| `dataeng-data_cleaning.ipynb` | Guided data cleaning walkthrough |
| `starting_file-*.ipynb` | Fill-in-the-blank versions of the two lectures above |
| `Data Wrangling Homework Stubs.ipynb` | Homework stubs |

Input datasets live in `input/`, figures in `figs/`.

## Running

The `starting_file-*` notebooks are the ones to work in during class; the
matching notebook without the prefix is the completed reference.

This folder has no Docker stack of its own. The shared notebook image
(`notebook/`) is pulled in by the database lectures (`05`, `06`, `07`) via
`compose-notebook.yml`, which cannot be started on its own -- it relies on the
`Practice` network that each of those stacks defines. To get a Jupyter server
with the course packages, start any of those stacks, e.g.:

```sh
cd ../05_mongodb && docker compose up --build notebook
```

Then open <http://localhost:8888> and browse to `work/08_data_preparation/`.

Alternatively, run them in any local Jupyter with the packages listed in
`notebook/requirements.txt`.
