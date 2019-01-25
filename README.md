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
                        [--summarize] [--filter FILTER [FILTER ...]]
                        [--out-format [OUTPUT_FORMAT]] [--out [OUTPUT_FILE]]
```

## Examples

We create some object file and an archive.

```console
$ echo "const char* var1 = \"test\"; int var2 = 32;" | gcc -x c - -c -o object1.o
$ echo "const int var3 = 32" | gcc -x c - -c -o object2.o
$ ar cr ./archive.a ./object1.o ./object2.o
```

Generate a JSON file with the tree of object files and symbols contained in
an archive file.

```console
$ linker_report.py --out-format json --archive archive.a
{
    "name": "archive.a",
    "type": "archive",
    "program_size": 0,
    "ro_data_size": 4,
    "data_size": 12,
    "sub_nodes": [
        {
            "name": "object1.o",
            "type": "object",
            "program_size": 0,
            "ro_data_size": 0,
            "data_size": 12,
            "sub_nodes": [
                {
                    "name": "var1",
                    "type": "variable",
                    "program_size": 0,
                    "ro_data_size": 0,
                    "data_size": 8
                },
                {
                    "name": "var2",
                    "type": "variable",
                    "program_size": 0,
                    "ro_data_size": 0,
                    "data_size": 4
                }
            ]
        },
        {
            "name": "object2.o",
            "type": "object",
            "program_size": 0,
            "ro_data_size": 4,
            "data_size": 0,
            "sub_nodes": [
                {
                    "name": "var3",
                    "type": "constant",
                    "program_size": 0,
                    "ro_data_size": 4,
                    "data_size": 0
                }
            ]
        }
    ]
}
```

Generate a JSON file with the objects contained in an archive file.

```console
$ linker_report.py --out-format json --summarize --archive archive.a
{
    "name": "archive.a",
    "type": "archive",
    "program_size": 0,
    "ro_data_size": 4,
    "data_size": 12,
    "sub_nodes": [
        {
            "name": "object2.o",
            "type": "object",
            "program_size": 0,
            "ro_data_size": 4,
            "data_size": 0
        },
        {
            "name": "object1.o",
            "type": "object",
            "program_size": 0,
            "ro_data_size": 0,
            "data_size": 12
        }
    ]
}
```

Generate a wiki table with the symbols contained in an object file:

```console
$ linker_report.py --human-readable --out-format table --object object1.o
||Name||Program size||Data size||Read-only data size||
|object1.o|0|12|0|
|var1|0|8|0|
|var2|0|4|0|
```

We need now an executable ELF file.

```console
$ echo "const char* var1 = \"test\"; int var2 = 32; int main(void) {printf(\"bonjour\");}" | gcc -x c -
```

Generate a JSON object with the symbols contained in an executable file.

```console
$ linker_report.py --out-format json --elf a.out
{
    "name": "a.out",
    "type": "executable",
    "program_size": 70,
    "ro_data_size": 0,
    "data_size": 69,
    "sub_nodes": ...
}
```

Some filters are implemented. These filter are only applicable on symbols. The
tree structure with the containers (object or archive files) is still
generated.

Generate a wiki table with all the symbols smaller than 8 bytes contained in an
archive file.

```console
$ linker_report.py --filter "size<8" --out-format table --archive ./archive.a
||Name||Program size||Data size||Read-only data size||
|archive.a|0|12|4|
|object1.o|0|12|0|
|var2|0|4|0|
|object2.o|0|0|4|
|var3|0|0|4|
```

Generate JSON object with the symbol "var1" contained in an archive file.

```console
$ linker_report.py --filter "name=var1" --out-format json --archive ./archive.a
{
    "name": "archive.a",
    "type": "archive",
    "program_size": 0,
    "ro_data_size": 4,
    "data_size": 12,
    "sub_nodes": [
        {
            "name": "object2.o",
            "type": "object",
            "program_size": 0,
            "ro_data_size": 4,
            "data_size": 0,
            "sub_nodes": []
        },
        {
            "name": "object1.o",
            "type": "object",
            "program_size": 0,
            "ro_data_size": 0,
            "data_size": 12,
            "sub_nodes": [
                {
                    "name": "var1",
                    "type": "variable",
                    "program_size": 0,
                    "ro_data_size": 0,
                    "data_size": 8
                }
            ]
        }
    ]
}
```
