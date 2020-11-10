#!/usr/bin/env bash

# Test suite of the linker_report.py script.
# Currently, does only check that the ouput is a valid JSON file.

PYTHON="/usr/bin/env python3"
JSON_CHECKER="/usr/bin/env jq"

OBJECT1="object1.o"
OBJECT2="object2.o"
ARCHIVE="archive.a"

echo "const char* var1 = \"test\"; int var2 = 32;" | gcc -x c - -c -o ${OBJECT1}
echo "const int var3 = 32;" | gcc -x c - -c -o ${OBJECT2}
ar cr ${ARCHIVE} ${OBJECT1} ${OBJECT2}

${PYTHON} linker_report.py --archive ${ARCHIVE} | ${JSON_CHECKER}
if [ $? -ne 0 ]; then
	echo "The generated JSON stream is not valid"
	exit -1
fi


${PYTHON} linker_report.py --summarize --archive ${ARCHIVE} | ${JSON_CHECKER}
if [ $? -ne 0 ]; then
	echo "The generated JSON stream is not valid"
	exit -1
fi

${PYTHON} linker_report.py --human-readable --out-format table --object ${OBJECT1}
if [ $? -ne 0 ]; then
	echo "Failed to generate the Wiki Table."
	exit -1
fi

EXECUTABLE="a.out"

echo "const char* var1 = \"test\"; int var2 = 32; int main(void) {printf(\"bonjour\");}" | gcc -x c -

${PYTHON} linker_report.py --executable ${EXECUTABLE} | ${JSON_CHECKER}
if [ $? -ne 0 ]; then
	echo "The generated JSON stream is not valid"
	exit -1
fi

${PYTHON} linker_report.py --filter "size<8" --out-format table --archive ${ARCHIVE}
if [ $? -ne 0 ]; then
	echo "Failed to generate the Wiki Table."
	exit -1
fi

${PYTHON} linker_report.py --filter "name=var1" --archive ${ARCHIVE} | ${JSON_CHECKER}
if [ $? -ne 0 ]; then
	echo "The generated JSON stream is not valid"
	exit -1
fi

echo "===[ PASS ]==="
