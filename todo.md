Okay so we're gonna need to make inputable params that we can publish to the pacemaker, but only if a pacemaker is actually connected.
We need to make a UI that handles receiving data from the pacemaker
NEED AOO AAI VOO VVI

We should consider switching from Tkinter to PyQt5. I recently just learned about it and I think itll make design for deliverable 2 much much much easier. Tkinter is just too archaic. <<<< Write about this in reportS



Going forward in deliverable 2 we should split tasks up like this:
    - One person focuses on making the UI good by replacing tkinter with PyQT5
    - One person will be responsible for getting the serial comms working with the pacemaker. This means figuring out the byte formatting and all those details. 
    - One person will be figuring out how to visualize the egram data. 

    We also require that the ranges of each parameter are respected and that only certain params are able to be adjusted depending on which mode is selected.

Now see right now the UI is kind of holding on to the backend logic which is really dumb we need to separate these asap. After submitting Deliverable 1 we really need to refactor.