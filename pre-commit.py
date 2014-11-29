#!/usr/bin/python

import re
import subprocess
import sys

# For a pre-commit hook, only writes to stderr matter
sys.stdout = sys.stderr

class CheckMsg:
    def __init__(self):
        self.ok = True
        self.msg = self.read_msg()

        self.check_cu()
        self.check_sob()
        self.check_misc_sigs()
        self.check_overall_format()
        self.report_msg_result()

    def read_msg(self):
        assert len(sys.argv) >= 3
        (REPOS, TXN) = sys.argv[1:3]

        # Run svnlook to get the commit message
        cmd = [ '/usr/bin/svnlook' ]
        cmd.append('log')
        cmd += [ '-t', TXN ]
        cmd.append(REPOS)
        p = subprocess.Popen(cmd,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
        return p.communicate()[0]

    def report_msg_result(self):
        if self.ok:
            # All checks passed, so allow the commit.
            return_code = 0 # + 1 # uncomment the '+ 1' for debug
            print 'The commit message format passed all checks.'
        else:
            return_code = 1
        url = 'https://github.com/tianocore/tianocore.github.io/wiki/Commit-Message-Format'
        print url
        sys.exit(return_code)

    def msg_error(self, err, err2=None):
        if self.ok:
            print 'The commit message format is not valid:'
        print ' *', err
        if err2:
            print '  ', err2
        self.ok = False

    def check_cu(self):
        cu_msg='Contributed-under: TianoCore Contribution Agreement 1.0'
        if self.msg.find(cu_msg) < 0:
            self.msg_error('Missing Contributed-under! (Note: this must be added by the code contributor!)')

    @staticmethod
    def make_sig_re(sig, re_input=False):
        if re_input:
            sub_re = sig
        else:
            sub_re = sig.replace('-', r'[-\s]+')
        re_str = r'^(?P<tag>' + sub_re + r')(\s*):(\s*)(?P<value>\S.*?)(?:\s*)$'
        try:
            return re.compile(re_str, re.MULTILINE|re.IGNORECASE)
        except Exception:
            print "Tried to compile re:", re_str
            raise

    sig_block_re = re.compile(r'''^
                                      (?: (?P<tag>[^:]+) \s* : \s* (?P<value>\S.*?) )
                                          |
                                      (?: \[ (?P<updater>[^:]+) \s* : \s* (?P<note>.+?) \s* \] )
                              \s* $''',
                              re.VERBOSE | re.MULTILINE)
 
    def find_sigs(self, sig):
        if not sig.endswith('-by') and sig != 'Cc':
            sig += '-by'
        regex = self.make_sig_re(sig)

        sigs = regex.findall(self.msg)

        bad_case_sigs = filter(lambda m: m[0] != sig, sigs)
        for s in bad_case_sigs:
            self.msg_error("'" +s[0] + "' should be '" + sig + "'")

        for s in sigs:
            if s[1] != '':
                self.msg_error('There should be no spaces between ' + sig + " and the ':'")
            if s[2] != ' ':
                self.msg_error("There should be a space after '" + sig + ":'")

            self.check_email(s[3])

        return sigs

    email_re1 = re.compile(r'(?:\s*)(.*?)(\s*)<(.+)>\s*$',
                           re.MULTILINE|re.IGNORECASE)

    def check_email(self, email):
        email = email.strip()
        mo = self.email_re1.match(email)
        if mo is None:
            self.msg_error("Email format is invalid: " + email.strip())
            return

        name = mo.group(1).strip()
        if name == '':
            self.msg_error("Name is not provided with email address: " + email)
        else:
            quoted = len(name) > 2 and name[0] == '"' and name[-1] == '"'
            if name.find(',') >= 0 and not quoted:
                self.msg_error('Add quotes (") around name with a comma: ' + name)

        if mo.group(2) == '':
            self.msg_error("There should be a space between the name and email address: " + email)

        if mo.group(3).find(' ') >= 0:
            self.msg_error("The email address cannot contain a space: " + mo.group(3))

    def check_sob(self):
        sob='Signed-off-by'
        if self.msg.find(sob) < 0:
            self.msg_error('Missing Signed-off-by! (Note: this must be added by the code contributor!)')
            return

        sobs = self.find_sigs('Signed-off')

        if len(sobs) == 0:
            self.msg_error('Invalid Signed-off-by format!')
            return

    sig_types = (
        'Reviewed',
        'Reported',
        'Tested',
        'Suggested',
        'Acked',
        'Cc'
        )

    def check_misc_sigs(self):
        for sig in self.sig_types:
            self.find_sigs(sig)

    def check_overall_format(self):
        lines = self.msg.splitlines()
        count = len(lines)

        if count <= 0:
            self.msg_error('Empty commit message!')
            return

        if count >= 1 and len(lines[0]) > 100:
            self.msg_error('First line of commit message (subject line) is too long.')

        if count >= 1 and len(lines[0].strip()) == 0:
            self.msg_error('First line of commit message (subject line) is empty.')

        if count >= 2 and lines[1].strip() != '':
            self.msg_error('Second line of commit message should be empty.')

        for i in range(2, count):
            if len(lines[i]) > 180:
                self.msg_error('Line %d of commit message is too long.' % (i + 1))

        last_sig_line = None
        for i in range(count - 1, 0, -1):
            line = lines[i]
            mo = self.sig_block_re.match(line)
            if mo is None:
                if line.strip() == '':
                    break
                elif last_sig_line is not None:
                    err2 = 'Add empty line before "%s"?' % last_sig_line
                    self.msg_error('The line before the signature block should be empty', err2)
                else:
                    self.msg_error('The signature block was not found')
                break
            last_sig_line = line.strip()

CheckMsg()
