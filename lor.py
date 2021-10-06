import copy
import json
import math
import threading
import time
import urllib.request
from datetime import datetime

import win32api
from win32con import *

import joystickapi

gameMatrix = [[],[],[],[],[],[],[]]
newMatrix = [[],[],[],[],[],[],[]]
lostCards = []
width, height = 1920, 1080
curI, curJ = -1, -1   #joystick cursor current position in the matrix
LSTICK_SPEED = 27


#i made these depending on each other to change less code when moving to another OS
def getMouseX():
    x, y = win32api.GetCursorPos()
    return x
def getMouseY():
    x, y = win32api.GetCursorPos()
    return y

def moveMouseTo(x, y):
    win32api.SetCursorPos((int(x), int(y)))
def moveMouseRel(x, y):
    moveMouseTo(x + getMouseX(), y + getMouseY())

def isLeftClicked():
    return win32api.GetAsyncKeyState(0x01) < 0

def moveWheel(dir):
    win32api.mouse_event(MOUSEEVENTF_WHEEL, getMouseX(), getMouseY(), dir, 0)

def mouseClick():
    mouseDown()
    mouseUp()

def mouseDown():
    win32api.mouse_event(MOUSEEVENTF_LEFTDOWN, getMouseX(), getMouseY())
def mouseUp():
    win32api.mouse_event(MOUSEEVENTF_LEFTUP, getMouseX(), getMouseY())

def mouseDragRel(x, y):
    mouseDragTo(x + getMouseX(), y + getMouseY())
def mouseDragTo(x, y):
    mouseDown()
    time.sleep(0.1)
    moveMouseTo(x, y)
    time.sleep(0.1)
    mouseUp()


class Point:
    def __init__(self, x, y, id, cardCode, localPlayer):
        self.x = x
        self.y = y
        self.id = id
        self.cardCode = cardCode
        self.localPlayer = localPlayer
    def __repr__(self):
        return str(self.x)+' '+str(self.y)+' '+str(self.id)+'\n'
    def __eq__(self, other):
        return self.id == other.id


def handHovering():
    return height - getMouseY() < 90 and getMouseX() < 1700 and getMouseX() > 220
def coord(card):
    return Point(card['TopLeftX']+card['Width']/2, card['TopLeftY']-card['Height']/2, card['CardID'], card['CardCode'], card['LocalPlayer'])
def enemyHandCoord(card):
    return Point(card['TopLeftX']+card['Width']/2, 1065, card['CardID'], card['CardCode'], card['LocalPlayer'])
def handCoord(card):
    return Point(card['TopLeftX']+card['Width']/4, 40, card['CardID'], card['CardCode'], card['LocalPlayer'])


def getGameData():
    global gameData, gameMatrix, newMatrix, keepCursorOnCard, lostCards
    theoricalTime = 0
    startTime = datetime.now()
    while True:
        try:
            gameData = json.loads(urllib.request.urlopen("http://localhost:21337/positional-rectangles").read())

            if(handHovering()):
                newMatrix = [[], [], [], [], [], [], gameMatrix[6]]
            else:
                newMatrix = [[], [], [], [], [], [], []]
            lostCards = []

            for card in gameData['Rectangles']:
                if(card['CardCode'] == 'face'):
                    lostCards.append(coord(card))
                elif(card['TopLeftY'] > 1030):
                    newMatrix[0].append(enemyHandCoord(card))
                elif(card['Height'] < 180 and card['TopLeftY'] > 950 and card['TopLeftY'] < 1000):
                    newMatrix[1].append(coord(card))
                elif(card['Height'] < 180 and card['TopLeftY'] > 780 and card['TopLeftY'] < 830):
                    newMatrix[2].append(coord(card))
                elif(card['Height'] < 120 and card['Height'] > 110 and card['Width'] < 120 and card['Width'] > 110):
                    newMatrix[3].append(coord(card))
                elif(card['Height'] < 180 and card['TopLeftY'] > 430 and card['TopLeftY'] < 480):
                    newMatrix[4].append(coord(card))
                elif(card['Height'] < 180 and card['TopLeftY'] > 240 and card['TopLeftY'] < 280):
                    newMatrix[5].append(coord(card))
                elif(card['TopLeftY'] < 150 and not handHovering()):
                    newMatrix[6].append(handCoord(card))
                else:
                    lostCards.append(coord(card))

            for a in newMatrix:
                a.sort(key=lambda x: x.x)


            theoricalTime += 4  # adds 4 seconds to the time it should be
            # finds out how much time actually passed
            actualTime = datetime.now() - startTime
            # waits to stay in track witht the theorical time, and doing so all the threads stay synchronized
            time.sleep(theoricalTime - (actualTime.seconds + actualTime.microseconds/1000000))
        except:
            print('ERROR! lor closed or you haven\'t enabled settings>third party tools>enable')

def choiceNumber():
    n = 0
    for card in gameData['Rectangles']:
        if card['Height'] < 140:
            continue
        if card['TopLeftY'] > height / 2 and card['TopLeftY']-card['Height'] < height / 2:
            n += 1
    return n

lastCardInChoice = None
def checkChoice(): # i know its wierdly coded, but i had to consider taht when you draw a card, the card goes into the middle of the screen
    global lastCardInChoice
    ca = choiceArray()
    if len(ca) == 1:
        if lastCardInChoice:
            if lastCardInChoice.x == ca.x and lastCardInChoice.y == ca.y:
                lastCardInChoice = None
                return True
        lastCardInChoice = ca[0]
    elif len(ca) > 1:
        lastCardInChoice = None
        return True

    lastCardInChoice = None
    return False

def choiceArray():  # how many cards are you choosing?
    maxH = 0  # maxHeight
    arr = []
    for card in gameData['Rectangles']:
        if (card['Height'] > maxH):
            maxH = card['Height']
            arr = [coord(card)]
        elif (card['Height'] == maxH):
            arr.append(coord(card))
    arr.sort(key=lambda x: x.x)
    return arr

def moveToMatrix(i, j):
    global curI, curJ, gameMatrix
    curI, curJ = i, j
    if (curI, curJ) != (-1, -1):
        moveMouseTo(gameMatrix[curI][curJ].x, 1080 - gameMatrix[curI][curJ].y)
    else:
        moveMouseTo(1918, 1078)


def moveCursorToId(nextCardId):
    global lostCards

    if choiceNumber():  # while a card like conchologist is being played, he is still in the animation while you choose, i return so that after you choose, the cursor will still move into him
        return

    for lost in lostCards:
        if nextCardId == lost.id:
            moveMouseTo(lost.x, lost.y)
            return False

    for i, row in enumerate(gameMatrix):
        for j, c in enumerate(row):
            if c.id == nextCardId:
                moveToMatrix(i, j)
                return True

    print('BIG ERROR A CARD FOOKING DISAPPEARED, WTF RIOT')
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
    if curJ < 0:
        toogleMatrix()
    else:
        curJ -= 1
def toogleMatrix():
    global curI, curJ
    curI, curJ = -1, -1

def allyNexusPoint():
    for l in lostCards:
        if l.cardCode == 'face' and l.localPlayer == True:
            return l
def enemyNexusPoint():
    for l in lostCards:
        if l.cardCode == 'face' and l.localPlayer == False:
            return l

#left stick act as a mouse, also runs as a different thread
def LStickMouse():
    global id, ret
    clickCoolDown = 0
    while(True):
        time.sleep(1/100)
        if len(gameData['Rectangles']) != 0:
            continue

        ret, info = joystickapi.joyGetPosEx(id)
        btns = [(1 << i) & info.dwButtons != 0 for i in range(caps.wNumButtons)]
        if info.dwButtons:
            print("buttons: ", btns)

        #[info.dwZpos-startinfo.dwZpos, info.dwRpos-startinfo.dwRpos]
        LeftStick = lambda: None
        RightStick = lambda: None
        LeftStick.x = (info.dwXpos-startinfo.dwXpos) / 32768 #2^15
        LeftStick.y = (info.dwYpos-startinfo.dwYpos) / 32768
        RightStick.y = (info.dwRpos-startinfo.dwRpos) / 32768

        #print('x: ', LeftStick.x, '    y: ', LeftStick.y)
        if abs(LeftStick.x) > 0.1 or abs(LeftStick.y) > 0.1:
            moveMouseRel(LeftStick.x * LSTICK_SPEED, LeftStick.y * LSTICK_SPEED)
        
        if abs(RightStick.y) > 0.5:
            moveWheel(-1*int(round(RightStick.y)))

        if len(gameData['Rectangles']) == 0:
            if(clickCoolDown == 10):
                if btns[2]:   # Circle
                    mouseClick()
                    clickCoolDown = 0
                if btns[1]:   # Cross
                    mouseClick()
                    clickCoolDown = 0
            else:
                clickCoolDown += 1

def input():
    global run, ret, curI, curJ, caps, id, keepCursorOnCard
    if len(gameData['Rectangles']) == 0: #if not in game
        return True #returns true to save some processing power

    ret, info = joystickapi.joyGetPosEx(id)
    
    if ret:
        btns = [(1 << i) & info.dwButtons != 0 for i in range(caps.wNumButtons)]
        if info.dwButtons:
            print("buttons: ", btns)

        if info.dwPOV != 65535: #arrows
            print(info.dwPOV)
            # check if there is a choice to make
            if checkChoice():
                print('check choice', checkChoice())
                chArr = choiceArray() # ch = choice
                currCh = -1
                for i, ch in enumerate(chArr):
                    if abs(ch.x - getMouseX()) < 20:
                        currCh = i
                        break

                if currCh == -1: #if you are not hovering any card in the choice
                    if info.dwPOV == 27000 or info.dwPOV == 0 or info.dwPOV == 18000 or info.dwPOV == 9000:
                        moveMouseTo(chArr[math.floor(len(chArr)/2)].x, chArr[math.floor(len(chArr)/2)].y)
                elif info.dwPOV == 9000:
                    if currCh != len(chArr)-1:
                        moveMouseTo(chArr[currCh+1].x, chArr[currCh+1].y)
                elif info.dwPOV == 27000:
                    if currCh != 0:
                        moveMouseTo(chArr[currCh-1].x, chArr[currCh-1].y)
                return True

            # if the enemy is attacking, or if i am attacking. it gives a choice on where to defende
            if isLeftClicked(): #if left click is being clicked
                if len(gameMatrix[2]) > len(gameMatrix[4]):
                    atk = 2 #whos attacking
                    lineY = 450 #where is the line of defense
                else:
                    atk = 4
                    lineY = 690
                if info.dwPOV == 9000:  # right
                    for i, p in enumerate(gameMatrix[atk]):
                        if( abs(p.x - getMouseX()) < 20 and i != len(gameMatrix[atk])-1 ):
                            moveMouseTo(gameMatrix[atk][i+1].x, 1080-lineY)
                            break
                elif info.dwPOV == 27000:  # left
                    for i, p in enumerate(gameMatrix[atk]):
                        if( abs(p.x - getMouseX()) < 20 and i != 0 ):
                            moveMouseTo(gameMatrix[atk][i-1].x, 1080-lineY)
                            break
                elif info.dwPOV == 18000 and atk == 2: # down
                    moveMouseRel(0, 250)
                    mouseUp()
                elif info.dwPOV == 0 and atk == 4:  # up
                    moveMouseRel(0, -250)
                    mouseUp()
                return True


            if (curI, curJ) == (-1, -1): # if i click anything while being on nothing, go to my hand
                curI, curJ = 7, 0   # will be decremented to 6, 0
                moveUpMatrix()

            elif info.dwPOV == 0: #up
                if(curI == 6): moveMouseTo(1919, 1079), time.sleep(0.1) #make the hand stop covering the board
                moveUpMatrix()

            elif info.dwPOV == 9000:  #right
                if(curI == 0): moveMouseTo(1919, 1079), time.sleep(0.1) #make the enemy hand stop covering the enemy hand
                moveRightMatrix()

            elif info.dwPOV == 18000: #down
                if(curI == 0): moveMouseTo(1919, 1079), time.sleep(0.1) #make the enemy hand stop covering the board
                moveDownMatrix()

            elif info.dwPOV == 27000:  # left
                if(curI == 0): moveMouseTo(1919, 1079), time.sleep(0.1) #make the enemyhand stop covering the enemy hand
                if curJ == 0: # move to the nexus
                    if curI > 3:
                        moveMouseTo( allyNexusPoint().x, 1080-allyNexusPoint().y )
                    elif curI < 3:
                        moveMouseTo( enemyNexusPoint().x, 1080-enemyNexusPoint().y )
                    curJ = -1
                    return True
                else:
                    moveLeftMatrix()

            moveToMatrix(curI, curJ)
            return True
            
        if btns[1]:   # Cross
            if(isLeftClicked()):
                mouseUp()
            else:
                mouseClick()
            return True

        if btns[0]:   # Square
            if curI == 6:  # from hand
                keepCursorOnCard = gameMatrix[curI][curJ].id
                mouseDragRel(0, -400)
            elif curI == 5:  # from board
                # check if the enemy is attacking, to give choice on where to defense
                if len(gameMatrix[2]) > len(gameMatrix[4]):
                    keepCursorOnCard = gameMatrix[curI][curJ].id
                    mouseDown()  # keep the mouse clicked, to choose where to put the card
                    time.sleep(0.1)
                    moveMouseTo(gameMatrix[2][math.floor(len(gameMatrix[2])/2)].x, 1080-450)
                else: #i am attacking
                    keepCursorOnCard = gameMatrix[curI][curJ].id
                    mouseDragRel(0, -200)
            elif curI == 1:
                # check if i am attacking, to select vulnerable enemies
                if len(gameMatrix[4]) > len(gameMatrix[2]):
                    mouseDown()  # keep the mouse clicked, to choose where to put the card
                    time.sleep(0.1)
                    moveMouseTo(gameMatrix[4][math.floor(len(gameMatrix[4])/2)].x, 1080-690)
            return True
                
        if btns[3]:   # Triangle
            moveMouseTo(1670, 540)
            mouseClick()
            toogleMatrix()
            return True

        if btns[2]:   # Circle
            if curI == 3:
                keepCursorOnCard = gameMatrix[curI][curJ].id
                mouseDragTo(getMouseX(), 1000)
            elif curI == 2:
                keepCursorOnCard = gameMatrix[curI][curJ].id
                mouseDragRel(0, -250)
            elif curI == 4:
                keepCursorOnCard = gameMatrix[curI][curJ].id
                mouseDragRel(0, 250)
            return True

    return False


num = joystickapi.joyGetNumDevs()
print('gamepad connected = ', num)
ret, caps, startinfo = False, None, None
for id in range(num):
    ret, caps = joystickapi.joyGetDevCaps(id)
    if ret:
        print("gamepad detected: " + caps.szPname)
        ret, startinfo = joystickapi.joyGetPosEx(id)
        break
    else:
        print("no gamepad detected")


run = ret
keepCursorOnCard = -1
gameData = json.loads(urllib.request.urlopen("http://localhost:21337/positional-rectangles").read())

# 6 inputs per second (except it takes a bit to process every input so it's less)
DELAY = 1/10
buttonPressed = False
#start N_THREAD thread because the data dragon api from LOR has a 2 seconds cooldown before responding to the same process
#but i made it a 4 seconds between each request, to keep the different threads synchronized
N_THREAD = 16

lStickTh = threading.Thread(target=LStickMouse)
lStickTh.start()

th = [None] * N_THREAD   #N_THREAD length array
for i in range(N_THREAD):
    th[i] = threading.Thread(target=getGameData)
for t in th:
    time.sleep(4/N_THREAD)
    t.start()

#----------------------------------------------------------------------------------------------#
while run:
    gameMatrix = copy.deepcopy(newMatrix) # gets the newMatrix asynchronously but only uses it synchronously, so it doesnt change while doing random instruction leading to crash
    
    if(keepCursorOnCard != -1 and not isLeftClicked()):
        # True if the card is in the matrix, False if its in the animation
        if moveCursorToId(keepCursorOnCard):
            keepCursorOnCard = -1
            
    if buttonPressed:  # if last cycle was an input, waits a cooldown, if it wasn't check for input
        buttonPressed = False
        time.sleep(DELAY)
    else:
        buttonPressed = input()
        time.sleep(0.03)
