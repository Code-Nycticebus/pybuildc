# Pybuildc
Personal build system for the C language.  

# Contents
- [Install](#install)
- [Commands](#commands)
  - [New](#new)
  - [Build](#build)
  - [Run](#run)
  - [Test](#test)
  - [Other Flags](#other-flags)
- [Config](#config)
  - [Project Info](#project-info)
  - [Executable](#executable)
  - [Dependencies](#dependencies)
  - [Build Scripts](#build-scripts)

# Install
I dont have any packaging setup so right now so you have to build it from source.

```terminal
git clone https://github.com/Code-Nycticebus/pybuildc.git
pip install pybuildc
```

# Commands
## New
Creates new project with some default files to get a project started. Also generates a `pybuild.toml` file with the required options.

```terminal
pybuildc new <project name>
```

## Build
When building a Project of a pybuildc.toml file has to be in the specified directory.
Default directory is the current working directory.

```terminal
pybuildc build
```
## Run

The Project is runs file that are registered as exe in the `pybuildc.toml`. By default it tries to run the exe with the project name (eg `pybuildc run -e <PROJECT NAME>`).
```terminal
pybuildc run
```

You can change the target with the ```-e``` flag: 
```terminal
pybuildc run --exe <other>
```  
## Test
Compiles all ```*-test.c``` files in the ```test/``` directory and runs all. 

```terminal
pybuildc test
```
## Other flags
You can specify the directory of the project using the ```-d``` flag. 

```terminal
pybuildc -d path/to/project <action>
```

# Config

## Project Info
This is the project info required for building a project.
```toml
[pybuildc]
name = "PROJECT NAME"
cc = "clang"
```


## Executable
Register files that should be compiled to a executable like this:
```toml
[exe]
main = "src/main.c"
example = "examples/example1.c"
```

## Dependencies
Add dependencies by specifing it as deps. There are different types of dependencies. By default it links statically, but you could also include other `pybuildc` projects. The 
```toml
[deps]
math = { l="m" }
other_project = { dir = "other/project/directory", type = "pybuildc" }
```

if its is a platform specific dependency you can specify it like this:
```toml
[deps.linux]
math = { l = "m" }
```


## Build Scripts
You can add a script that should run everytime the project is build in the config file.
```toml
build.scripts = [
  { cmd = "make", args = ["generate"] },
]
```
