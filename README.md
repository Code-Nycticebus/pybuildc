# Pybuildc

Personal build system for the C language. For me a build system has to do a few things:

1. [ ] Only compile the changed file of a project to save compile-time.
2. [ ] Compile obj-files concurrently to safe compile time
3. [ ] Handle dependecies
4. [x] change between Debug and Release flags
5. [ ] Testing

## Install

```terminal
git clone https://github.com/Code-Nycticebus/pybuildc.git
pip install pybuildc
```

## Usage

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

```terminal
pybuildc test
```
### Other flags

You can specify the directory of the project using the ```-d``` flag. 

```terminal
pybuildc -d examples/test_project <action>
```
