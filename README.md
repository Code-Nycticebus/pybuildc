# Pybuildc

Build system for the C language. For me a build system has to do a few things:

1. Only compile the changed file of a project to save compile-time.
2. Compile obj-files concurrently to safe compile time
3. Handle dependecies
4. change between Debug and Release flags
5. Automatic testing

## Install

```terminal
pip install .
```

## Usage

### New

Creates new project with some default files to get you started.
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

## Planed program flow

1. Loading in config and cache
2. compiling files
3. compiling to exe or lib
