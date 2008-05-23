from layers import *
from gRead import *
import Tkinter, ImageTk

class Preview:
    def __init__(self, layers):
        self.images = make_images(layers)
        self.index = 0
        size = self.images[0].size
        self.root = Tkinter.Tk()
        self.root.title("HydraRaptor")
        frame = Tkinter.Frame(self.root)
        frame.pack()
        self.canvas = Tkinter.Canvas(frame, width = size[0], height = size[1])
        self.canvas.pack()
        self.canvas.config(scrollregion=self.canvas.bbox(Tkinter.ALL))
        self.exit_button = Tkinter.Button(frame, text = "Exit", fg = "red", command = frame.quit)
        self.exit_button.pack(side=Tkinter.RIGHT)
        self.down_button = Tkinter.Button(frame, text = "Down", command = self.down)
        self.down_button.pack(side=Tkinter.LEFT)
        self.up_button = Tkinter.Button(frame, text = "Up", command = self.up)
        self.up_button.pack(side=Tkinter.LEFT)
        self.update()
        self.root.mainloop()

    def update(self):
        self.image = ImageTk.PhotoImage(self.images[self.index])
        self.canvas.create_image(0,0, anchor= Tkinter.NW, image = self.image)
        if self.index < len(self.images) - 1:
            self.up_button.config(state = Tkinter.NORMAL)
        else:
            self.up_button.config(state = Tkinter.DISABLED)
        if self.index > 0:
            self.down_button.config(state = Tkinter.NORMAL)
        else:
            self.down_button.config(state = Tkinter.DISABLED)

    def up(self):
        self.index += 1
        self.update()

    def down(self):
        self.index -= 1
        self.update()


#
# script interface

import sys

if not sys.argv[1:]:
    print "Syntax: python pilview.py gcodefile"
#    sys.exit(1)

#filename = sys.argv[1]
#layers = []
#gRead(filename, layers)
#Preview(layers)
