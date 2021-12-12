import pexpect
import re
from pexpect.expect import searcher_re

# regex for vt100 from https://stackoverflow.com/a/14693789/5008284
class StripAnsiExpecter(pexpect.Expecter):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

    def new_data(self, data):
        data = self.ansi_escape.sub('', data)
        return pexpect.Expecter.new_data(self, data)

class StripAnsiSpawn(pexpect.spawn):
    def expect_list(self, pattern_list, timeout=-1, searchwindowsize=-1, async_=False):
        if timeout == -1:
            timeout = self.timeout
        exp = StripAnsiExpecter(self, searcher_re(pattern_list), searchwindowsize)
        return exp.expect_loop(timeout)
