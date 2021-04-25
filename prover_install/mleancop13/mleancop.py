#!/usr/bin/env python3

### This is a rewrite of mleancop.sh in Python. Everything is kept as similar to the original as possible
### (especially strange percentages where there are 194 parts in the whole thing unlike in the normal percentages
### where there are 100 parts), only things that obviously did not work very well in the original (such as timeouts
### of the process when given timeouts were relatively small) are changed.
###
### Python was chosen because of the ease of launching and controlling subprocess (compared to shell script, the
### original language). This is significant as there is a need to be able to use fractional timeout for the prover
### which is currently impossible and highly unreliable.
###
### Modifications to the shell script which were done to make the shell script run on the newer version of swilp are
### also kept.

import subprocess
import sys
import argparse
import signal

from settings import settings, validateSettings

# command line only options
problemFile = ''
timeout = 200

# interface settings
printSettings = True

def mleancop(opts, comp, time_pc):
    # because percentages apparently have 194 parts, not 100
    partial_timeout = timeout / 194 * time_pc
    try:
        proc = subprocess.run([settings['prolog-path']] + settings['prolog-options'] +
                              ['-g', 'assert((print(A):-write(A))).',
                               '-g', 'assert(prolog(\'%s\')).' % (settings['prolog'],),
                               '-g', '[\'%s/mleancop_main.pl\'].' % (settings['mleancop-path'],),
                               '-g', 'asserta(logic(\'%s\')).' % (settings['logic'],),
                               '-g', 'asserta(domain(\'$%s\')).' % (settings['domain'],),
                               '-g', 'mleancop_main(\'%s\',%s,_).' % (problemFile, opts),
                               '-t', 'halt.'
                               ],
                              universal_newlines=True,
                              check=True,
                              stdout=subprocess.PIPE,
                              timeout=partial_timeout or None
                              )
    except subprocess.TimeoutExpired:
        return

    theoremOrUnsatisfiable = findInOutput(proc.stdout, ' Theorem', ' Unsatisfiable')
    if comp:
        nonTheoremOrSatisfiable = findInOutput(proc.stdout, ' Non-Theorem', ' Satisfiable')
    else:
        nonTheoremOrSatisfiable = None

    if theoremOrUnsatisfiable or nonTheoremOrSatisfiable:
        if settings['print-proof']:
            print(proc.stdout)
        if settings['save-proof']:
            with open(problemFile + '.proof', 'w') as f:
                f.write(proc.stdout)

        if theoremOrUnsatisfiable:
            sys.exit(0)
        else:
            sys.exit(1)

    # no answer for some reason

def findInOutput(output, *args):
    lines = output.split('\n')
    for item in args:
        for line in lines:
            if line.find(item) >= 0:
                return line

def positive_int(value):
    ival = int(value)
    if ival < 0:
        raise argparse.ArgumentTypeError("invalid positive int value: '%s'" % (value,))
    return ival
            
def readSettings():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('problem_file', metavar='problem-file', help='path of the problem file')
    parser.add_argument('timeout',
                        help='prover timeout in seconds',
                        type=positive_int,
                        nargs="?",
                        )
    parser.add_argument('-q', action='store_false', dest='quiet', default=True)
    overrides = parser.add_argument_group("Overrides", "These options correspond to the options in the settings file and can be used to override values from there.")
    for setting in settings.keys():
        if type(settings[setting]) is bool:
            boolGroup = overrides.add_mutually_exclusive_group(required=False)
            boolGroup.add_argument('--'+ setting, dest=setting.replace('-', '_'), action='store_true', default=None)
            boolGroup.add_argument('--no-' + setting, dest=setting.replace('-', '_'), action='store_false', default=None)
        elif type(settings[setting]) is list:
            overrides.add_argument('--' + setting, nargs='*', metavar='OPTION')
        else:
            overrides.add_argument('--' + setting)
    args = parser.parse_args()

    global problemFile
    problemFile = args.problem_file
    global timeout
    timeout = args.timeout or timeout
    global printSettings
    printSettings = args.quiet

    argDict = vars(args)
    for setting in settings.keys():
        if argDict[setting.replace('-', '_')] is not None:
            settings[setting] = argDict[setting.replace('-', '_')]

def signal_handler(signum, frame):
    sys.exit(2)
            
if __name__ == '__main__':
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # some settings are read from command line, others are from config file, command line can override config file
    readSettings()

    validateSettings()

    if printSettings:
        print('Using settings:')
        print('\tProblem file:', problemFile)
        print('\tTimeout:', timeout)
        print('\tConfig:', settings)

    # uses loaded settings, exits when gets some result
    mleancop("[cut,scut,comp(7)]",      True,  20)
    mleancop("[def,cut]",               False, 20)
    mleancop("[nodef]",                 True,  10)
    mleancop("[reo(23),cut,scut]",      False, 10)
    mleancop("[reo(31),cut,scut]",      False, 10)
    mleancop("[reo(47),cut,scut]",      False, 10)
    mleancop("[reo(25),def,cut,scut]",  False,  5)
    mleancop("[reo(42),conj,cut,scut]", False,  5)
    mleancop("[conj,def,cut,scut]",     False,  5)
    mleancop("[def]",                   True,  99)

    print('Timeout')
    sys.exit(2) # tried everything and everything timed out
