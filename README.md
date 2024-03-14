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

This also generates a `pybuildc.toml` file.
```toml
[pybuildc]
name="<PROJECT NAME>"
cc="clang"
cflags=[]

[exe]
<PROJECT NAME>="src/<PROJECT NAME>.c"
example="examples/example1.c"
```

### Build
When building a Project of a pybuildc.toml file has to be in the specified directory.
Default directory is the current working directory.

```terminal
pybuildc build
```
### Run

The Project is runs file that are registered as exe in the `pybuildc.toml`. By default it tries to run the file with the project name (eg. `src/bin/<project name>.c`).
```terminal
pybuildc run
```

You can change the target with the ```-e``` flag: 
```terminal
pybuildc run --exe <other>
```  
### Test
Compiles all ```*-test.c``` files in the ```test/``` directory and runs all. 

```terminal
pybuildc test
```
### Other flags
You can specify the directory of the project using the ```-d``` flag. 

```terminal
pybuildc -d path/to/project <action>
```

### Dependencies
Add dependencies by specifing it as deps. There are different types of dependencies. By default it links statically, but you could also include other `pybuildc` projects. The 
```toml
[deps]
math = { l="m" }
other_project = { dir="other/project/directory", type="pybuildc" }
```

if its is a platform specific dependency you can specify it like this:
```toml
[deps.linux]
math = { l="m" }
```


### Build Scripts
You can add a script that should run everytime the project is build in the config file.
```toml
[[build.scripts]]
cmd="generate.sh"
args=["<BUILD DIR>"]
```
