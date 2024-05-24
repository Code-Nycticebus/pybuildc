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
  - [Project Config](#project-config)
  - [Executable](#executable)
  - [Libraries](#libraries)
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
Default directory is the current working directory. But you can also specify a directory with the `-d` flag.

```terminal
pybuildc build
```
## Run

The Project runs file that are registered as exe in the `pybuildc.toml`. By default it tries to run the exe with the project name (eg `pybuildc run -e <PROJECT NAME>`).
```terminal
pybuildc run
```

You can change the target with the `-e` flag: 
```terminal
pybuildc run -e <other>
```  
## Test
Compiles all `*-test.c` files in the `test/` directory and runs all. 

```terminal
pybuildc test
```

## Other flags
You can specify the directory of the project using the `-d` flag. 

```terminal
pybuildc -d path/to/project <action>
```

# Config
## Project Config
This is the minimal `pybuildc.toml` required for building a project. 
```toml
[pybuildc]
name = "PROJECT NAME"
```


## Executable
Register files that should be compiled to a executable like this:
```toml
[exe]
main = "src/main.c"
example = "examples/example1.c"
```

## Libraries
By default it links statically, but you can also include other `pybuildc` projects.
```toml
[libs]
math = { l = "m" }
prebuild = { dir = "other/prebuild/", I = "include/", L = "lib/", l = "prebuild" }
project = { dir = "other/project/directory", type = "pybuildc" }
```

if its is a platform specific library you can specify it like this:
```toml
[libs.linux]
math = { l = "m" }
```

## Scripts
You can add a script that should run everytime the project is build for example in the config file.
```toml
[[scripts.build]]
cmd = "make"
args = ["generate"]
```

## Run script (not implemented) 
