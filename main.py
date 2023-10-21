from tkinter import filedialog
from abbs import Abbreviator 

import tkinter as tk

def callback(ab):
    name= filedialog.askopenfilename()
    log.insert(tk.INSERT, "\n" + ab.run(name))


if __name__ == "__main__":

    my_abbreviator = Abbreviator('data/values.txt')

    root = tk.Tk() 
    root.title("Name Abbreviator") 
    root.geometry("770x650") 


    tk.Button(text='Import Text File', command=lambda: callback(my_abbreviator)).pack(fill=tk.X)
    
    log = tk.Text(root, font=("Verdana", 10), fg="black", width=70, height=40 )
    log.pack() 
    
    tk.mainloop()

