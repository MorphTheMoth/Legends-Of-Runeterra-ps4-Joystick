import _thread
import json
import math
import msvcrt
import time
import urllib.request

import pyautogui
import win32api

import joystickapi

pyautogui.FAILSAFE = False

gameMatrix = [[],[],[],[],[],[],[]]
width, height = 1920, 1080
curI, curJ = -1, -1   #joystick cursor current position in the matrix

class Point:
  def __init__(self, x, y, id):
    self.x = x
    self.y = y
    self.id = id
  def __repr__(self):
    return str(self.x)+' '+str(self.y)

def handHovering():
    return height - pyautogui.position().y < 90 and pyautogui.position().x < 1700 and pyautogui.position().x > 220
def coord(card):
    return Point(card['TopLeftX']+card['Width']/2, card['TopLeftY']-card['Height']/2, card['CardID'])
def enemyHandCoord(card):
    return Point(card['TopLeftX']+card['Width']/2, 1065, card['CardID'])
def handCoord(card):
    return Point(card['TopLeftX']+card['Width']/4, 40, card['CardID'])

def getGameData():
    global gameData, gameMatrix
    while True:
        gameData = json.loads(urllib.request.urlopen("http://localhost:21337/positional-rectangles").read())
        print('--- game data ---')

        if(handHovering()):
            newMatrix = [[], [], [], [], [], [], gameMatrix[6]]
        else:
            newMatrix = [[], [], [], [], [], [], []]
        # -- rectangles matrix
        for card in gameData['Rectangles']:
            if(card['CardCode'] == 'face'):
                continue
            if(card['TopLeftY'] > 1030):
                newMatrix[0].append(enemyHandCoord(card))
            elif(card['Height']<180 and card['TopLeftY']>950 and card['TopLeftY']<1000):
                newMatrix[1].append(coord(card))
            elif(card['Height']<165 and card['TopLeftY']>780 and card['TopLeftY']<830):
                newMatrix[2].append(coord(card))
            elif(card['Height']<120 and card['Height']>110 and card['Width']<120 and card['Width']>110):
                newMatrix[3].append(coord(card))
            elif(card['Height']<165 and card['TopLeftY']>430 and card['TopLeftY']<480):
                newMatrix[4].append(coord(card))
            elif(card['Height']<180 and card['TopLeftY']>240 and card['TopLeftY']<280):
                newMatrix[5].append(coord(card))
            elif(card['TopLeftY']<150 and not handHovering()):
                newMatrix[6].append(handCoord(card))

        for a in newMatrix:
            a.sort(key=lambda x: x.x)
        # print(gameMatrix)
        gameMatrix = newMatrix


def choiceArray():  # how many cards are you choosing?
    maxH = 0  # maxHeight
    arr = []
    for card in gameData['Rectangles']:
        if (card['Height'] > maxH):
            maxH = card['Height']
            arr = [coord(card)]
        elif (card['Height'] == maxH):
            arr.append(coord(card))
    return arr
def checkChoice():
    for card in gameData['Rectangles']:
        if card['Height'] < 140:
            continue
        if (card['TopLeftY'] > height / 2 and card['TopLeftY']-card['Height'] < height / 2):
            return True
    return False

def moveUpMatrix():
    global curI, curJ
    if curI <= 0:
        toogleMatrix()
        return
    curI -= 1
    if len(gameMatrix[curI]) == 0:
        moveUpMatrix()
    else:
        curJ = 0
def moveDownMatrix():
    global curI, curJ
    if curI == 6:
        toogleMatrix()
        return
    curI += 1
    if gameMatrix[curI] == []:
        moveDownMatrix()
    else:
        curJ = 0
def moveRightMatrix():
    global curI, curJ
    if curJ == len(gameMatrix[curI])-1:
        toogleMatrix()
    else:
        curJ += 1
def moveLeftMatrix():
    global curI, curJ
    if curJ == 0:
        toogleMatrix()
    else:
        curJ -= 1

def toogleMatrix():
    global curI, curJ
    curI, curJ = -1, -1


def input():
    global run, ret, curI, curJ, move, cdCounter, caps, id
    if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode(): # detect ESC (panic button)
        run = False

    ret, info = joystickapi.joyGetPosEx(id)
    #print(info.dwPOV)
    if ret:
        btns = [(1 << i) & info.dwButtons != 0 for i in range(caps.wNumButtons)]
        if info.dwButtons:
            print("buttons: ", btns)

        if info.dwPOV != 65535:
            cdCounter = 0
            print(info.dwPOV)
            # check if there is a choice to make
            if checkChoice():
                print('check choice', checkChoice())
                chArr = choiceArray() # ch = choice
                currCh = -1
                for i, ch in enumerate(chArr):
                    if abs(ch.x - pyautogui.position().x) < 20:
                        currCh = i
                        break

                if currCh == -1:
                    if info.dwPOV == 27000 or info.dwPOV == 0 or info.dwPOV == 18000 or info.dwPOV == 9000:
                        pyautogui.moveTo(chArr[math.floor(len(chArr)/2)].x, chArr[math.floor(len(chArr)/2)].y, 0.1)
                elif info.dwPOV == 9000:
                    if currCh != len(chArr)-1:
                        pyautogui.moveTo(chArr[currCh+1].x, chArr[currCh+1].y)
                elif info.dwPOV == 27000:
                    if currCh != 0:
                        pyautogui.moveTo(chArr[currCh-1].x, chArr[currCh-1].y)
                return

            # if the enemy is attacking, or if i am attacking () to give choice on where to defense
            # len(gameMatrix[2]) > len(gameMatrix[4]) and
            if win32api.GetAsyncKeyState(0x01) < 0: #if left click is being clicked
                if len(gameMatrix[2]) > len(gameMatrix[4]):
                    atk = 2 #whos attacking
                    lineY = 450 #where is the line of defense
                else:
                    atk = 4
                    lineY = 690
                if info.dwPOV == 9000:  # right
                    for i, p in enumerate(gameMatrix[atk]):
                        if( abs(p.x - pyautogui.position().x) < 20  and  i != len(gameMatrix[atk])-1 ):
                            pyautogui.moveTo(gameMatrix[atk][i+1].x, 1080-lineY, 0.1)
                            break
                elif info.dwPOV == 27000:  # left
                    for i, p in enumerate(gameMatrix[atk]):
                        if( abs(p.x - pyautogui.position().x) < 20 and i != 0 ):
                            pyautogui.moveTo(gameMatrix[atk][i-1].x, 1080-lineY, 0.1)
                            break
                elif info.dwPOV == 18000 and atk == 2: # down
                    pyautogui.moveRel(0, 250, 0.1)
                    pyautogui.mouseUp()
                elif info.dwPOV == 0 and atk == 4:  # up
                    pyautogui.moveRel(0, -250, 0.1)
                    pyautogui.mouseUp()
                return

            move = True
            if (curI, curJ) == (-1, -1):
                curI, curJ = 7, 0   # will be decremented to 6, 0
                moveUpMatrix()
            elif info.dwPOV == 0:
                if(curI == 6):
                    pyautogui.moveTo(1919, 1079)
                moveUpMatrix()
            elif info.dwPOV == 9000:
                moveRightMatrix()
            elif info.dwPOV == 18000:
                moveDownMatrix()
            elif info.dwPOV == 27000:
                moveLeftMatrix()
        
        if btns[1]:   # Croce
            if(win32api.GetAsyncKeyState(0x01) < 0):
                pyautogui.mouseUp()
            else:
                pyautogui.click()


        if btns[0]:    # Quadrato
            if curI == 6: #from hand
                pyautogui.dragRel(0, -400, 0.2, button='left')
            elif curI == 5:  # from board
                # check if the enemy is attacking, to give choice on where to defense
                if len(gameMatrix[2]) > len(gameMatrix[4]):
                    pyautogui.mouseDown()  # keep the mouse clicked, to choose where to put the card
                    pyautogui.moveTo(gameMatrix[2][math.floor(len(gameMatrix[2])/2)].x, 1080-450, 0.1)
                else:
                    pyautogui.mouseDown()
                    pyautogui.moveRel(0, -200, 0.1)
                    pyautogui.mouseUp()
            elif curI == 1:
                # check if i am attacking, to select vulnerable enemies
                if len(gameMatrix[4]) > len(gameMatrix[2]):
                    pyautogui.mouseDown() #keep the mouse clicked, to choose where to put the card
                    pyautogui.moveTo(gameMatrix[4][math.floor(len(gameMatrix[4])/2)].x, 1080-690, 0.1)
                
            cdCounter = 0

        if btns[3]:   # Triangolo
            pyautogui.moveTo(1670, 540)
            pyautogui.click()
            toogleMatrix()
            cdCounter = 0

        if btns[2]:   # Cerchio
            if abs(pyautogui.position().y - height/2) < 20:
                pyautogui.mouseDown()
                pyautogui.moveTo(pyautogui.position().x, 1000, 0.1)
                pyautogui.mouseUp()
                toogleMatrix()
                cdCounter = 0

        if len(btns) > 12:
            if btns[12]:
                toogleMatrix()
                cdCounter = 0
            

DELAY = 1/30
COOLDOWN = 1 / DELAY / 20  # clicks per second
cdCounter = 0

num = joystickapi.joyGetNumDevs()
ret, caps, startinfo = False, None, None
for id in range(num):
    ret, caps = joystickapi.joyGetDevCaps(id)
    if ret:
        print("gamepad detected: " + caps.szPname)
        ret, startinfo = joystickapi.joyGetPosEx(id)
        break
else:
    print("no gamepad detected")

gameData = json.loads(urllib.request.urlopen("http://localhost:21337/positional-rectangles").read())
_thread.start_new_thread(getGameData, ())

run = ret

#----------------------------------------------------------------------------------------------#
move = True
while run:
    cdCounter += 1
    time.sleep(DELAY)

    if( cdCounter > COOLDOWN ):
        input()
        if(move):
            if (curI, curJ) != (-1, -1):
                print(gameMatrix[curI][curJ].x, ' - ', 1080 - gameMatrix[curI][curJ].y)
                pyautogui.moveTo(gameMatrix[curI][curJ].x, 1080 - gameMatrix[curI][curJ].y)
            else:
                pyautogui.moveTo(1919, 1079)
            move = False
