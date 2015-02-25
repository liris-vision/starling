#!/bin/bash
#
# STARLING PROJECT 
#
# LIRIS - Laboratoire d'InfoRmatique en Image et Systèmes d'information 
#
# Copyright: 2012 - 2015 Eric Lombardi (eric.lombardi@liris.cnrs.fr), LIRIS (liris.cnrs.fr), CNRS (www.cnrs.fr)
#
#
#    This program is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License version 3, as published
#    by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranties of
#    MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#    PURPOSE.  See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    For further information, check the COPYING file distributed with this software.
#
#----------------------------------------------------------------------

# 
# run regression tests
# usage: run_regression_tests.sh
#    or: run_regression_tests.sh test1 test2 ...
#

# get OS type (linux/windows)
function getOSType()
{
	if [ "$OS" = "Windows_NT" ]
	then
		echo "win"
	else
		kernel_version="$(uname -p)"
		if [ "$kernel_version" = "x86_64" ]
		then
			echo "linux64"
		elif [ "$kernel_version" = "i686" ]
		then
			echo "linux32"
		else
			echo "unknown"
		fi
	fi
}

# get detailed OS version
function getOSVersion()
{
	"$PYTHONPATH" tools/getos.py
}

# compare images and videos using OpenCV
function diff2()
{
	if [ "$(expr match "$1" '.*\.txt$')" != "0" ]
	then
		# compare text files
		diff "$1" "$2"
	elif [ "$(expr match "$1" '.*\.xml$')" != "0" ]
	then
		# compare xml files
		diff "$1" "$2"
	elif [ "$(expr match "$1" '.*\.png$')" != "0" ]
	then
		# compare images
		"$PYTHONPATH" tools/diffimg.py "$1" "$2"
	else
		# compare videos
		"$PYTHONPATH" tools/diffvid.py "$1" "$2"
	fi
}

OSTYPE="$(getOSType)"
echo "OS type is '$OSTYPE'"

# change to script dir
cd "$(dirname "$0")"

# change to starling dir
cd ..

TESTTMP="test.tmp"
TESTLIST="test.p*/*.hrp"  # test.public & test.private

PYTHONPATH="python"
WINOS="off"
if [ "$1" = "-win" -o "$OSTYPE" = "win" ]
then
	echo "Windows mode selected"
	WINOS="on" 
	PYTHONPATH="../../External/python/python.exe"
	
	if [ "$1" = "-win" ]
	then
		shift
	fi
fi

OSVERSION="$(getOSVersion)"
echo "OS version is '$OSVERSION'"

if [ -n "$*" ]
then
	TESTLIST="$*"
fi

# create directory for tests outputs
mkdir "$TESTTMP"

# do tests
for t in $TESTLIST
do
	# ensure test exists
	if [ ! -e "$t" ]
	then
		echo "File '$t' doesn't exist. Skipped."
		continue
	fi

	# use an OS-specific version of the test, if it exists
	if [ -e "$t.$OSVERSION" ]
	then
		t="$t.$OSVERSION"
	fi

	echo "-------------------------------------------------"
	echo "Processing test '$t' ..."

	# does this test provide a testable output ? 
	# yes, if it refers to a file named "xxx_output.xxx"
	if [ "$WINOS" = "off" ]
	then
		# on linux
		output="$(grep -o '[0-9]*_output\.[0-9a-zA-Z]*' $t)"
	else
		# on git bash / windows
		output="$(grep _output $t | sed -e 's/.*test.tmp\///' -e 's/[^A-Za-z0-9]*$//')"
	fi

	if [ -n "$output" ]
	then
		# there is a testable output

		# clean output
		echo "- delete '$TESTTMP/$output'"
		rm -f $TESTTMP/$output

		# run test in foreground
		echo "- run test ..."
		"$PYTHONPATH" ./starling.py -b $t

		# compare test output with reference
		# ! works only if output is just one file !
		# compare testable output with reference

		# if an OS specific reference exists, use it, else use general reference 
		testdir="$(dirname "$t")"
		output_ref="$testdir/$output.ref.$OSVERSION"
		if [ ! -e "${output_ref}" ]
		then
			output_ref="$testdir/$output.ref"
		fi

		echo "- compare with reference '${output_ref}'"
		#diff -q $TESTTMP/$output ${output_ref}
		diff2 $TESTTMP/$output ${output_ref}
		diffreturn="$?"
		if [ "$diffreturn" = "0" ]
		then
			# test succeeded
			result="succeeded"
		else
			# test failed
			result="FAILED"
		fi
	else
		# no testable output
		# just try to compile test project
				
		# run test in background
		echo "- no testable output, just try to compile and run ..."
		echo "- run test ..."
		OUTPUTFILE="/tmp/testoutput"
		"$PYTHONPATH" ./starling.py -b $t >"$OUTPUTFILE" 2>&1 &
		testpid="$!"

		# wait some time, then stop test
		sleep 6
		#xdotool key "Escape"
		kill $testpid

		# get execution status
		wait $testpid
		teststatus=$?

		# check for execution error
		if [ "$teststatus" != 0 ]
		then
			# something goes wrong during test execution
			echo "- execution error detected !"
			result="FAILED"
		else
			# check test output for compilation error
			echo "- look for compilation error"
			errors="$(grep 'COMPILATION FAILED' "$OUTPUTFILE")" 
			if [ -z "$errors" ]
			then
				# no run error, test succeeded
				result="succeeded"
			else
				# run errors, test failed
				cat "$OUTPUTFILE"
				result="FAILED"
			fi
		fi
	fi

	msg="Test '$t' ... $result."
	echo $msg
	logs="${logs}${msg}\n"
done

echo
echo "******************************"
echo All tests summary:
echo -e $logs
echo Failed tests summary:
echo -e $logs | grep FAILED
echo
