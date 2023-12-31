# Pybuildc
Personal build system for the C language.  

### Contents
1. [Install](#install)
2. [Usage](#usage)

## Install
I dont have any packaging setup so right now so you have to build it from source.

```terminal
git clone https://github.com/Code-Nycticebus/pybuildc.git
pip install pybuildc
```

## Usage

### Commands
1. [New](#new)
2. [Build](#build)
2. [Run](#run)
3. [Test](#test)
4. [Other Flags](#other-flags)

### New
Creates new project with some default files to get a project started. Also generates a ```pybuild.toml``` file with the required options.

```terminal
pybuildc new <project name>
```

### Build
When building a Project of a pybuildc.toml file has to be in the specified directory.
Default directory is the current working directory.
It will build a executable binary if ```src/main.c``` exists, else it will build a ```.a``` static library.

```terminal
pybuildc build
```
### Run
The Project is runnable if ```src/main.c``` exists.

```terminal
pybuildc run
```
### Test
Compiles all ```*-test.c``` files in the ```tests/``` directory and runs all. It excludes the ```src/main.c``` file.

```terminal
pybuildc test
```
### Other flags
You can specify the directory of the project using the ```-d``` flag. 

```terminal
pybuildc -d path/to/project <action>
```
