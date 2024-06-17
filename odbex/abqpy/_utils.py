import sys

def cae_print(msg):
    # type: (str) -> None
    """Print a message to the console when in the cae kernel process.

    Parameters
    ----------
    msg : str
        Message to be printed to console.
    """
    if any(".py" in arg for arg in sys.argv):
        print >> sys.__stdout__, msg    # Console
    else:
        print(msg)  # Abaqus GUI