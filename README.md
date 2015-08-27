# USAGE
It is assumed that a virtual `test-calvin` environment is set up to run calvin-base, as described in _virtualenv.md_

Activate a environment in a separate terminal window, hereafter called Terminal 2    source ~/.virtualenvs/test-calvin/bin/activateand your prompt should change to indicate the activation by prepending `(test-calvin)` to whatever was there before. Use `deactivate` if you should want to leave the virtual environment.

Start calvin runtime within virtualenv at Terminal 1 

    source ~/.virtualenvs/test-calvin/bin/activate
    
and deploy script `test3.calvin`

    $ csruntime --keep-alive --host localhost --port 5000 --controlport 5001 calvin/scripts/test3.calvin

It is also possible to do all this through the web interface, as described in the setup for calvin base.

Activate the same virtual environment in a new separate terminal window, hereafter called Terminal 2    source ~/.virtualenvs/test-calvin/bin/activateand your prompt should change to indicate the activation by prepending `(test-calvin)` to whatever was there before. Use `deactivate` if you should want to leave the virtual environment.

start calvin-mini runtime in Terminal 2

    $ python calvin_mini.py

`CTRL+Z` stops the current process, which can then be resumed as a background process using the command `bg`. 

Execute setup & migrate program to move the sink (io.StandardOut) from the big calvin runtime to the calvin-mini runtime.

    $ python runme.py sink

this should move the output from Terminal 1 to Terminal 2.

#### N.B.
The `runme.py` has hardcoded the port used, therefore you cannot run this script twice to have another stdout actor used in another script moved to a calvin-mini instance wihtout assigning this to another port.

It is possible to know what process uses what port with `lsof`, e.g:

    sudo lsof -iTCP:5000 -n -P'

to check which process uses port 5000. See 'man lsof' for (way too much) information.


## Terminating calvin mini

If calvin mini executes in the background with `bg` you can move it to the foreground with `fg`and end it with `CTRL-C`.

More info here: <http://www.thegeekstuff.com/2010/05/unix-background-job/>

