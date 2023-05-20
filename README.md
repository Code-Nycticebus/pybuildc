# Pybuildc

Personal build system for the C language. This project serves as a way to learn the [returns](https://github.com/dry-python/returns) library. It kinda makes my job harder sometimes and the code is more complex and harder to read.  

1. [Install](#install)
2. [Usage](#usage)

### For me a build system has to do a few things:

1. [ ] Only compile the changed file of a project to save compile-time.
2. [X] Compile obj-files concurrently to safe compile time
3. [ ] Handle dependecies
4. [x] change between Debug and Release flags
5. [x] Testing

## Install

I dont have any Packaging setup so right now you have to build it from source.

```terminal
git clone https://github.com/Code-Nycticebus/pybuildc.git
pip install pybuildc
```

## Usage

1. [New](#new)
2. [Build](#build)
3. [Test](#test)
4. [Other Flags](#other-flags)

### New

Creates new project with some default files to get a project started.
Also generates a pybuild.toml file.

```terminal
pybuildc new <project directory>
```

### Build

When building a Project of a pybuildc.toml file has to be in the specified directory.
Default directory is the current working directory.

```terminal
pybuildc build
```
### Test

Compiles all ```tests/*-test.c``` files and runs all executables.

```terminal
pybuildc test
```
### Other flags

You can specify the directory of the project using the ```-d``` flag. 

```terminal
pybuildc -d path/to/project <action>
```
