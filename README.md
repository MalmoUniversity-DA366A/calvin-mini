USAGE
=====

1. start calvin runtime and deploy script `test3.calvin`

    $ csruntime --keep-alive --host localhost --port 5000 --controlport 5001 calvin/scripts/test3.calvin

2. start calvin-mini runtime

    $ python calvin_mini.py

3. execute setup & migrate program

    $ python runme.py sink
    
    This will move the sink (io.StandardOut) from the big calvin runtime to the calvin-mini runtime.

4. ????

5. profit
