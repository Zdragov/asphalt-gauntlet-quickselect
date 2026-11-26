#!/usr/bin/env python3

from difflib import get_close_matches
import logging
import mss
import numpy as np
import pydirectinput

import time
import vgamepad as vg

from PIL import Image
from rapidocr import RapidOCR

_gamepad = vg.VX360Gamepad()   # coonect virtual controller

KEYMAP = {
    "up":    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "down":  vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "left":  vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    "a":     vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "b":     vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
}


logging.getLogger("RapidOCR").setLevel(logging.WARNING)

MONITOR = 1

#build REGION from that monitor
with mss.MSS() as sct:
    mon = sct.monitors[MONITOR]

w, h = mon["width"], mon["height"]

REGION = {
    "left":   mon["left"] + int(round(w * 0.072265625)),
    "top":    mon["top"]  + int(round(h * 0.38194444444)),
    "width":  int(round(w * 0.85546875)),
    "height": int(round(h * 0.06944444444)),
    "mon":    MONITOR,
}

engine = RapidOCR()

def mouseClickSClass():
    pydirectinput.moveTo(int(round(0.8*w)), int(round(0.1458333333*h)))
    time.sleep(0.1)
    pydirectinput.mouseDown()
    time.sleep(0.05)
    pydirectinput.mouseUp()
    time.sleep(0.1)

def pressButton(name, delay=0.03):
    btn = KEYMAP[name]
    _gamepad.press_button(button=btn)
    _gamepad.update()
    time.sleep(0.02)
    _gamepad.release_button(button=btn)
    _gamepad.update()
    time.sleep(delay)

def resetCursorToStart(delay=0.1):

    _gamepad.left_trigger(value=255)
    _gamepad.update()
    time.sleep(delay)
    _gamepad.left_trigger(value=0)
    _gamepad.update()
    time.sleep(delay)

    _gamepad.right_trigger(value=255)
    _gamepad.update()
    time.sleep(delay)
    _gamepad.right_trigger(value=0)
    _gamepad.update()
    time.sleep(delay)


def importPreferences(path="order.txt"):
    priorities = {} #create the priorities list
    with open(path, "r", encoding="utf-8") as f: 
        for line in f:  
            line = line.strip() 
            if not line or line.startswith("#"): 
                continue
            parts = [p.strip() for p in line.split(",")] 
            if len(parts) < 2: 
                continue
            priorities[parts[0].lower()] = [c.lower() for c in parts[1:] if c] 
    return priorities 


def captureScreenRegion(region):
    with mss.MSS() as sct:
        sctImg = sct.grab(region)
        return Image.frombytes("RGB", sctImg.size, sctImg.bgra, "raw", "BGRX")


def imgToList(img):
    result = engine(np.array(img))
    return [] if result.txts is None else list(result.txts) 


def matchTrack(entry, priorities, cutoff=0.75):
    entry = entry.strip().lower()
    if entry in priorities:
        return entry
    candidates = get_close_matches(entry, priorities.keys(), n=1, cutoff=cutoff)
    return candidates[0] if candidates else None


def resolveTracks(raw_entries, priorities, cutoff=0.75):
    matched, unmatched = {}, []

    for raw in raw_entries:
        track = matchTrack(raw, priorities, cutoff)
        if track is None:
            unmatched.append(raw)
            continue

        if track != raw.strip().lower():
            print(f"fuzzy: {raw!r} → {track!r}")

        matched[track] = priorities[track]

    return matched, unmatched

#for now, entirecarlist acts as your garage. implement actual system later

def loadEntireCarList():
    entireCarList = []
    with open("maxrankorder.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            entireCarList.extend(c.strip() for c in line.split(",") if c.strip())
    return entireCarList

def sortEntireCarList(cars):
    topRow = cars[0::2]
    botRow = cars[1::2]
    return topRow, botRow

def findCarPosInEntireCarList(targetCar, topRow, botRow):
    key = targetCar.strip().lower()
    if key in topRow:
        return (0, topRow.index(key))
    if key in botRow:
        return (1, botRow.index(key))
    return None

def navigateToCar(currentRow, targetRow, currentCol, targetCol, pressButton):
    dc = targetCol - currentCol
    if dc > 0:
        for _ in range(dc):   pressButton("right")
    elif dc < 0:
        for _ in range(-dc):  pressButton("left")

    if targetRow > currentRow:       pressButton("down")
    elif targetRow < currentRow:     pressButton("up")


    

def activateMacro():

    #take screenshot here

    #calculate (while navigating?)

    pressButton("b")       # back
    time.sleep(2)

    pressButton("down")    # navigate to confirm button
    time.sleep(2)

    pressButton("a")       # press Confirm opponent
    time.sleep(2)

    pressButton("a")       # press Select car
    time.sleep(2)

    #go to S class

    #at this point, in garage menu. find car 1





if __name__ == "__main__":

    time.sleep(5) #let the user tab into the game
    pressButton("b") #exit "controller connected" prompt
    time.sleep(3) #padding

    priorities = importPreferences("order.txt")

    entireCarList = loadEntireCarList()
    topRow, botRow = sortEntireCarList(entireCarList)
    print(f"loaded {len(entireCarList)} cars")
    print(f"  topRow ({len(topRow)}): {topRow[:5]}{'...' if len(topRow) > 5 else ''}")
    print(f"  botRow ({len(botRow)}): {botRow[:5]}{'...' if len(botRow) > 5 else ''}")




    #take a photo 

    rawEntries = imgToList(captureScreenRegion(REGION))
    rawEntries = rawEntries[:5]
    matched, unmatched = resolveTracks(rawEntries, priorities, cutoff=0.75)

    usedCars = set()
    carsChosen = []




    #calculate
    print("\npicks per track:")
    for track, cars in matched.items(): #find track, then find priority order
        carPicked = None                #clear selection   
        for car in cars:                #go through the priority in order
            if car not in usedCars:     #if this car hasnt been selected yet,
                carPicked = car         #pick the car
                usedCars.add(car)       #and add it to the usedCars list
                break                   #exit inner loop
        if carPicked:                   #is carPicked is something and not None,
            carsChosen.append(carPicked)       #add it to the output list
            print(f"  {track}: {carPicked}  (order: {' > '.join(cars)})")   




    #navigate to car

    """
    #test function
    pos = findCarPosInEntireCarList("senna", topRow, botRow)
    if pos is None:
        print("target not found in garage list")
    else:
        row, col = pos
        print(f"sf90 → (row={row}, col={col})")

        resetCursorToStart()
        navigateToCar(row, col, pressButton)

        pressButton("a") #confirm
        time.sleep(1)
        pressButton("left") #next track
        time.sleep(1)
        pressButton("a") # into garage screen again

        resetCursorToStart()
        navigateToCar(row, col, pressButton)
"""
    
    #actual function

    carsChosen = ["devel", "sf90", "nevera","lykan","abs"]

    """for i in range(300):
        pressButton("right")      # go to the right side of car list - S class
        time.sleep(0.05)
"""

    match 2: #standard vs advanced
        case 1:
            for car in carsChosen:
                pos = findCarPosInEntireCarList(car, topRow, botRow)
                if pos is None:
                    print("target not found in garage list")
                else:
                    row, col = pos
                    print(f"sf90 → (row={row}, col={col})")

                    resetCursorToStart()
                    navigateToCar(row, col, pressButton)

                match 2: #which option?
                    case 1:  #actual challenge screen
                        pressButton("a") #confirm
                        time.sleep(1)
                        pressButton("right") #next track
                        time.sleep(1)
                        pressButton("a") # into garage screen again
                    case 2: #garage testing
                        pressButton("a")
                        time.sleep(2)
                        pressButton("b")
                        time.sleep(2)
        case 2: #navigate to car (advanced, faster)

            resetCursorToStart()
            currentRow, currentCol = 0, 0

            for car in carsChosen:
                pos = findCarPosInEntireCarList(car, topRow, botRow)
                if pos is None:
                    print(f"{car} not found in garage list")
                    continue

                targetRow, targetCol = pos
                print(f"{car} -> ({targetRow}, {targetCol})  from ({currentRow}, {currentCol})")

                navigateToCar(currentRow, targetRow, currentCol, targetCol, pressButton)
                currentRow, currentCol = targetRow, targetCol  

                match 2:              
                    case 1:  # actual challenge screen
                        pressButton("a")
                        time.sleep(1)
                        pressButton("right")
                        time.sleep(1)
                        pressButton("a")
                        # cursor is now on this car in the next track's picker
                    case 2:  # garage testing
                        pressButton("a")
                        time.sleep(2)
                        pressButton("b")
                        time.sleep(2)