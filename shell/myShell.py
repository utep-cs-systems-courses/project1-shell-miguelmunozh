#! /usr/bin/env python3
import re, sys, os

    
def change_dir(command):
    current_path = os.getcwd()          # get the current directory
    command, desired_dir = re.split(" ", command) # get the command and the desired dir
    os.chdir(desired_dir)
    
def execute_command(command):
    pass
            
# for other commands
def execute(command):
    rc = os.fork()
    if rc < 0:
        os.write(2, "fork failed".encode())
        sys.exit()
    elif rc == 0:
        command = [i.strip() for i in re.split(' ', command)]
        if '/' in command[0]: # ? xd
            try:
                os.execve(command[0], command, os.environ)
            except FileNotFoundError:
                pass
        else:
            for directory in re.split(':', os.environ['PATH']):
                program = "%s/%s" % (directory, command[0])
                try:
                    os.execve(program, command, os.environ)
                except FileNotFoundError:
                    pass
                except ValueError:
                    pass

        os.write(2, ("Command %s not found\n" % command[0]).encode())
        sys.exit(1)
    else:
        child_pid_code = os.wait()

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
        os.close(1)
        sys.stdout = open(file_path, 'w+') # for writting
                
        os.set_inheritable(1, True)
                
        for directory in re.split(':', os.environ['PATH']):
            program = "%s/%s" % (directory, command[0])
            try:
                os.execve(program, command, os.environ)
            except FileNotFoundError:
                pass
            except ValueError:
                pass

        os.write(2, ("Command %s not found\n" % command[0]).encode())
        sys.exit(1)
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
            except ValueError:
                pass

        os.write(2, ("Command %s not found\n" % command[0]).encode())
        sys.exit(1)
    else:
        child_pid_code = os.wait()

def path(args):
    for dir in re.split(":", os.environ['PATH']):   # try each directory in the path
        program = "%s/%s" % (dir, args[0])
        try:
            os.execve(program, args, os.environ)    # try to exec program
        except FileNotFoundError:                   # ...expected
            pass                                    # ...fail quietly
    os.write(2, ("Child was not able to exec %s\n" % args[0]).encode())
    sys.exit(1)                                     # terminate with error

def pipe(command):
   inst1, inst2 = command.split('|')
   inst1 = inst1.split()
   inst2 = inst2.split()
   r, w = os.pipe()
   for f in (r, w):
       os.set_inheritable(f, True)
       pid = os.fork()
       if pid == 0:
           os.close(1)
           os.dup(w)
           os.set_inheritable(1, True)
           for fd in (r, w):
               os.close(fd)
               path(inst1)
       elif pid > 0:
           os.close(0)
           os.dup(r)
           os.set_inheritable(0, True)
           for fd in (w, r):
               os.close(fd)
               path(inst2)
       else:
           os.write(2, ('Fork failed').encode())
           sys.exit(1)
       
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


