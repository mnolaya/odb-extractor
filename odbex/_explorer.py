import os
import Tkinter as tk
import tkFileDialog as tkdialogs

def _hide_root_window():
    # Hide root Tk window.
    root = tk.Tk()
    root.overrideredirect(1)
    root.attributes("-topmost", True)
    root.withdraw()

def filepaths_from_odb_explorer(initial_dir=None):
    """
    Create a file selection dialog for selecting one or multiple odb files.
    """
    _hide_root_window()
    if initial_dir == None: initial_dir = os.getcwd()
    title = "Select .odb file(s) to load."
    file_types = (("Abaqus Output Database files", "*.odb"),)
    return [str(fp)for fp in tkdialogs.askopenfilenames(title=title, initialdir=initial_dir, filetypes=file_types)]