# Repository for V0 characterization experiments

## Description

This repository contains code that is specific to V0 characterization experiments:
* Jupiter notebooks (or scripts for Spyder) with measurement execution code
* Experiment specific python modules

## Structure

The repository contains mainly two directories:
* `scripts` - place for the notebooks and scripts which run the experiments
* `v0_utils` - python modules with code that is specific to these
experiments

## Installation

1. Clone this repository
2. In the command prompt (or terminal, or Anaconda prompt), from the root
of the cloned repository, install this package using pip like this: `pip 
install --no-deps -e .` (the `-e` argument removes the need for reinstalling 
the package once local changes has been made)

