#!/bin/sh
#-----------
# File:      mleancop.sh
# Version:   1.3 (1.3b)
# Date:      1 January 2014
#-----------
# Purpose:   Invokes the MleanCoP prover
# Usage:     ./mleancop.sh <problem file> [<time limit>]
# Author:    Jens Otten
# Web:       www.leancop.de/mleancop/
# Copyright: (c) 2007-2014 by Jens Otten
# License:   GNU General Public License
#-----------

#-----------
# Parameters

# set modal logic to D,T,S4,S5 or multimodal [d|t|s4|s5|multi]
LOGIC=s5

# set domain to constant, cumulative or varying [const|cumul|vary]
DOMAIN=const

# set MleanCoP prover path
PROVER_PATH=.

# set Prolog system, path, and further options

# PROLOG=eclipse
# PROLOG_PATH=/usr/bin/eclipse
# PROLOG_OPTIONS='-e'

PROLOG=swi
PROLOG_PATH=/usr/bin/swipl
# changed: goals moved to the actual call, removed parameters which were removed at some point
#          --no-debug does not seem to do much currently. It either used to do something useful (documentation does
#              not show that), or was here just in case. Either way, I am leaving this in, just in case
#          --stack-limit used to be three separate stacks with their own limits. Here I used the sum of those
#              numbers. It can be incorrect, but there is nothing I can do, old options are gone.
# NOTE: on the cluster should use original file if possible (smaller chance to get different results)
PROLOG_OPTIONS='--no-debug --stack-limit=340m'

#PROLOG=sicstus
#PROLOG_PATH=/usr/bin/sicstus
#PROLOG_OPTIONS='--nologo --noinfo --goal'

# print proof [yes|no]
PRINT_PROOF=yes
# save proof [yes|no]
SAVE_PROOF=no

# set TPTP library path
# TPTP=.

#----------
# Functions

mleancop()
{
    # Serious changes because original timeout calculations are absolute bullshit:
    # 1. TIMELIMIT is now in fractional seconds. This allows to use milliseconds which are required if timeout is
    #        given in smaller quantities than 100s
    # 2. Single invocation of this function is allocated TIME_PC parts of TIMELIMIT out of 194 (don't ask why,
    #        apparently 194 is the equivalent of 100% in certain circles).
    # 3. Output of the result or the lack of one is not included in timings, as it was originally.

    # Input: $SET, $COMP, $TIME_PC
    TLIMIT=`expr $TIME_PC '*' $TIMELIMIT / 111`
    if [ $TLIMIT -eq 0 ]; then TLIMIT=1; fi
    # changes:
    # moved one goal from options down here
    # split what was supposed to go under -t in one big sequence into goals, they should be executed in order.
    #     Not sure if really works as it should but what can I do.
    $PROLOG_PATH $PROLOG_OPTIONS \
		 -g "assert((print(A):-write(A)))."\
		 -g "assert(prolog('$PROLOG'))."\
		 -g "['$PROVER_PATH/mleancop_main.pl']."\
		 -g "asserta(logic('$LOGIC'))."\
		 -g "asserta(domain('$DOMAIN'))."\
		 -g "mleancop_main('$FILE',$SET,_)."\
		 -t "halt."\
		 > $OUTPUT &
    PID=$!
    echo "[$PID] [INIT    ]    Initial settings: TIMELIMIT: $TIMELIMIT ; TIME_PC: $TIME_PC ; TLIMIT: $TLIMIT." >&2
    CPU_SEC=0
    trap "echo \"[$PID] [END     ]    signal received.\" >&2; rm $OUTPUT; kill $PID >/dev/null 2>&1; exit 2"\
	 ALRM XCPU INT QUIT TERM
    while [ $CPU_SEC -lt $TLIMIT ]
    do
	sleep 1
	CPUTIME=`ps -p $PID -o time | grep :`
	if [ ! -n "$CPUTIME" ]; then
	    echo "[$PID] [END     ]    finished while waiting: CPUTIME length is zero." >&2;
	    break
	fi
	CPU_H=`expr 1\`echo $CPUTIME | cut -d':' -f1\` - 100`
	CPU_M=`expr 1\`echo $CPUTIME | cut -d':' -f2\` - 100`
	CPU_S=`expr 1\`echo $CPUTIME | cut -d':' -f3\` - 100`
	CPU_SEC=`expr 3600 '*' $CPU_H + 60 '*' $CPU_M + $CPU_S`
	echo "[$PID] [PROGRESS]    still waiting ( $CPU_SEC / $TLIMIT )." >&2
    done
    if [ -n "$CPUTIME" ]; then
	echo "[$PID] [END     ]    did not finish while waiting: CPUTIME length is non-zero." >&2
	rm $OUTPUT
	kill $PID >/dev/null 2>&1
    else
	RESULT1=`egrep ' Theorem| Unsatisfiable' $OUTPUT`
	RESULT2=`egrep ' Non-Theorem| Satisfiable' $OUTPUT`
	if [ $COMP = n ]; then RESULT2= ; fi
	if [ -n "$RESULT1" -o -n "$RESULT2" ]
	then
	    if [ $PRINT_PROOF = yes ]; then cat $OUTPUT
	    else if [ -n "$RESULT1" ]; then echo $RESULT1
		 else echo $RESULT2; fi
	    fi
	    if [ $SAVE_PROOF = yes ]; then mv $OUTPUT $PROOF_FILE
	    else rm $OUTPUT; fi
	    if [ -n "$RESULT1" ]; then
		echo "[$PID] [END     ]    exiting with status 0." >&2
		exit 0
	    else
		echo "[$PID] [END     ]    exiting with status 1." >&2
		exit 1
	    fi
	else rm $OUTPUT
	fi
	echo "[$PID] [END     ]    neither RESULT1 nor RESULT2 are non-zero." >&2;
    fi
}

#-------------
# Main Program

if [ $# -eq 0 -o $# -gt 2 ]; then
    echo "Usage: $0 <problem file> [<time limit>]"
    exit 2
fi

if [ ! -r "$1" ]; then
    echo "Error: File $1 not found" >&2
    exit 2
fi

if [ -n "`echo "$2" | grep '[^0-9]'`" ]; then
    echo "Error: Time $2 is not a number" >&2
    exit 2
fi

if [ $# -eq 1 ]
then TIMELIMIT=100
else TIMELIMIT=$2
fi

FILE=$1
PROOF_FILE=$FILE.proof
OUTPUT=TMP_OUTPUT_mleancop_`date +%F_%T_%N`

set +m

# invoke MleanCoP core prover with different settings SET
# for time TIME_PC [%]; COMP=y iff settings are complete

SET="[cut,scut,comp(7)]";      COMP=y; TIME_PC=20; mleancop
SET="[def,cut]";               COMP=n; TIME_PC=20; mleancop
SET="[nodef]";                 COMP=y; TIME_PC=10; mleancop
SET="[reo(23),cut,scut]";      COMP=n; TIME_PC=10; mleancop
SET="[reo(31),cut,scut]";      COMP=n; TIME_PC=10; mleancop
SET="[reo(47),cut,scut]";      COMP=n; TIME_PC=10; mleancop
SET="[reo(25),def,cut,scut]";  COMP=n; TIME_PC=5;  mleancop
SET="[reo(42),conj,cut,scut]"; COMP=n; TIME_PC=5;  mleancop
SET="[conj,def,cut,scut]";     COMP=n; TIME_PC=5;  mleancop
SET="[def]";                   COMP=y; TIME_PC=99; mleancop

echo Timeout
exit 2
