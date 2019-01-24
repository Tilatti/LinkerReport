# linker_report.py

## Introduction

The linker_report.py generates a list of symbols in the form of a JSON tree or
a Wiki table. The script accepts several ELF files (executable, object or
archives). It uses the tools nm and readelf of GNU binutils to get the list of
symbols.

## Usage

```
usage: linker_report.py [-h] [--objectfile OBJECTFILE [OBJECTFILE ...]]
                        [--archivefile ARCHIVEFILE [ARCHIVEFILE ...]]
                        [--elffile ELFFILE [ELFFILE ...]] [--human-readable]
                        [--sumarize] [--filter FILTER [FILTER ...]]
                        [--out-format [OUTPUT_FORMAT]] [--out [OUTPUT_FILE]]
```

## Examples

Generate a wiki table with the symbols contained in the object file:

```
$ ./linker_report.py --human-readable --outformat table --objectfile test.o
```

Generate a JSON file with the tree of object files and symbols contained in
the archive file.

```
$ ./linker_report.py --outformat json --archivefile test.a
```

Generate a JSON file with the section sizes of the archive file.

```
$ ./linker_report.py --outformat json --sumarize --archivefile test.a
```

Generate a JSON object with the section sizes of the executable file.

```
$ ./linker_report.py --outformat json --sumarize --elffile a.out
```
