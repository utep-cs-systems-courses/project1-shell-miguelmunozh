#! /usr/bin/env python3
import re, sys, os

    
def change_dir(command):
    current_path = os.getcwd()                    # get the current directory
    command, desired_dir = re.split(" ", command) # get the command and the desired dir
    os.chdir(desired_dir)
    

# to execute commands
def execute(command):
    rc = os.fork()
    if rc < 0:
        os.write(2, "fork failed".encode())
        sys.exit()
    elif rc == 0:
        command = [i.strip() for i in re.split(' ', command)]
        if '/' in command[0]: 
            try:
                os.execve(command[0], command, os.environ)
            except FileNotFoundError:
                pass
        else:
            for directory in re.split(':', os.environ['PATH']): # try each dir in the path
                program = "%s/%s" % (directory, command[0])
                try:
                    os.execve(program, command, os.environ) # try to exec program
                except FileNotFoundError:                   # ...expected
                    pass                                    # fail quietly

    else:
        childPidCode = os.wait() # parent waiting for child process to finish

def output_redirection(command):
    # get the command and the file path to write on it
    command, file_path = [i.strip() for i in re.split('>', command)]
    file_path = os.getcwd() + '/' + file_path  # get current dir, add the dir to put the file
    command = [i.strip() for i in re.split(' ', command)] # remove leading and trailing chars
    
    rc = os.fork()
    if rc < 0:
        os.write(2, "Fork failed".encode())
        sys.exit(0)
    elif rc == 0:
        os.close(1)                        # redirect child's stdout
        sys.stdout = open(file_path, 'w+') # open file to write
        os.set_inheritable(1, True)
        for directory in re.split(':', os.environ['PATH']):
            program = "%s/%s" % (directory, command[0])
            try:
                os.execve(program, command, os.environ)  #try to exec program
            except FileNotFoundError:
                pass

    else:
        child_pid_code = os.wait()

                                            
# almost same than for output redirection 
def input_redirection(command):
    command, file_path = [i.strip() for i in re.split('<', command)]
    file_path = os.getcwd() + '/' + file_path
    command = [i.strip() for i in re.split(' ', command)]
    rc = os.fork()
    if rc < 0:
        os.write(2, "Fork failed".encode())
        sys.exit(1)
    elif rc == 0:
        os.close(0)
        sys.stdin = open(file_path, 'r')
        os.set_inheritable(1, True)
        for directory in re.split(':', os.environ['PATH']):
            program = "%s/%s" % (directory, command[0])
            try:
                os.execve(program, command, os.environ)
            except FileNotFoundError:
                pass
    else:
        child_pid_code = os.wait()


def pipe(command):
   inst1, inst2 = command.split('|')
   inst1 = inst1.split()
   inst2 = inst2.split()
   r, w = os.pipe()
   for f in (r, w):
       os.set_inheritable(f, True)
       pid = os.fork()
       if pid == 0:            # child - will write to pipe
           os.close(1)         # redirect childs stdout
           os.dup(w)
           os.set_inheritable(1, True)
           for fd in (r, w):
               os.close(fd)
               # execute child program
               for dir in re.split(":", os.environ['PATH']):   # try each directory in the path
                   program = "%s/%s" % (dir, inst1[0])
                   try:
                       os.execve(program, inst1, os.environ)    # try to exec program
                   except FileNotFoundError:                   # ...expected
                       pass                                    # ...fail quietly
   
       elif pid > 0:           # parent (forked ok)
           os.close(0)
           os.dup(r)
           os.set_inheritable(0, True)
           for fd in (w, r):
               os.close(fd)
               # executes parent program
               for dir in re.split(":", os.environ['PATH']):   # try each directory in the path
                   program = "%s/%s" % (dir, inst2[0])
                   try:
                       os.execve(program, inst2, os.environ)    # try to exec program
                   except FileNotFoundError:                   # ...expected
                       pass                                    # ...fail quietly
   
       else:
           os.write(2, ('Fork failed').encode())
       
# call a functiond depending on the command
def commands(command):
    if "exit" in command:
        sys.exit(0)
    elif "cd" in command:
        change_dir(command)
    elif "|" in command:
        pipe(command)
    elif ">" in command:
        output_redirection(command)
    elif "<" in command:
        input_redirection(command)
    # if enter is clicke with no commands ask for prompt again
    elif command == "\n": 
        return
    else:
        execute(command)



# try to set PS1 to be $
# export PS1="\u - \h$ " 
 
try:
    sys.ps1 = os.environ['PS1']
except KeyError:
    sys.ps1 = '$ '
if sys.ps1 is None:
    sys.ps1 = '$ '

        
if __name__ == '__main__':
    try:
        while True:
            os.write(1, sys.ps1.encode())
            userInput = os.read(0, 1024).decode()[:-1]
            # get the user input, commands function determines which command it is
            commands(userInput)
    except KeyboardInterrupt:
        os.write(1, "\nProcess finished with exit code 0".encode())


