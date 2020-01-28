# linker_report.py

## Introduction

The linker_report.py generates a list of symbols in the form of a JSON tree or
a Wiki table. The script accepts several ELF files (executable, object or
archives). It uses the tools *nm* and *readelf* of GNU binutils to get the list
of symbols.

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
$ echo "const int var3 = 32;" | gcc -x c - -c -o object2.o
$ ar cr ./archive.a ./object1.o ./object2.o
```

Generate a JSON file with the tree of object files and symbols contained in
an archive file.

```console
$ linker_report.py --archive archive.a
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
$ linker_report.py --summarize --archive archive.a
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
|object1.o|  0B| 12B|  0B|
|var2|  0B|  4B|  0B|
|var1|  0B|  8B|  0B|
```

We need now an executable ELF file.

```console
$ echo "const char* var1 = \"test\"; int var2 = 32; int main(void) {printf(\"bonjour\");}" | gcc -x c -
```

Generate a JSON object with the symbols contained in an executable file.

```console
$ linker_report.py --elf a.out
{
    "name": "a.out",
    "type": "executable",
    "program_size": 70,
    "ro_data_size": 0,
    "data_size": 69,
    "sub_nodes": ...
}
```

Note here that we use the flag "--elf". The only difference with "--object" and
"--archive" is that the first get the list of symbols via *readelf* and the
second via *nm*.

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
$ linker_report.py --filter "name=var1" --archive ./archive.a
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

## Examples with jq

We cannot directly compare two JSON outpus with diff, as the symbols are not
sorted. But we can use *jq* to sort the symbols in alphabetical order:

```console
$ linker_report.py --elf ./archive.a | jq ".sub_nodes | sort_by(.name)"
[
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
  },
  {
    "name": "var3",
    "type": "variable",
    "program_size": 0,
    "ro_data_size": 0,
    "data_size": 4
  }
]
```

Note that to be able to execute the previous jq program, we need a flat
*sub_nodes* list, it is why we use the *--elf* flag.

In the same way, we can sort the symbols according to their size in data
sections (.data, .bss or .rodata):

```console
linker_report.py --elf ./archive.a | jq ".sub_nodes | sort_by(.data_size)"
[
  {
    "name": "var2",
    "type": "variable",
    "program_size": 0,
    "ro_data_size": 0,
    "data_size": 4
  },
  {
    "name": "var3",
    "type": "variable",
    "program_size": 0,
    "ro_data_size": 0,
    "data_size": 4
  },
  {
    "name": "var1",
    "type": "variable",
    "program_size": 0,
    "ro_data_size": 0,
    "data_size": 8
  }
]
```
