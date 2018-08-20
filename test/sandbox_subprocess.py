from subprocess import Popen, check_output, PIPE, STDOUT, check_call
import os
import shlex
import glob

def call(cmd, **kwargs):
    if not isinstance(cmd, list):
        cmd = shlex.split(cmd)
        parsed_cmd = [cmd[0],]
        for i, word in enumerate(cmd[1:]):
            if word[0]=='$':
                var = word[1:].strip('{').strip('}') 
                varval = os.environ.get(var, word)
                parsed_cmd.append(varval)
            else:
                if '*' in word:
                    items = glob.glob(word)
                    for item in items:
                        parsed_cmd.append(item)
                else:
                    parsed_cmd.append(word)
        cmd = parsed_cmd
    out=check_output(cmd, universal_newlines=True, stderr=STDOUT, **kwargs)
    return out

cmd = 'python --version'
print(call(cmd))

cmd = 'echo $HOME ${SHELL}'
print(call(cmd))

cmd = 'ls test*.yaml'
print(call(cmd))

cmd = 'echo 5'
print(call(cmd))
