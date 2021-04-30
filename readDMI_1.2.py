"""
Matthew Kavanaugh

For issues:
matthew.kavanaugh@windstream.com
kavanaughm1@gmail.com

this program reads from a Microdynamics DOT-Z1 PRO DMI
"""

import serial
import serial.tools.list_ports
import os
from tkinter import *
import threading


class SerialReader:
    def __init__(self, outlog, comport_textbox, filename_textbox):
        self.userfile = None
        self.microfile = None
        self.outlog = outlog
        self.comport_textbox = comport_textbox
        self.filename_textbox = filename_textbox
        self.userport = self.checkports()
    
    def checkports(self):
        """This function looks at all COM ports and identifies the USB device
         (which we assume is ours bc i am bad at this)
        It is ran on startup and also when "refresh" button is pressed
        """
        try:
            # first line focuses on end of log window
            self.outlog.see("end")

            # clear text field and enable writing
            self.comport_textbox.config(state=NORMAL)
            self.comport_textbox.delete(0, END)
            self.comport_textbox.insert(0, "None")

            # run through every COM port to find USB
            for comport in serial.tools.list_ports.comports():
                if comport.description[0:3] == "USB":
                    self.comport_textbox.delete(0, END)
                    self.comport_textbox.insert(0, comport.name)
                    self.outlog.insert(END, f">>DMI Detected on port {comport.name}\n")
                    self.comport_textbox.config(state=DISABLED)
                    return comport.name

            # handling for none connected
            self.outlog.insert(
                END,
                ">>No DMI detected, please ensure USB cable is connected and DMI is powered on \n",
            )
            # this line makes the text box static again
            self.comport_textbox.config(state=DISABLED)
        except:
            self.outlog.insert(
                END,
                ">> ERROR\n>>>>An unknown error ocurred. Please email me and try again I guess",
            )

    def extract(self):
        # This function is called when "Extract" button pressed and prepares for communication by generating an output file
        try:
            # parse user input into a file path
            self.outlog.see("end")
            self.userfile = self.filename_textbox.get()
            
            # handle if they forgot to type
            if self.userfile == "":
                self.outlog.insert(END, ">>You must insert a desired file name\n")
                return
            workdir = os.getcwd()
            self.microfile = os.path.join(workdir, "OUTPUT", f"{self.userfile}_microstation.txt")
            self.userfile = os.path.join(workdir, "OUTPUT", f"{self.userfile}.txt")
            # create directory
            os.makedirs(os.path.dirname(self.userfile), exist_ok=True)

            # create/wipe file
            with open(self.userfile, "w") as file:
                file.write("DMI OUTPUT LOG \n")
            with open(self.microfile, "w") as file:
                file.write("place point\n")
            
            # prompt user to turn on DMI
            self.outlog.insert(
                END,
                f'>>{self.userport} open...\n>>>>Waiting for DMI. Press MODE and enter "70"....\n',
            )
            self.outlog.see("end")

            # call the threadread function in
        
            threading.Thread(target=self.threadread).start()

           
            
                        
            

            
            
        except OSError as e:
            self.outlog.insert(
                END,
                ">> ERROR\n>>>>Invalid filename. Do not use special characters or spaces.\n",
            )
            
        except serial.SerialException as e:
            self.outlog.insert(
                END,
                ">> ERROR\n>>>>Serial error. Please unplug any USB devices and try again\n",
            )
            
            
        except Exception as e:
            self.outlog.insert(
                END, ">> ERROR\n>>>>Unkown error. Please restart and try again\n"
            )
            
            

    def threadread(self):
        # this function performs the CPU intesive communication in a seperate thread so GUI doesn't hang
            # open serial com line
        try:
            ser = serial.Serial(self.userport)
            has_begun = False
            ser.timeout = 1
            line = ""
            # read every byte
            while ser.is_open:
                
                byte = ser.read()

                # has_begun gives us a way to time out because the DMI will keep sending junk after info is transferred
                if has_begun and not byte:
                    break

                if byte != b"\r":
                    line += byte.decode()

                # newline signifies the end of a line so we print it and reset the var
                if byte == b"\n":
                    with open(self.userfile, "a") as file:
                        file.write(line)
                    self.outlog.insert(END, line)
                    self.outlog.see("end")
                    line = ""
                    has_begun = True
            # Only makes it here if everything works
            #download complete
            self.processdata()
            self.outlog.insert(
            END, ">> DOWNLOAD COMPLETE\n>>>>You may close the window\n"
            )
            self.outlog.insert(END, f">>>>Raw output file saved to {self.userfile}\n")
            self.outlog.insert(END, f">>>>Microstation file saved to {self.microfile}\n")
            self.outlog.see("end")
        except serial.SerialException:
            self.outlog.insert(
                END, ">> ERROR\n>>>>Serial Error: Device may have been disconnected\n"
            )
        except Exception as e:
            self.outlog.insert(
                END, ">> ERROR\n>>>>Unkown Error: Please restart and try again"
            )
            print(e)
            
    def processdata(self):
        #generates text file that can be imported into microstation
        with open(self.microfile, "a") as outfile:
                with open(self.userfile, "r") as infile:
                    linelist=infile.readlines() 
                    for l in linelist[2:]:
                        tmp=l.split()
                        outfile.write(f"point acsabsolute {tmp[4]}, {tmp[3]};\n")
                    outfile.write("reset")        

                    
# GOOEY BELOW THIS POINT

if __name__ == '__main__':
    # build window
    top = Tk()
    top.title("DMI Extractor")
    top.geometry("680x500")
    
    # static text on left
    L1 = Label(top, text="COM Port:")
    L1.grid(padx=10, row=0, column=0, sticky=W)
    L2 = Label(top, text="Output Name:")
    L2.grid(padx=10, row=1, column=0, sticky=W)
    L3 = Label(top, text="Microdynamics DOTZ1 PRO")
    L3.grid(row=0, column=9, sticky=E)
    
    # draw log box with scroll wheel
    outlog = Text(state=NORMAL, width=80)
    outlog.grid(columnspan=10, row=2, rowspan=50, padx=10, pady=5)
    scrollb = Scrollbar(command=outlog.yview)
    scrollb.grid(row=2, column=10, rowspan=50, sticky=NSEW)
    scrollb = outlog["yscrollcommand"] = scrollb.set
    
    # text boxes in the middle
    comport_textbox = Entry(state=DISABLED)
    comport_textbox.grid(row=0, column=1, padx=5, pady=5, sticky=NSEW)
    filename_textbox = Entry()
    filename_textbox.grid(row=1, column=1, padx=5, pady=5, sticky=NSEW)
    
    sr = SerialReader(outlog, comport_textbox, filename_textbox)
    
    # Buttons on the right
    btn1 = Button(top, text="Refresh", command=lambda: sr.checkports())
    btn1.grid(row=0, column=2, sticky=NSEW, padx=5, pady=5)
    btn2 = Button(top, text="Extract", command=lambda: sr.extract())
    btn2.grid(row=1, column=2, sticky=NSEW, padx=5, pady=5)
    
    # binding box to enter to start extraction
    filename_textbox.bind("<Return>", lambda _: sr.extract())
    
    # check com ports on startup and loop gui
    top.mainloop()
    
