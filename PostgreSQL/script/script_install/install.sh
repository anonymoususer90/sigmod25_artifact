#!/bin/bash

# Change to this-file-exist-path.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"/
cd $DIR

# Default
BASE_DIR="$DIR""../../../PostgreSQL/"
CONFIGURE=YES
BUILD=RELEASE
GDB=YES
LLVM=NO
TIMESCALE=0

# useful config option:
# --enable-cassert
# --with-llvm
CONFIG_OPTION=""

if [ "$LLVM" == "YES" ]
then
	CONFIG_OPTION+=" --with-llvm"
	LLVM_DIR=$BASE_DIR"llvm_"
fi

COMPILE_OPTION=$@
echo $@

SOURCE_DIR=$BASE_DIR"postgres/"
TARGET_DIR=$BASE_DIR"pgsql/"

cd $SOURCE_DIR

make clean -j

# build
if [ "$BUILD" == "DEBUG" ]
then
	CONFIG_OPTION+=" --enable-cassert"

    COMPILE_OPTION+=" -O0"

	GDB=YES

	if [ "$LLVM" == "YES" ]
	then
		#LLVM_DIR+="Debug"
		LLVM_DIR+="Release"
	fi
else
    COMPILE_OPTION+=" -O2 -DNDEBUG"

	if [ "$LLVM" == "YES" ]
	then
		LLVM_DIR+="Release"
	fi
fi

# gdb
if [ "$GDB" == "YES" ]
then
	COMPILE_OPTION+=" -ggdb3 -g3 -fno-omit-frame-pointer"
fi


if [ "$LLVM" == "YES" ]
then
	LLVM_DIR+="/bin/llvm-config"
	CONFIG_OPTION+=" LLVM_CONFIG="$LLVM_DIR
fi

COMPILE_OPTION+=" -DSLEEP_ON_ASSERT -DABORT_AT_FAIL -DHOOK_SIGNAL -D_GNU_SOURCE -luring"

echo $CONFIG_OPTION
echo $COMPILE_OPTION
echo $LLVM_DIR

# configure
if [ "$CONFIGURE" == "YES" ]
then
    ./configure --silent --prefix=$TARGET_DIR $CONFIG_OPTION CFLAGS="$COMPILE_OPTION"
fi

# make
make -j --silent

# make install
make install -j --silent

cd $DIR


