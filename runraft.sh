#!/bin/sh

#
# Utility script for keeping track of which preference settings a file was processed
# with, by copying the current preferences to a date-tagged directory together
# with the output files.
#

dir=`dirname $1`
file=`basename $1 .gts`

newdir=$file-`date +%m%d%H%M`
mkdir -p $newdir/skeinforge-prefs
cp $1 $newdir
cp ~/.skeinforge/*.csv $newdir/skeinforge-prefs
python raft.py $newdir/$file.gts
