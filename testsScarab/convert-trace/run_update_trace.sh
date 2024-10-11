SCRIPT=$(readlink -f "$0")
SCRIPTDIR=$(dirname "$SCRIPT")

DRIO_BUILD_DIR=${SCRIPTDIR}/../../tools/scarab/src/deps/dynamorio

for dir in */; do
    echo "$dir"
    cd $dir
    python3 $SCRIPTDIR/updateTraceModulePaths.py .
    cd -
done
