USAGE
=====
It is assumed that a virtual `test-calvin` environment is set up to run calvin-base, as described in _virtualenv.md_

Activate the new  environment    source ~/.virtualenvs/test-calvin/bin/activateand your prompt should change to indicate the activation by prepending `(test-calvin)` to whatever was there before. Use `deactivate` if you should want to leave the virtual environment.

Start calvin runtime within virtualenv and deploy script `test3.calvin`

    $ csruntime --keep-alive --host localhost --port 5000 --controlport 5001 calvin/scripts/test3.calvin

start calvin-mini runtime

    $ python calvin_mini.py

execute setup & migrate program

    $ python runme.py sink
    
This will move the sink (io.StandardOut) from the big calvin runtime to the calvin-mini runtime.
