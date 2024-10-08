# EDL - Experiment Directory Layout

[![QA](https://github.com/bothlab/edlio/actions/workflows/python-qa.yml/badge.svg)](https://github.com/bothlab/edlio/actions/workflows/python-qa.yml)

This repository contains specifications for the "Experiment Directory Layout" (EDL) storage layout as
used by the [Syntalos](https://github.com/bothlab/syntalos) data acquisition tool.

It also contains a Python module, `edlio`, to easily load and save data in an EDL structure
for simplified raw experiment data management.

Check out the [online documentation](https://edl.readthedocs.io/latest/) to learn more about this project!

To install, run:
```sh
pip install git+https://github.com/athp18/edlio.git
```
Or to install from source:
```sh
git clone https://github.com/athp18/edlio.git
cd edlio
pip install -r requirements.txt
pip install -e .
```

To re-format a Syntalos dataset to a MoSeq dataset, try something like this:
```python
from edlio.format import format

dataset = '/path/to/some/EDLCollection/dataset' # make sure the dataset is an EDLCollection dataset and has a manifest.toml file
format(dataset)
```
