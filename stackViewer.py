import subprocess as sp
from sys import *
import re
import curses
from enum import Enum
from string import Formatter
from math import *
from random import *

# classes
class StkOrder(Enum):
    INC = 0 #increasing
    DEC = 1 #decreasing

class Addr:
    val = 0
    pointedToBy = None
    pointer = False
    matched = None
    addr = None
    
    def __init__(self, value, addr=-1):
        self.val = value
        self.addr = addr

# global vars
wd = None # window object
stk = []# stack object
stkOrder = StkOrder.INC
screenCenter = -1
matches = []
selected = None

# functions
def readData(fName):
    headerStr = sp.check_output(["readelf", "-l", fName]).decode()
    line = re.findall(r'^\s*LOAD\s*[0-9a-fx]+ [0-9a-fx]+ [0-9a-fx]+\n\s*[0-9a-fx]+ [0-9a-fx]+  RW', headerStr, re.MULTILINE)[-1]
    
    line = line.split()[:-2]
    line.remove(line[3])
    line.remove(line[0])
    stkFOffset, stkAddr, stkSize = tuple([int(word[2:], 16) for word in line])
    
    with open(fName, 'br') as cDump:
        cDump.seek(stkFOffset, 0)
        for i in range(0, stkSize):
            newAddr = Addr(int(cDump.read(1)[0]), i + stkAddr)
            stk.append(newAddr)
    return stkAddr, stkSize

def drawMemRegion():
    global screenCenter
    global selected
    
    scrH = wd.getmaxyx()[0]
    screenCenter = int(max(scrH//2, min(screenCenter, len(stk)-scrH//2))) #clamp screenCenter to the indicies of the stk
    loI = screenCenter - scrH//2
    hiI = screenCenter + scrH//2
    
    wd.clear()
    
    lineNum = 0
    for i, addr in enumerate(stk[loI:hiI]):
        lineStr = "{0:#05x} \x7C {1:#04x}".format(addr.addr, addr.val)
        if addr.matched == None:
            wd.addstr(lineNum, 0, lineStr)
        else:
            hColor = curses.A_STANDOUT if i+loI == selected else curses.color_pair(1)
            hStart, hEnd = addr.matched
            wd.addstr(lineNum, 0, lineStr[0:hStart])
            wd.addstr(lineNum, hStart, lineStr[hStart:hEnd], hColor)
            wd.addstr(lineNum, hEnd, lineStr[hEnd:])
        lineNum += 1
    wd.refresh()

def findMatchingAddrsIndicies(indexLst, searchStr):
    global stk
    matches = []
    searchStr = searchStr.lower()
    for i in indexLst:
        if len(matches) < 100: break
        addr = stk[i]
        hexAddr = "{0:#06x}".format(addr.addr)
        if searchStr in hexAddr:
            loc = int(hexAddr.find(searchStr))
            addr.matched = (loc, loc+len(searchStr))
            matches.append(i)
        else:
            addr.matched = None
    return matches

# def genMatchingAddrs(s):
    # lo = stk[0].addr
    # hi = stk[-1].addr
    # dist = hi-lo
    # chBits = ceil(log(dist, 2)) - cil(log(s
    
def findAddr():
    global screenCenter
    global matches
    global selected
    startI = screenCenter
    searchStr = ""
    # matches = list(stk)
    matches = list(range(len(stk)))
    dispH = wd.getmaxyx()[0]
    while True:
        curses.setsyx(dispH, 0)
        wd.deleteln()
        wd.addstr(dispH-1, 0, "/" + searchStr)
        nextChar = chr(wd.getch())
    
        if nextChar == '\n':
            # break
            return
        # elif nextChar == chr(23): # enter
            # screenCenter = startI
            # return
        elif nextChar == chr(263): # backspace
            searchStr = searchStr[:-1]
            matches = list(range(len(stk)))# TODO find a better way of doing this
        else:
            searchStr += nextChar
    
        matches = findMatchingAddrsIndicies(matches, searchStr)
        if len(matches) == 0:
            screenCenter = startI
        else:
            screenCenter = matches[0]
            selected = matches[0]
            # stk[matches[0]].selected = True
        drawMemRegion()

def main(stdscr):
    global wd
    global screenCenter
    global stk
    global stkOrder
    global matches
    global selected
    wd = stdscr
    
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1, -1, curses.COLOR_RED) # make color pair 1 the yellow hilight color
    # curses.start_color()
    
    wd.clear()
    wd.addstr(0,0,"Reading data")
    wd.refresh()
    baseAddr, size = readData("./core.1717")
     
    scrH = wd.getmaxyx()[0]
    screenCenter = len(stk)
    # screenCenter = baseAddr + scrH/2
    
    while True:
        drawMemRegion()
        button = chr(wd.getch())
        
        if (abs(size - screenCenter) < scrH/2):
            continue
     
        if button == 'j':
            screenCenter += 1
        elif button == 'k':
            screenCenter -= 1
        elif button == '/':
            findAddr()
        elif button == 'G':
            screenCenter = len(stk)
        elif button == 'g':
            screenCenter = 0
        elif button == 'n':
            if len(matches) > 0:
                selected = matches[(matches.index(selected)+1)%(len(matches)-1)]
                if abs(screenCenter - selected) >= scrH/2:
                    screenCenter = selected
        elif button == 'N':
            if len(matches) > 0:
                selected = matches[matches.index(selected)-1]
                if abs(screenCenter - selected) >= scrH/2:
                    screenCenter = selected
        elif button == ' ':
            selected = None
            matches = []
            for addr in stk:
                addr.matched = None
        elif button == 'q':
            return
            

curses.wrapper(main)
