from pathlib import Path
from tkinter import filedialog
from abbs import Abbreviator 

import tkinter as tk

def callback(ab):
    name= filedialog.askopenfilename()
    print(output(name, ab))

def output(fname, ab):
    return "{}, {}".format(Path(fname).stem, ab.make_abbreviations_dataframe(fname))



if __name__ == "__main__":

    my_abbreviator = Abbreviator('data/values.txt')

    tk.Button(text='Click to Open File', 
        command=lambda: callback(my_abbreviator)).pack(fill=tk.X)
    tk.mainloop()

