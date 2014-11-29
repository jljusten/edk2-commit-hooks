#!/usr/bin/python

import re
import subprocess
import sys

# For a pre-commit hook, only writes to stderr matter
sys.stdout = sys.stderr

if len(sys.argv) >= 3:
    (REPOS, TXN) = sys.argv[1:3]
else:
    REPOS='/home/svn/p/edk2/code'
    TXN = None

# Run svnlook to get the commit message
cmd = [ '/usr/bin/svnlook' ]
cmd.append('log')
if TXN is not None: cmd += [ '-t', TXN ]
cmd.append(REPOS)
p = subprocess.Popen(cmd,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
r = p.communicate()[0]

url = 'http://sourceforge.net/apps/mediawiki/tianocore/index.php?title=Code_Style/Commit_Message'

def good_msg():
    print 'The commit message format passed all checks.'
    print url
    sys.exit(0)

def msg_error(err):
    print 'The commit message format is not valid:'
    print ' ', err
    print url
    sys.exit(1)

cu_msg='Contributed-under: TianoCore Contribution Agreement 1.0'
if r.find(cu_msg) < 0:
    msg_error('Missing Contributed-under')

# All checks passed, so allow the commit.
good_msg()
