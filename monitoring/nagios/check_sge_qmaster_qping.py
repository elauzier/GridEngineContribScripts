#!/usr/bin/python
#
# check_sge_qmaster_qping.py  Ed Lauzier June 2013
# Original code used for reference:
# http://exchange.nagios.org/directory/Plugins/Uncategorized/Operating-Systems/Solaris/Sun-Grid-Engine/details
#
# Code set up presently for simple qping check.
#

import os
import sys
import string
import getopt
import shlex
import subprocess
import signal

progname = 'check_sge_qmaster_qping'
version  = '0.1'
nagiosStateOk = 0
nagiosStateWarning = 1
nagiosStateCritical = 2
nagiosStateUnknown = 3

hostName = ''
sgeCell = ''
warningStates = ''
criticalStates = ''
childPid = 0
timeout = 15

def printUsage():
    print 'Usage: check_sge_qmaster_qping -H <hostname> -C <sge_cell_name> -t <timeout>'

def printHelp():
    printUsage()
    print ''
    print 'Options:'
    print '-V, --version'
    print '   Version of the script.'
    print '-H, --hostname=HOST'
    print '   The hostname (as recognized by SGE) of the node you want to check'
    print '-C, --CELL'
    print '   The SGE_CELL name.'
    print '-t, --timeout=TIMEOUT'
    print '   in seconds'
    sys.exit(nagiosStateUnknown)

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'VhH:C:t:v?', ['version', 'help', 'hostname=', 'sgeCell=', 'timeout=', 'verbose'])
except getopt.GetoptError, errorStr:
    print errorStr
    printUsage()
    sys.exit(nagiosStateUnknown)

if len(args) != 0:
    printUsage()
    sys.exit(nagiosStateUnknown)

for opt, arg in optlist:
    if opt in ('-V', '--version'):
        print '%s %s' % (progname, version)
        sys.exit(nagiosStateUnknown)
    elif opt in ('-h', '--help'):
        printHelp()
        sys.exit(nagiosStateUnknown)
    elif opt in ('-H', '--hostname'):
        hostName = arg
    elif opt in ('-C', '--CELL'):
        sgeCell = arg
    elif opt in ('-v', '--verbose'):
        # Plugin guidelines require this, but we don't have anything extra to
        # report
        pass
    elif opt in ('-t', '--timeout'):
        try:
            timeout = int(arg)
        except ValueError:
            print 'Invalid argument for %s: %s' % (opt, arg)
            sys.exit(nagiosStateUnknown)
    elif opt == '-?':
        printUsage()
        sys.exit(nagiosStateUnknown)
        
if sgeCell == 'prod':
	os.environ['SGE_ROOT']          = '/site/gridengine/soge'
	os.environ['SGE_QMASTER_PORT']  = '16444'
	os.environ['SGE_CLUSTER_NAME']  = 'prod'
	os.environ['SGE_CELL']          = 'prod'
	os.environ['SGE_EXECD_PORT']    = '16445'
	
if sgeCell == 'test':
	os.environ['SGE_ROOT']          = '/site/gridengine/soge'
	os.environ['SGE_QMASTER_PORT']  = '17444'
	os.environ['SGE_CLUSTER_NAME']  = 'test'
	os.environ['SGE_CELL']          = 'test'
	os.environ['SGE_EXECD_PORT']    = '17445'
	
if sgeCell == 'prod' or sgeCell == 'test':
	qhostPath = os.environ['SGE_ROOT'] + '/bin/lx-amd64/qhost'
	qstatPath = os.environ['SGE_ROOT'] + '/bin/lx-amd64/qstat'
	qconfPath = os.environ['SGE_ROOT'] + '/bin/lx-amd64/qconf'
	qpingPath = os.environ['SGE_ROOT'] + '/bin/lx-amd64/qping'
else:
    print 'SGE_CELL must be: prod or test'
    printUsage()
    sys.exit(nagiosStateUnknown)

if hostName == '':
    print 'No hostname specified.'
    printUsage()
    sys.exit(nagiosStateUnknown)

def handleAlarm(signum, frame):
    try:
        if childPid != 0:
            os.kill(childPid, signal.SIGKILL)
    except OSError:
        pass
    print 'Execution timeout exceeded'
    sys.exit(nagiosStateUnknown)

signal.signal(signal.SIGALRM, handleAlarm)
signal.alarm(timeout)

if os.access(qpingPath, os.X_OK) == 0:
    print 'Cannot execute %s' % (qpingPath)
    sys.exit(nagiosStateUnknown)

# for redirect of mycmdline stdout to /dev/null 
# as we only care about errors in this script...
FNULL = open(os.devnull, 'w')
mycmdline = shlex.split( qpingPath + ' -info ' + hostName + ' ' + os.environ["SGE_QMASTER_PORT"] + ' qmaster 1' )
qpingPipe = subprocess.Popen(mycmdline, stdout=FNULL, stderr=subprocess.PIPE)
childPid = qpingPipe.pid
elines = qpingPipe.communicate(input=None)[1]  # (stdout,stderr)
exitStatus = qpingPipe.returncode
exitCode = nagiosStateOk
outputMsg = ''
childPid = 0
if not os.WIFEXITED(exitStatus) or os.WEXITSTATUS(exitStatus) != 0:
    # qping didn't exit cleanly
    # Check if qping printed something out
    # from stderr
    if len(elines) >= 1:
        # Print first line of output
        outputMsg = 'ERROR: qmaster daemon on %s port %s: qping: %s' % (hostName, os.environ['SGE_QMASTER_PORT'], elines.splitlines()[0])
        exitCode = nagiosStateCritical
    else:
        print 'Error with qping'
        sys.exit(nagiosStateUnknown)

if len(outputMsg) > 0:
    print outputMsg
    print 'exitCode %s ' % (exitCode)
else:
    print 'qping Ok'
    print 'exitCode %s ' % (exitCode)

sys.exit(exitCode)
