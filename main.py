#!/usr/bin/env python3

from difflib import get_close_matches
import logging
import mss
import numpy as np
from PIL import Image
from rapidocr import RapidOCR

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

#for now, entirecarlist acts as your garage. implement fallback system later

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







if __name__ == "__main__":

    priorities = importPreferences("order.txt")

    entireCarList = loadEntireCarList()
    topRow, botRow = sortEntireCarList(entireCarList)
    print(f"loaded {len(entireCarList)} cars")
    print(f"  topRow ({len(topRow)}): {topRow[:5]}{'...' if len(topRow) > 5 else ''}")
    print(f"  botRow ({len(botRow)}): {botRow[:5]}{'...' if len(botRow) > 5 else ''}")

    a = findCarPosInEntireCarList("ats", topRow, botRow)
    print(a)







    rawEntries = imgToList(captureScreenRegion(REGION))
    rawEntries = rawEntries[:5]
    matched, unmatched = resolveTracks(rawEntries, priorities, cutoff=0.75)

    usedCars = set()  

    print("\npicks per track:")
    for track, cars in matched.items():
        pick = None
        for car in cars:
            if car not in usedCars:
                pick = car
                usedCars.add(car)
                break
        if pick:
            print(f"  {track}: {pick}  (order: {' > '.join(cars)})")