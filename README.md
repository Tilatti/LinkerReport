# linker_report.py

## Introduction

The linker_report.py generates a list of symbols in the form of a JSON tree or
a Wiki table. The script accepts several ELF files (executable, object or
archives). It uses the tools nm and readelf of GNU binutils to get the list of
symbols.

## Usage

```
usage: linker_report.py [-h] [--object OBJECTFILE [OBJECTFILE ...]]
                        [--archive ARCHIVEFILE [ARCHIVEFILE ...]]
                        [--elf ELFFILE [ELFFILE ...]] [--human-readable]
                        [--sumarize] [--filter FILTER [FILTER ...]]
                        [--out-format [OUTPUT_FORMAT]] [--out [OUTPUT_FILE]]
```

## Examples

We create some object file and an archive.

```shell
$ echo "const char* var1 = \"test\"; int var2 = 32;" | gcc -x c - -c -o object1.o
$ echo "const int var3 = 32" | gcc -x c - -c -o object2.o
$ ar cr ./archive.a ./object1.o ./object2.o
```

Generate a JSON file with the tree of object files and symbols contained in
an archive file.

```shell
$ linker_report.py --out-format json --archive archive.a
```

Generate a JSON file with the objects contained in an archive file.

```shell
$ linker_report.py --out-format json --sumarize --archive archive.a
```

Generate a wiki table with the symbols contained in an object file:

```shell
$ linker_report.py --human-readable --out-format table --object object1.o
```

We need now an executable ELF file.

```shell
$ echo "const char* var1 = \"test\"; int var2 = 32; int main(void) {printf(\"bonjour\");}" | gcc -x c -
```

Generate a JSON object with the symboles in an executable file.

```shell
$ linker_report.py --out-format json --elf a.out
```
