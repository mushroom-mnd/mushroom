# Version 1.0
import cv2
import mediapipe as mp
import pyautogui
import time
import threading
import tkinter as tk
import ctypes
import sys
import webbrowser
import subprocess
from enum import Enum
if sys.platform == "win32":
  import win32gui
  import win32con

#################################################################
# Default system Constants (override from config.txt at startup)
#################################################################
screen_w, screen_h = pyautogui.size()

CONTROL_OPTION = 1  # 1 means use eye blinking and smile, 2 = blinking only.
SMILE_LEVEL = 0

# Config file setting
EYE_CLOSED_COUNTER = 0  # eye close detection in seconds
SCROLL_DELAY = 0  # Set icon scroll delay timer in seconds
CURSOR_MOVE_SPEED_X = 0 # Set cursor moving speed
CURSOR_MOVE_SPEED_Y = 0
ENABLE_KEYBOARD_OPTION = 0
ENABLE_FAVOR_OPTION = 0
ENABLE_HOTKEY_OPTION = 0
ENABLE_CLOSE_APPLICATION_OPTION = 0

#################################################################
# Initial global constants
##### Cursor/Mouse related #####################
MOVE_X = 0
MOVE_Y = 0
SCREEN_WORK_AREA_X = 0  # The starting workaround position
SCREEN_WORK_AREA_Y = 0
FIRST_ROUND_QUAD_INDEX = 0
SECOND_ROUND_QUAD_INDEX = 0
DRAG_START_X = 0
DRAG_START_Y = 0
DRAG_IN_PROGRESS = False
##### Keyboard related #########################
CAP_LOCK = False
CTRL_LOCK = False
SHIFT_LOCK = False
SYMBOL_LOCK = False
ALT_LOCK = False
SELECTED_TWO_COLUMNS = 0
SELECTED_ONE_COLUMN  = 0
FINAL_COLUMN_IDX = 0
SELECTED_ONE_KEYBOARD = 0
##### Favor and hotkey related #####################
FAVOR_CHOICE = 0
FAVOR_LINKS = []
HOTKEY_CHOICE = 0
BLINK_CHOICE = 0
STOP_EVENT = None

# State Machine (SM) and its msg.
class SM(Enum):
  PROGRAM_STARTED_STATE = 0
  MINIMIZE_MENU_STATE = 1
  PARK_STATE = 2
  CURSOR_SECTION_CHOICE_ROUND1_STATE = 3
  CURSOR_SECTION_CHOICE_ROUND2_STATE = 5
  CURSOR_SECTION_CONFIRMED_ROUND2_STATE = 6  
  MOVE_CURSOR_X_STATE = 7
  CONFIRM_CURSOR_X_STATE = 8
  MOVE_CURSOR_Y_STATE = 9
  CONFIRM_CURSOR_Y_STATE = 10
  CLICK_MOUSE_CHOICE_STATE = 11
  CLICK_LEFT_BUTTON_STATE = 12
  DOUBLE_CLICK_BUTTON_STATE = 13
  CLICK_MIDDLE_BUTTON_STATE = 14
  CLICK_RIGHT_BUTTON_STATE = 15
  DRAG_MOUSE_STATE = 16

  SHOW_KEYBOARD_ALPHA_STATE = 17
  LIGHT_UP_TWO_COLUMNS_KEYBOARDS = 18
  LIGHT_UP_ONE_COLUMN_KEYBOARDS = 19
  LIGHT_UP_FOUR_KEYBOARDS_CHOICE = 20
  SELECTED_KEY_STATE = 21
  
  FAVOR_SELECTION_STATE = 22
  FAVOR_SELECTED_STATE = 23
  MORE_FAVOR_STATE = 24
  HOTKEY_SELECTION_STATE = 25
  HOTKEY_SELECTED_STATE = 26
  MORE_HOTKEY_STATE = 27  
  CONFIRM_ENDED_STATE = 40
  
  PROGRAM_ENDED_STATE = 99
  ERROR_STATE = 80

STATE = SM.PROGRAM_STARTED_STATE

# Define the APPBARDATA structure
class APPBARDATA(ctypes.Structure):
  _fields_ = [
      ("cbSize", ctypes.c_uint),
      ("hWnd", ctypes.c_void_p),
      ("uCallbackMessage", ctypes.c_uint),
      ("uEdge", ctypes.c_uint),
      ("rc", ctypes.wintypes.RECT),
      ("lParam", ctypes.c_long),
  ]
    
#################################################################
# Windows OS specific functions...
#################################################################
# Function to get the height of the taskbar
def get_taskbar_height():
  ABM_GETTASKBARPOS = 5
  abd = APPBARDATA()
  abd.cbSize = ctypes.sizeof(APPBARDATA)
  shell32 = ctypes.windll.shell32
  result = shell32.SHAppBarMessage(ABM_GETTASKBARPOS, ctypes.byref(abd))
  if result:
      return abd.rc.bottom - abd.rc.top
  else:
      return None

#################################################################
# Helper function to read config file.
#################################################################   
def read_config(filename):
  config = {}
  with open(filename, 'r') as file:
    for line in file:
      if line.strip():  # Skip empty lines
        key, value = line.strip().split('===')
        key = key.strip()
        value = value.strip()
        # Check if the value is numeric or a string
        if value.isdigit():  # Check if the value is an integer
          config[key] = int(value)
        else:
          config[key] = value
  return config

#################################################################
# Helper function for cursor section setup.
#################################################################   
def setupCursorSection():
  global STATE
  global FIRST_ROUND_QUAD_INDEX 
  global SECOND_ROUND_QUAD_INDEX 
  global MOVE_X
  global MOVE_Y
  global SCREEN_WORK_AREA_X
  global SCREEN_WORK_AREA_Y

  screenWorkAreaWidth = screen_w // 4
  screenWorkAreaHeight = screen_h // 4
  
  # Upper-left hand side, x,y starts with 0
  if FIRST_ROUND_QUAD_INDEX == 1:
    if (SECOND_ROUND_QUAD_INDEX == 1):
      SCREEN_WORK_AREA_X = 0
      SCREEN_WORK_AREA_Y = 0
      MOVE_X = screenWorkAreaWidth / 2 # Center point of work area
      MOVE_Y = screenWorkAreaHeight / 2    
    elif (SECOND_ROUND_QUAD_INDEX == 2):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth
      SCREEN_WORK_AREA_Y = 0
      MOVE_X = (SCREEN_WORK_AREA_X / 2) + screenWorkAreaWidth # Center point of work area
      MOVE_Y = screenWorkAreaHeight / 2    
    elif (SECOND_ROUND_QUAD_INDEX == 3):
      SCREEN_WORK_AREA_X = 0
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight
      MOVE_X = screenWorkAreaWidth / 2
      MOVE_Y = (SCREEN_WORK_AREA_Y / 2) + screenWorkAreaHeight 
    elif (SECOND_ROUND_QUAD_INDEX == 4):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight
      MOVE_X = (SCREEN_WORK_AREA_X / 2) + screenWorkAreaWidth
      MOVE_Y = (SCREEN_WORK_AREA_Y / 2) + screenWorkAreaHeight 

  elif FIRST_ROUND_QUAD_INDEX == 2:
    if (SECOND_ROUND_QUAD_INDEX == 1):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth * 2
      SCREEN_WORK_AREA_Y = 0
      MOVE_X = (screenWorkAreaWidth / 2) * 5 # Center point of work area
      MOVE_Y = screenWorkAreaHeight / 2    
    elif (SECOND_ROUND_QUAD_INDEX == 2):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth * 3
      SCREEN_WORK_AREA_Y = 0
      MOVE_X = (screenWorkAreaWidth / 2) * 7
      MOVE_Y = screenWorkAreaHeight / 2    
    elif (SECOND_ROUND_QUAD_INDEX == 3):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth * 2      
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight
      MOVE_X = (screenWorkAreaWidth / 2) * 5
      MOVE_Y = (screenWorkAreaHeight / 2) * 3
    elif (SECOND_ROUND_QUAD_INDEX == 4):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth * 3
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight
      MOVE_X = (screenWorkAreaWidth / 2) * 7
      MOVE_Y = (screenWorkAreaHeight / 2) * 3

  elif FIRST_ROUND_QUAD_INDEX == 3:
    if (SECOND_ROUND_QUAD_INDEX == 1):
      SCREEN_WORK_AREA_X = 0
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight * 2      
      MOVE_X = (screenWorkAreaWidth / 2)
      MOVE_Y = (screenWorkAreaHeight / 2) * 5    
    elif (SECOND_ROUND_QUAD_INDEX == 2):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight * 2          
      MOVE_X = (screenWorkAreaWidth / 2) * 3
      MOVE_Y = (screenWorkAreaHeight / 2) * 5     
    elif (SECOND_ROUND_QUAD_INDEX == 3):
      SCREEN_WORK_AREA_X = 0
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight * 3
      MOVE_X = screenWorkAreaWidth / 2
      MOVE_Y = (screenWorkAreaHeight / 2) * 7
    elif (SECOND_ROUND_QUAD_INDEX == 4):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight * 3
      MOVE_X = (SCREEN_WORK_AREA_X / 2) + screenWorkAreaWidth
      MOVE_Y = (screenWorkAreaHeight / 2) * 7

  elif FIRST_ROUND_QUAD_INDEX == 4:
    if (SECOND_ROUND_QUAD_INDEX == 1):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth * 2
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight * 2      
      MOVE_X = (screenWorkAreaWidth / 2) * 5 # Center point of work area
      MOVE_Y = (screenWorkAreaHeight / 2) * 5    
    elif (SECOND_ROUND_QUAD_INDEX == 2):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth * 3
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight * 2        
      MOVE_X = (screenWorkAreaWidth / 2) * 7
      MOVE_Y = (screenWorkAreaHeight / 2) * 5     
    elif (SECOND_ROUND_QUAD_INDEX == 3):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth * 2
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight * 3      
      MOVE_X = (screenWorkAreaWidth / 2) * 5 
      MOVE_Y = (screenWorkAreaHeight / 2) * 7
    elif (SECOND_ROUND_QUAD_INDEX == 4):
      SCREEN_WORK_AREA_X = screenWorkAreaWidth * 3
      SCREEN_WORK_AREA_Y = screenWorkAreaHeight * 3        
      MOVE_X = (screenWorkAreaWidth / 2) * 7
      MOVE_Y = (screenWorkAreaHeight / 2) * 7
      
  STATE = SM.MOVE_CURSOR_X_STATE

#################################################################
# Helper function for cursor movement X/Y axis.
#################################################################   
def cursorMove():
  global STATE
  global MOVE_X
  global MOVE_Y
  global SCREEN_WORK_AREA_X
  global SCREEN_WORK_AREA_Y
  global CURSOR_MOVE_SPEED_X
  global CURSOR_MOVE_SPEED_Y
  
  moveBackward = False

  screenWorkAreaWidth = screen_w // 4
  screenWorkAreaHeight = screen_h // 4
  
  while True:      
    # Move Cursor on X-axis
    if STATE == SM.MOVE_CURSOR_X_STATE:
      if MOVE_X < SCREEN_WORK_AREA_X and moveBackward:
       moveBackward = False
      elif (MOVE_X > (SCREEN_WORK_AREA_X + screenWorkAreaWidth) and not moveBackward):
       moveBackward = True
          
      if moveBackward:
        MOVE_X -= CURSOR_MOVE_SPEED_X
      else:
        MOVE_X += CURSOR_MOVE_SPEED_X
      pyautogui.moveTo(MOVE_X, MOVE_Y)

    # Move Cursor on Y-axis
    if STATE == SM.MOVE_CURSOR_Y_STATE:
      if MOVE_Y < SCREEN_WORK_AREA_Y and moveBackward:
       moveBackward = False
      if (MOVE_Y > (SCREEN_WORK_AREA_Y + screenWorkAreaHeight) and not moveBackward):
       moveBackward = True
          
      if not moveBackward:
        MOVE_Y += CURSOR_MOVE_SPEED_Y
      else:
        MOVE_Y -= CURSOR_MOVE_SPEED_Y
      pyautogui.moveTo(MOVE_X, MOVE_Y)

#################################################################
# Function to setup the shading window.
#################################################################    
def setupShadingWindow(shadeWindow):

  width = 0
  height = 0
  x_position = 0
  y_position = 0
  savedGeometry = f"{width}x{height}+{x_position}+{y_position}"
  shadeWindow.overrideredirect(True)  # Hide Window title bar
  shadeWindow.geometry(savedGeometry)
  shadeWindow.attributes("-topmost", True)   # Set the window always on top
  shadeWindow.title("")
  shadeWindow.attributes('-alpha', 0.5)

#################################################################
# Function to setup the keyboard layout window.
#################################################################    
def setupKeyboardLblWindow(keyboardMenu, keyboardLbls, images, imgPadding, maxNrOfImagesPerKeyboardMenu, maxNrOfRowsPerMenu):
  
  widthAndHeightPerImage = 64

  # Windows OS check for taskbar.
  tmpTaskbarHeight = None
  if sys.platform == "win32":
      tmpTaskbarHeight = get_taskbar_height()
  taskbar_height = tmpTaskbarHeight
  if taskbar_height is None:
      taskbar_height = 120    

  # Calculate the menu bar position (x, y, width, height)
  width = (widthAndHeightPerImage + (imgPadding * 4)) * maxNrOfImagesPerKeyboardMenu
  height = (widthAndHeightPerImage + (imgPadding * 3)) * maxNrOfRowsPerMenu
  x_position = (screen_w - width) // 2
  y_position = (screen_h - height - taskbar_height - (imgPadding * 2))

  savedGeometry = f"{width}x{height}+{x_position}+{y_position}"
  keyboardMenu.overrideredirect(True)  # Hide Window title bar
  keyboardMenu.geometry(savedGeometry)
  keyboardMenu.attributes("-topmost", True)   # Set the window always on top
  keyboardMenu.title("Eye control - Keyboard menu")
  
  # Load up 8 images to the keyboard labels, will change images on different menu while keeping these labels the same.
  for eachRow in range(maxNrOfRowsPerMenu):
    for i in range(maxNrOfImagesPerKeyboardMenu):
      keyboardLbls.append(tk.Label(keyboardMenu, image=images[i]))
      keyboardLbls[(eachRow * maxNrOfImagesPerKeyboardMenu) + i].grid(row=eachRow, column=i, padx=imgPadding, pady=imgPadding)
  
#################################################################
# Function to setup the label main window.
#################################################################    
def setupLabelWindow(menuBar, labels, images, imgPadding):
  
  maxNrOfImagesPerMenu = 6 # Max number of images to show on a menu.
  widthAndHeightPerImage = 64

  # Windows OS check for taskbar.
  tmpTaskbarHeight = None
  if sys.platform == "win32":
      tmpTaskbarHeight = get_taskbar_height()
  taskbar_height = tmpTaskbarHeight
  if taskbar_height is None:
      taskbar_height = 120    

  # Calculate the menu bar position (x, y, width, height)
  width = (widthAndHeightPerImage + (imgPadding * 4)) * maxNrOfImagesPerMenu
  height = widthAndHeightPerImage + (imgPadding * 3)
  x_position = (screen_w - width) // 2
  y_position = (screen_h - height - taskbar_height - (imgPadding * 2))

  savedGeometry = f"{width}x{height}+{x_position}+{y_position}"
  menuBar.overrideredirect(True)  # Hide Window title bar
  menuBar.geometry(savedGeometry)
  menuBar.attributes("-topmost", True)   # Set the window always on top
  menuBar.title("Eye control")
  
  # Load up 6 images to the labels, will change images on different menu while keeping these labels the same.
  for i in range(maxNrOfImagesPerMenu):
    labels.append(tk.Label(menuBar, image=images[i]))
    labels[i].grid(row=0, column=i, padx=imgPadding, pady=imgPadding)

#################################################################
# Function to read in all the images files.
#################################################################    
def getAllImages(images, maxNrOfImagesForAllMenu):
  imagesPath = []
  for i in range(maxNrOfImagesForAllMenu):
    imagesPath.append("images\\" + str(i) + ".png")
    images.append(tk.PhotoImage(file=imagesPath[i]))

#################################################################
# Function to display icons/text messages in the menuBar.
#################################################################    
def displayMenuBar():
  global STATE
            
  # Create labels, images etc...
  labels = []
  keyboardLbls = []
  images = []
  imgPadding = 5
  maxNrOfImagesForAllMenu = 107

  # Number of images per keyboard menu, number of rows
  nrOfImgPerRow = 10
  maxNrOfRowsPerMenu = 4
  
  # Highlight/normal icon background colors.
  hlColor = "#FF59FF" # light pink
  nlColor = "white"
  
  menuBar = tk.Tk()
  keyboardMenu = tk.Toplevel(menuBar)
  shadeWindow = tk.Toplevel(menuBar)
  pink_frame = None
  pink_frame = tk.Frame(shadeWindow, width=0, height=0, bg="#FFB6C1")
  pink_frame.pack_propagate(False)  # Prevent the frame from resizing
  pink_frame.pack()
  
  getAllImages(images,maxNrOfImagesForAllMenu)
  setupLabelWindow(menuBar, labels, images, imgPadding)
  setupKeyboardLblWindow(keyboardMenu, keyboardLbls, images, imgPadding, nrOfImgPerRow, maxNrOfRowsPerMenu)
  setupShadingWindow(shadeWindow)
  
  # Show each menu for each state machine....
  while STATE.value < SM.PROGRAM_ENDED_STATE.value:
      
    if (STATE == SM.PROGRAM_STARTED_STATE):
      showStartMenu(labels, images, menuBar, keyboardMenu, hlColor, nlColor, 0, 6, 0, SM.PROGRAM_STARTED_STATE)
    elif (STATE == SM.MINIMIZE_MENU_STATE):
      menuBar.withdraw() # Hide the menuBar
      STATE = SM.PARK_STATE
    elif (STATE == SM.CURSOR_SECTION_CHOICE_ROUND1_STATE):
      sectionChoiceImgIdxList = [10, 11, 12, 13]
      showCursorSectionChoiceMenu(labels, images, menuBar, shadeWindow, pink_frame, hlColor, nlColor, 9, sectionChoiceImgIdxList, 1, STATE)

    elif (STATE == SM.CURSOR_SECTION_CHOICE_ROUND2_STATE):
      sectionChoiceImgIdxList = [10, 11, 12, 13]
      showCursorSectionChoiceMenu(labels, images, menuBar, shadeWindow, pink_frame, hlColor, nlColor, 9, sectionChoiceImgIdxList, 2, STATE)

    elif (STATE == SM.CURSOR_SECTION_CONFIRMED_ROUND2_STATE):      
      setupCursorSection()

    elif (STATE == SM.MOVE_CURSOR_X_STATE):
      showCursorSelectInstruction(labels, images, menuBar, nlColor, 14, 15, 16, STATE)

    elif (STATE == SM.MOVE_CURSOR_Y_STATE):
      showCursorSelectInstruction(labels, images, menuBar, nlColor, 17, 15, 16, STATE)
      
    elif (STATE == SM.CONFIRM_CURSOR_X_STATE or STATE == SM.CONFIRM_CURSOR_Y_STATE or STATE == SM.CONFIRM_ENDED_STATE):
      showTwoChoicesMenu(labels, images, menuBar, hlColor, nlColor, 7, 8, STATE)      

    elif (STATE == SM.CLICK_MOUSE_CHOICE_STATE):
      # Clear the shading window
      savedGeometry = f"{0}x{0}+{0}+{0}"
      shadeWindow.geometry(savedGeometry)
      shadeWindow.update()

      if (not DRAG_IN_PROGRESS):    
        cursorActionImgIdxList = [18, 19, 20, 21]
        additionalImgIdx = 22
        showSixChoicesMenu(labels, images, menuBar, hlColor, nlColor, 9, cursorActionImgIdxList, additionalImgIdx, STATE)
      else:
        handleDragAction()
        
    elif (STATE == SM.CLICK_LEFT_BUTTON_STATE):
      clickButtonAction(labels, images, menuBar, hlColor, nlColor, 1, 9, STATE)
    elif (STATE == SM.DOUBLE_CLICK_BUTTON_STATE):
      clickButtonAction(labels, images, menuBar, hlColor, nlColor, 2, 9, STATE)       
    elif (STATE == SM.CLICK_MIDDLE_BUTTON_STATE):
      clickButtonAction(labels, images, menuBar, hlColor, nlColor, 3, 9, STATE)  
    elif (STATE == SM.CLICK_RIGHT_BUTTON_STATE):
      clickButtonAction(labels, images, menuBar, hlColor, nlColor, 4, 9, STATE)  
    elif (STATE == SM.DRAG_MOUSE_STATE):
      clickButtonAction(labels, images, menuBar, hlColor, nlColor, 5, 9, STATE)

    ############# Keyboard ############################
    elif (STATE == SM.SHOW_KEYBOARD_ALPHA_STATE):
      showKeyboard(keyboardLbls, images, menuBar, keyboardMenu, nrOfImgPerRow, maxNrOfRowsPerMenu, hlColor, nlColor, 9, 33, STATE)
    elif (STATE == SM.LIGHT_UP_ONE_COLUMN_KEYBOARDS):
      lightUpOneRowKeyboard(keyboardLbls, keyboardMenu, hlColor, nlColor, nrOfImgPerRow, maxNrOfRowsPerMenu, STATE)
    elif (STATE == SM.LIGHT_UP_FOUR_KEYBOARDS_CHOICE):
      lightUpFourKeyboardChoice(keyboardLbls, keyboardMenu, hlColor, nlColor, nrOfImgPerRow, maxNrOfRowsPerMenu, STATE)
    elif (STATE == SM.SELECTED_KEY_STATE):
      handleSelectedKey(nrOfImgPerRow, maxNrOfRowsPerMenu)
      
    ############# FAVOR ##############################    
    elif (STATE == SM.FAVOR_SELECTION_STATE):
      favorImgIdxList = [24, 25, 26, 27]
      moreImgIdx = 23
      showSixChoicesMenu(labels, images, menuBar, hlColor, nlColor, 9, favorImgIdxList, moreImgIdx, STATE)
    # Handle selected favor choice
    elif (STATE == SM.FAVOR_SELECTED_STATE):
      handleFavorChoice()
    elif (STATE == SM.MORE_FAVOR_STATE):
      favorImgIdxList = [28, 29, 30, 31]
      additionalImgIdx = 32
      showSixChoicesMenu(labels, images, menuBar, hlColor, nlColor, 9, favorImgIdxList, additionalImgIdx, STATE)

    ############# HOTKEYS ##############################         
    elif (STATE == SM.HOTKEY_SELECTION_STATE):
      hotkeyImgIdxList = [43, 44, 45, 46]
      moreImgIdx = 23      
      showSixChoicesMenu(labels, images, menuBar, hlColor, nlColor, 9, hotkeyImgIdxList, moreImgIdx, STATE)
    elif (STATE == SM.HOTKEY_SELECTED_STATE):
      handleHotkeyChoice()
    elif(STATE == SM.MORE_HOTKEY_STATE):
      hotkeyImgIdxList = [50, 77, 78, 48]
      additionalImgIdx = 49      
      showSixChoicesMenu(labels, images, menuBar, hlColor, nlColor, 9, hotkeyImgIdxList, additionalImgIdx, STATE)
      
      
#################################### BEGIN FAVOR FUNCTIONS ####################################
#################################################################
# Function to handle favor choice
#################################################################    
def handleFavorChoice():
  global STATE
  global FAVOR_CHOICE
  global FAVOR_LINKS
  
  if 'http' in FAVOR_LINKS[FAVOR_CHOICE - 1]:
    webbrowser.open(FAVOR_LINKS[FAVOR_CHOICE - 1])
  else:
    subprocess.Popen([FAVOR_LINKS[FAVOR_CHOICE - 1]])
  #print(FAVOR_CHOICE, [FAVOR_LINKS[FAVOR_CHOICE - 1]])
    
  STATE = SM.PROGRAM_STARTED_STATE  

#################################### END FAVOR FUNCTIONS ####################################
  
#################################### KEYBOARD ###############################################
#################################################################
# Function to handle the selected key
#################################################################    
def handleSelectedKey(nrOfImgPerRow, maxNrOfRowsPerMenu):
  global STATE  
  global CAP_LOCK
  global CTRL_LOCK
  global SHIFT_LOCK
  global SYMBOL_LOCK
  global ALT_LOCK
  global FINAL_COLUMN_IDX
  global SELECTED_ONE_KEYBOARD

  finalImgIdx = (nrOfImgPerRow * (SELECTED_ONE_KEYBOARD - 1)) + FINAL_COLUMN_IDX 
  symbolKey = ['-','+','=','<','>','/','\\','?','0','1','2','3','4','5','6','7','8','9']
  alphaKey = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
  if finalImgIdx == 0:  # Go back to main menu
    STATE = SM.PROGRAM_STARTED_STATE
  else:
    shiftKey = ''
    ctrlKey = ''
    altKey = ''
    if SHIFT_LOCK:
      shiftKey = 'shift'
    if CTRL_LOCK:
      ctrlKey = 'ctrl'
    if ALT_LOCK:
      altKey = 'alt'
      
    if not SYMBOL_LOCK: 
      if finalImgIdx == 2: # CAP lock
        CAP_LOCK = not CAP_LOCK
      elif finalImgIdx == 3:
        SHIFT_LOCK = not SHIFT_LOCK
      elif finalImgIdx == 4:
        CTRL_LOCK = not CTRL_LOCK
      elif finalImgIdx == 5:
        ALT_LOCK = not ALT_LOCK
      elif finalImgIdx == 6:
        pyautogui.hotkey('up')
      elif finalImgIdx == 7:
        pyautogui.hotkey('down')
      elif finalImgIdx == 8:
        pyautogui.hotkey('left')
      elif finalImgIdx == 9:
        pyautogui.hotkey('right')
      elif finalImgIdx == 10:
        pyautogui.hotkey('spacebar')
      elif finalImgIdx == 11:
        pyautogui.hotkey('backspace')
      elif finalImgIdx == 12:
        pyautogui.hotkey('enter')
      elif finalImgIdx == 13:
        pyautogui.hotkey('escape')        
    else:
      if finalImgIdx == 2:
        pyautogui.hotkey(':')
      elif finalImgIdx == 3:
        pyautogui.hotkey('.')
      elif finalImgIdx == 4:
        pyautogui.hotkey('_')
      elif finalImgIdx == 5:
        pyautogui.hotkey(',')
      elif finalImgIdx == 6:
        pyautogui.hotkey('pageup')
      elif finalImgIdx == 7:
        pyautogui.hotkey('pagedown')
      elif finalImgIdx == 8:
        pyautogui.hotkey('!')
      elif finalImgIdx == 9:
        pyautogui.hotkey('@')
      elif finalImgIdx == 10:
        pyautogui.hotkey('#')
      elif finalImgIdx == 11:
        pyautogui.hotkey('$')
      elif finalImgIdx == 12:
        pyautogui.hotkey('(')
      elif finalImgIdx == 13:
        pyautogui.hotkey(')')
      
    # Alphabets / symbols
    for idx in range(26):
      if finalImgIdx == 14 + idx:
        if SYMBOL_LOCK:
          pyautogui.hotkey(symbolKey[idx])
        else:  
          if CAP_LOCK:
            pyautogui.hotkey(shiftKey, ctrlKey, altKey, alphaKey[idx].upper())
          else:
            pyautogui.hotkey(shiftKey, ctrlKey, altKey, alphaKey[idx])
                      
    if finalImgIdx == 1: # Symbol lock
      SYMBOL_LOCK = not SYMBOL_LOCK
    
    STATE = SM.SHOW_KEYBOARD_ALPHA_STATE
    
#################################################################
# Function to show keyboard
#################################################################    
def showKeyboard(keyboardLbls, images, menuBar, keyboardMenu, nrOfImgPerRow, maxNrOfRowsPerMenu, hlColor, nlColor, gobackImgIdx, imgIdxNum1, runState):
  global STATE
  global CAP_LOCK
  global CTRL_LOCK
  global SHIFT_LOCK
  global SYMBOL_LOCK
  global ALT_LOCK
  
  # hide the menuBar and show keyboard menu
  menuBar.withdraw()
  keyboardMenu.deiconify()

  imgNumber = imgIdxNum1  # The initial image index of the keyboard (other than the go back to previous menu icon).
  # Reset border color to normal
  keyboardLbls[0].config(image=images[gobackImgIdx], bg=nlColor)
  for i in range(nrOfImgPerRow * maxNrOfRowsPerMenu - 1): # 10 * 4 rows - 1
    # Special handling of certain keyboard images..
    # DEBUG
    if imgIdxNum1 == 33 and SYMBOL_LOCK == True:
      imgIdxNum1 += 1 # Show highlight SYMBOL_LOCK icon

    if not SYMBOL_LOCK:
      if imgIdxNum1 == 35 and CAP_LOCK == True:
        imgIdxNum1 += 1 # Show highlight symbol icon
      elif imgIdxNum1 == 37 and SHIFT_LOCK == True:
        imgIdxNum1 += 1
      elif imgIdxNum1 == 39 and CTRL_LOCK == True:
        imgIdxNum1 += 1
      elif imgIdxNum1 == 41 and ALT_LOCK == True:
        imgIdxNum1 += 1
        
    if SYMBOL_LOCK:
      if imgIdxNum1 == 35:
        imgIdxNum1 = 103
      if imgIdxNum1 == 107:
        imgIdxNum1 = 77  # jump to first symolic icon
    keyboardLbls[i + 1].config(image=images[imgIdxNum1], bg=nlColor)
    # Skip highlight images.
    if imgIdxNum1 == 33 and SYMBOL_LOCK == False:
      imgIdxNum1 += 1
    elif imgIdxNum1 == 35 and CAP_LOCK == False:
      imgIdxNum1 += 1
    elif imgIdxNum1 == 37 and SHIFT_LOCK == False:
      imgIdxNum1 += 1
    elif imgIdxNum1 == 39 and CTRL_LOCK == False:
      imgIdxNum1 += 1
    elif imgIdxNum1 == 41 and ALT_LOCK == False:
      imgIdxNum1 += 1  
    # Advance by one in all cases
    imgIdxNum1 += 1
        
  STATE = SM.LIGHT_UP_TWO_COLUMNS_KEYBOARDS
  
  # Light up keyboard images for first round of selection.
  lightUpTwoRowsKeyboard(keyboardLbls, keyboardMenu, hlColor, nlColor, nrOfImgPerRow, STATE)

#################################################################
# Function to light up 4 images (out of the selected rows).
#################################################################    
def lightUpFourKeyboardChoice(keyboardLbls, keyboardMenu, hlColor, nlColor, nrOfImgPerRow, maxNrOfRowsPerMenu, runState):
  global STATE
  global STOP_EVENT
  global BLINK_CHOICE
  global SCROLL_DELAY
  global SELECTED_TWO_COLUMNS
  global SELECTED_ONE_COLUMN
  global FINAL_COLUMN_IDX

  if SELECTED_TWO_COLUMNS == 1:  # Either column 1 or column 2
    if SELECTED_ONE_COLUMN == 1:
      FINAL_COLUMN_IDX = 0
    else:
      FINAL_COLUMN_IDX = 1
  elif SELECTED_TWO_COLUMNS == 2:  # Either column 3 or column 4
    if SELECTED_ONE_COLUMN == 1:
      FINAL_COLUMN_IDX = 2
    else:
      FINAL_COLUMN_IDX = 3
  elif SELECTED_TWO_COLUMNS == 3:
    if SELECTED_ONE_COLUMN == 1:
      FINAL_COLUMN_IDX = 4
    else:
      FINAL_COLUMN_IDX = 5      
  elif SELECTED_TWO_COLUMNS == 4:
    if SELECTED_ONE_COLUMN == 1:
      FINAL_COLUMN_IDX = 6
    else:
      FINAL_COLUMN_IDX = 7
  elif SELECTED_TWO_COLUMNS == 5:
    if SELECTED_ONE_COLUMN == 1:
      FINAL_COLUMN_IDX = 8
    else:
      FINAL_COLUMN_IDX = 9      

  # Reset border color to normal
  for i in range(nrOfImgPerRow * maxNrOfRowsPerMenu):
    keyboardLbls[i].config(bg=nlColor)
    
  STOP_EVENT.clear()  # Allow wait event to proceed.
  
  # Light up the background
  while STATE == runState:
    # Change background color to light up
    if (STATE == runState):
      keyboardLbls[FINAL_COLUMN_IDX + (nrOfImgPerRow * 0)].config(bg=hlColor)
      keyboardMenu.update()
      BLINK_CHOICE = 1
    if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
      keyboardLbls[FINAL_COLUMN_IDX + (nrOfImgPerRow * 0)].config(bg=nlColor)
      time.sleep(0.8)
      keyboardLbls[FINAL_COLUMN_IDX + (nrOfImgPerRow * 1)].config(bg=hlColor)
      keyboardMenu.update()
      BLINK_CHOICE = 2
    if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
      keyboardLbls[FINAL_COLUMN_IDX + (nrOfImgPerRow * 1)].config(bg=nlColor)
      time.sleep(0.8)
      keyboardLbls[FINAL_COLUMN_IDX + (nrOfImgPerRow * 2)].config(bg=hlColor)
      keyboardMenu.update()
      BLINK_CHOICE = 3
    if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
      keyboardLbls[FINAL_COLUMN_IDX + (nrOfImgPerRow * 2)].config(bg=nlColor)
      time.sleep(0.8)
      keyboardLbls[FINAL_COLUMN_IDX + (nrOfImgPerRow * 3)].config(bg=hlColor)
      keyboardMenu.update()
      BLINK_CHOICE = 4
    if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
      keyboardLbls[FINAL_COLUMN_IDX + (nrOfImgPerRow * 3)].config(bg=nlColor)
      time.sleep(0.8)
      
#################################################################
# Function to light up one rows (out of two rows) of keyboard column images
#################################################################    
def lightUpOneRowKeyboard(keyboardLbls, keyboardMenu, hlColor, nlColor, nrOfImgPerRow, maxNrOfRowsPerMenu, runState):
  global STATE
  global STOP_EVENT
  global BLINK_CHOICE
  global SCROLL_DELAY
  global SELECTED_TWO_COLUMNS

  columnIdx = 0
  if SELECTED_TWO_COLUMNS == 2:
    columnIdx = 2
  elif SELECTED_TWO_COLUMNS == 3:
    columnIdx = 4
  elif SELECTED_TWO_COLUMNS == 4:
    columnIdx = 6

  # Reset border color to normal
  for i in range(nrOfImgPerRow * maxNrOfRowsPerMenu):
    keyboardLbls[i].config(bg=nlColor)

  STOP_EVENT.clear()  # Allow wait event to proceed.
  lightUpLabelList = [columnIdx, columnIdx + 1]
  
  # Light up the background
  while STATE == runState:
    choiceCounter = 1
    # Change background color to light up
    for labelIdx in lightUpLabelList:      
      # Update highlight color only if still within the same menu.
      if (STATE == runState):
        keyboardLbls[labelIdx].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 1 + labelIdx].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 2 + labelIdx].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 3 + labelIdx].config(bg=hlColor)
        keyboardMenu.update()
        BLINK_CHOICE = choiceCounter
      if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
        keyboardLbls[labelIdx].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 1 + labelIdx].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 2 + labelIdx].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 3 + labelIdx].config(bg=nlColor)
        choiceCounter += 1
        time.sleep(0.8)
        
#################################################################
# Function to light up two rows of keyboard column images
#################################################################    
def lightUpTwoRowsKeyboard(keyboardLbls, keyboardMenu, hlColor, nlColor, nrOfImgPerRow, runState):
  global STATE
  global STOP_EVENT
  global BLINK_CHOICE
  global SCROLL_DELAY

  # Reset border color to normal
  for i in range(40):
    keyboardLbls[i].config(bg=nlColor)
    
  STOP_EVENT.clear()  # Allow wait event to proceed.

  lightUpLabelList = [0, 2, 4, 6, 8]

  # Light up the background
  while STATE == runState:
    choiceCounter = 1
    # Change background color to light up
    for labelIdx in lightUpLabelList:      
      # Update highlight color only if still within the same menu.
      if (STATE == runState):
        keyboardLbls[labelIdx].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 1 + labelIdx].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 2 + labelIdx].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 3 + labelIdx].config(bg=hlColor)
        keyboardLbls[labelIdx + 1].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 1 + labelIdx + 1].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 2 + labelIdx + 1].config(bg=hlColor)
        keyboardLbls[nrOfImgPerRow * 3 + labelIdx + 1].config(bg=hlColor)
        keyboardMenu.update()
        BLINK_CHOICE = choiceCounter
      if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
        keyboardLbls[labelIdx].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 1 + labelIdx].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 2 + labelIdx].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 3 + labelIdx].config(bg=nlColor)
        keyboardLbls[labelIdx + 1].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 1 + labelIdx + 1].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 2 + labelIdx + 1].config(bg=nlColor)
        keyboardLbls[nrOfImgPerRow * 3 + labelIdx + 1].config(bg=nlColor)
        choiceCounter += 1
        time.sleep(0.8)

#################################### BEGIN CURSOR/MOUSE FUNCTIONS ####################################
      
#################################################################
# Function to handle drag action
#################################################################    
def handleDragAction():
  global DRAG_START_X
  global DRAG_START_Y
  global STATE

  # Drag the mouse to the ending position.
  dragEndX, dragEndY = pyautogui.position()

  # Move the cursor back to the starting point
  pyautogui.moveTo(DRAG_START_X, DRAG_START_Y)

  pyautogui.mouseDown() # Simulate mouse down to start dragging

  # Move the cursor to the ending point while holding the mouse button
  pyautogui.moveTo(dragEndX, dragEndY)

  # Simulate mouse up to release the mouse button
  pyautogui.mouseUp()  

  STATE = SM.PROGRAM_STARTED_STATE
  
#################################################################
# Function to perform click button action
#################################################################    
def clickButtonAction(labels, images, menuBar, hlColor, nlColor, clickButton, startImgIdx, runState):
  global STATE
  global STOP_EVENT
  global BLINK_CHOICE
  global DRAG_START_X
  global DRAG_START_Y
  global DRAG_IN_PROGRESS

  if clickButton == 1: # left click
    pyautogui.click()
    STATE = SM.PROGRAM_STARTED_STATE
  elif clickButton == 2: # double click
    pyautogui.click(clicks=2, interval=0.2)
    STATE = SM.PROGRAM_STARTED_STATE    
  elif clickButton ==3: # middle click
    pyautogui.click(button='middle')
    STATE = SM.HOTKEY_SELECTION_STATE
  elif clickButton == 4: # right click
    pyautogui.click(button='right')
    STATE = SM.HOTKEY_SELECTION_STATE    
  elif clickButton == 5: # drag cursor
    DRAG_START_X, DRAG_START_Y = pyautogui.position() # record the starting x,y position.
    DRAG_IN_PROGRESS = True
    STATE = SM.CURSOR_SECTION_CHOICE_ROUND1_STATE  # Go back to the cursor state to capture the DRAG_END_X and DRAG_END_Y

#################################################################
# Function to show the quad shading.
#################################################################    
def showShadingWindow(shadeWindow, pink_frame, roundNum, quadNum):
  global FIRST_ROUND_QUAD_INDEX
  
  x_position = 0
  y_position = 0
  width = 0
  height = 0
  
  if roundNum == 1:
    width = screen_w // 2
    height = screen_h // 2
    if (quadNum == 1):
      x_position = 0
      y_position = 0
    elif (quadNum == 2):
      x_position = screen_w // 2
    elif (quadNum == 3):
      y_position = screen_h // 2
    elif (quadNum == 4):
      x_position = screen_w // 2
      y_position = screen_h // 2
    else:
      width = 0
      height = 0
  else: # Second round
    width = screen_w // 4
    height = screen_h // 4
    if FIRST_ROUND_QUAD_INDEX == 1:
      if (quadNum == 1):
        width = screen_w // 4
        height = screen_h // 4
      elif (quadNum == 2):
        x_position = screen_w // 4
      elif (quadNum == 3):
        y_position = screen_h // 4
      elif (quadNum == 4):
        x_position = screen_w // 4
        y_position = screen_h // 4
      else:
        width = 0
        height = 0

    elif FIRST_ROUND_QUAD_INDEX == 2:
      if (quadNum == 1):
        x_position = screen_w // 2
      elif (quadNum == 2):
        x_position = (screen_w // 4) * 3
      elif (quadNum == 3):
        x_position = screen_w // 2
        y_position = screen_h // 4    
      elif (quadNum == 4):
        x_position = (screen_w // 4) * 3
        y_position = screen_h // 4
      else:
        width = 0
        height = 0

    elif FIRST_ROUND_QUAD_INDEX == 3:
      if (quadNum == 1):
        y_position = screen_h // 2
      elif (quadNum == 2):
        x_position = (screen_w // 4)
        y_position = (screen_h // 2)
      elif (quadNum == 3):
        y_position = (screen_h // 4) * 3
      elif (quadNum == 4):
        x_position = (screen_w // 4)
        y_position = (screen_h // 4) * 3
      else:
        width = 0
        height = 0

    elif FIRST_ROUND_QUAD_INDEX == 4:
      if (quadNum == 1):
        x_position = screen_w // 2        
        y_position = screen_h // 2
      elif (quadNum == 2):
        x_position = (screen_w // 4) * 3
        y_position = (screen_h // 2)
      elif (quadNum == 3):
        x_position = screen_w // 2
        y_position = (screen_h // 4) * 3
      elif (quadNum == 4):
        x_position = (screen_w // 4) * 3
        y_position = (screen_h // 4) * 3
      else:
        width = 0
        height = 0
        
  savedGeometry = f"{width}x{height}+{x_position}+{y_position}"
  shadeWindow.geometry(savedGeometry)
  if roundNum == 1:
    pink_frame.config(width=width, height=height, bg="#FFB6C1")
  else:
    pink_frame.config(width=width, height=height, bg="#D3F07B")
      
#################################################################
# Function to show five choices menu (5 icons: back to previous menu/upper left/right, lower left/right)
#################################################################    
def showCursorSectionChoiceMenu(labels, images, menuBar, shadeWindow, pink_frame, hlColor, nlColor, gobackImgIdx, imgIdxList, roundNum, runState):
  global STATE
  global STOP_EVENT
  global BLINK_CHOICE
  global SCROLL_DELAY
    
  # Load images and reset border color to normal
  labels[0].config(image=images[gobackImgIdx], bg=nlColor)
  labels[1].config(image=images[6], bg=nlColor)
  labels[2].config(image=images[imgIdxList[0]], bg=nlColor)
  labels[3].config(image=images[imgIdxList[1]], bg=nlColor)
  labels[4].config(image=images[imgIdxList[2]], bg=nlColor)
  labels[5].config(image=images[imgIdxList[3]], bg=nlColor)

  STOP_EVENT.clear()  # Allow wait event to proceed.

  lightUpLabelList = [0, 2, 3, 4, 5]
  
  while STATE == runState:
    choiceCounter = 1
    # Change background color to light up
    for labelIdx in lightUpLabelList:
      if (STATE == runState):
        showShadingWindow(shadeWindow, pink_frame, roundNum, labelIdx-1)      
        labels[labelIdx].config(bg=hlColor)
        menuBar.update()
        BLINK_CHOICE = choiceCounter
      if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
        labels[labelIdx].config(bg=nlColor)
        time.sleep(0.8)
        choiceCounter += 1

  # Hide the shading window for round 1
  # For round 2, let it stay there until all the selection are done.
  if roundNum == 1:
    savedGeometry = f"{0}x{0}+{0}+{0}"
    shadeWindow.geometry(savedGeometry)
    shadeWindow.update()
  
#################################################################
# Function to show three img info menu (3 icons: blink to stop cursor)
#################################################################    
def showCursorSelectInstruction(labels, images, menuBar, nlColor, imgIdx1, imgIdx2, imgIdx3, runState):
    
  # Load images and reset border color to normal.
  labels[0].config(image=images[6], bg=nlColor)
  labels[1].config(image=images[imgIdx1], bg=nlColor)
  labels[2].config(image=images[6], bg=nlColor)
  labels[3].config(image=images[imgIdx2], bg=nlColor)
  labels[4].config(image=images[6], bg=nlColor)
  labels[5].config(image=images[imgIdx3],bg=nlColor)
  while STATE == runState:
    menuBar.update()

#################################################################################
# Function to show two choices menu (2 icons: Yes/no to confirm cursor position) 
#################################################################################    
def showTwoChoicesMenu(labels, images, menuBar, hlColor, nlColor, imgIdx1, imgIdx2, runState):
  global STATE
  global STOP_EVENT
  global BLINK_CHOICE
  global SCROLL_DELAY
  
  # Load yes and no images and reset border color to normal.
  labels[0].config(image=images[6], bg=nlColor)
  labels[1].config(image=images[6], bg=nlColor)
  labels[2].config(image=images[imgIdx1], bg=nlColor)
  labels[3].config(image=images[imgIdx2], bg=nlColor)
  labels[4].config(image=images[6], bg=nlColor)
  labels[5].config(image=images[6], bg=nlColor)

  STOP_EVENT.clear()  # Allow wait event to proceed.
  lightUpLabelList = [2, 3] # Light up label index 1 (yes) and 4 (no)

  time.sleep(1.0)  # Have enough delay for the user to be ready first before highlight
  # Light up the background
  while STATE == runState:
    choiceCounter = 1
    # Change background color to light up
    for labelIdx in lightUpLabelList:
      if (STATE == runState):
        labels[labelIdx].config(bg=hlColor)
        menuBar.update()
        BLINK_CHOICE = choiceCounter
      if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
        labels[labelIdx].config(bg=nlColor)
        time.sleep(0.8)
        choiceCounter += 1

#################################### BEGIN HOTKEY FUNCTIONS ####################################
#################################################################
# Function to handle hotkey choice
#################################################################    
def handleHotkeyChoice():
  global STATE
  global HOTKEY_CHOICE
  
  if HOTKEY_CHOICE == 1:
    pyautogui.hotkey('up')
  elif HOTKEY_CHOICE == 2:
    pyautogui.hotkey('down')
  elif HOTKEY_CHOICE == 3:
    pyautogui.hotkey('left')
  elif HOTKEY_CHOICE == 4:
    pyautogui.hotkey('right')
    
  elif HOTKEY_CHOICE == 6:
    pyautogui.hotkey('escape')
  elif HOTKEY_CHOICE == 7:
    pyautogui.hotkey('pageup')
  elif HOTKEY_CHOICE == 8:
    pyautogui.hotkey('pagedown')
  elif HOTKEY_CHOICE == 9:
    pyautogui.hotkey('backspace')
  elif HOTKEY_CHOICE == 10:
    pyautogui.hotkey('enter')
    
  STATE = SM.HOTKEY_SELECTION_STATE
  
#################################################################
# Share function to show six choices menu (FAVOR: prev + 4 favor icons + more icon)
# This is also for CURSOR: mouse click choices menu, and HOTKEY: hotkey menu 
#################################################################    
def showSixChoicesMenu(labels, images, menuBar, hlColor, nlColor, gobackImgIdx, imgIdxList, moreImgIdx, runState):
  global STATE
  global STOP_EVENT
  global BLINK_CHOICE
  global SCROLL_DELAY
  
  # Load images with normal border
  labels[0].config(image=images[gobackImgIdx], bg=nlColor)
  labels[1].config(image=images[imgIdxList[0]], bg=nlColor)
  labels[2].config(image=images[imgIdxList[1]], bg=nlColor)
  labels[3].config(image=images[imgIdxList[2]], bg=nlColor)
  labels[4].config(image=images[imgIdxList[3]], bg=nlColor)
  labels[5].config(image=images[moreImgIdx], bg=nlColor)
              
  STOP_EVENT.clear()  # Allow wait event to proceed.
  lightUpLabelList = [0, 1, 2, 3, 4, 5]

  # Light up the background
  while STATE == runState:
    choiceCounter = 1
    # Change background color to light up
    for labelIdx in lightUpLabelList:      
      # Update highlight color only if still within the same menu.
      if (STATE == runState):
        labels[labelIdx].config(bg=hlColor)
        menuBar.update()
        BLINK_CHOICE = choiceCounter
      if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
        labels[labelIdx].config(bg=nlColor)
        choiceCounter += 1
        time.sleep(0.8)

#################################################################
# Function to show start menu (6 icons: Hidden, cursor, favor, keyboard, setting, shutdown)
#################################################################    
def showStartMenu(labels, images, menuBar, keyboardMenu, hlColor, nlColor, startImgIdx, nrOfImgForThisMenu, hlImageIdx, runState):
  global STATE
  global STOP_EVENT
  global BLINK_CHOICE
  global SCROLL_DELAY
  global DRAG_IN_PROGRESS
  
  # Show the menuBar and hide keyboard menu
  menuBar.deiconify()
  keyboardMenu.withdraw()
  DRAG_IN_PROGRESS = False
  
  # Load all 6 images for start menu and reset border color to normal
  for i in range(startImgIdx, nrOfImgForThisMenu):
    # Load empty image if any option are disabled.
    if (i == 3 and ENABLE_KEYBOARD_OPTION == 0):
      labels[i].config(image=images[4], bg=nlColor)
    if (i == 4 and ENABLE_FAVOR_OPTION == 0):
      labels[i].config(image=images[5], bg=nlColor)
    elif (i == 5 and ENABLE_CLOSE_APPLICATION_OPTION == 0):
      labels[i].config(image=images[6], bg=nlColor)
    else:
      labels[i].config(image=images[i], bg=nlColor)
        
  STOP_EVENT.clear()  # Allow wait event to proceed.

  # Light up the background
  while STATE == runState:
    choiceCounter = 1
    if hlImageIdx > 0:
      labels[hlImageIdx].config(bg=hlColor)
      menuBar.update()
    else:  
      # Change background color to light up
      for i in range(startImgIdx, nrOfImgForThisMenu):
        # Update highlight color only if still within the same menu.
        if (STATE == runState):
          if (i == 3 and ENABLE_KEYBOARD_OPTION == 0):
            continue
          elif (i == 4 and ENABLE_FAVOR_OPTION == 0):
            continue  
          if (i == 5 and ENABLE_CLOSE_APPLICATION_OPTION == 0):
            break
          else:  
            labels[i].config(bg=hlColor)
            menuBar.update()
            BLINK_CHOICE = choiceCounter
            if STOP_EVENT is not None and not STOP_EVENT.wait(SCROLL_DELAY):
              labels[i].config(bg=nlColor)
              choiceCounter += 1
              time.sleep(0.8) 
        
#################################################################
# Function to detect eye blinking etc., then update STATE machine.
#################################################################    
def detectResponse():
  global STATE
  global BLINK_CHOICE
  global STOP_EVENT
  global CURSOR_MOVE_SPEED_X
  global CURSOR_MOVE_SPEED_Y
  global SCROLL_DELAY
  global FIRST_ROUND_QUAD_INDEX
  global SECOND_ROUND_QUAD_INDEX
  global SELECTED_TWO_COLUMNS  
  global SELECTED_ONE_COLUMN
  global SELECTED_ONE_KEYBOARD
  global FAVOR_CHOICE
  global FAVOR_LINKS
  global HOTKEY_CHOICE

  # Setup video camera
  cam = cv2.VideoCapture(0)
  if not cam.isOpened():
    root = tk.Tk()
    root.title("Error")
    label = tk.Label(root, text="Error: Video camera not found.\n错误：找不到摄像机。")
    # Set the window always on top
    root.attributes("-topmost", True)
    label.pack(padx=20, pady=20)
    STATE = SM.ERROR_STATE # Error path
    root.after(3000, root.destroy)
    root.mainloop()
    sys.exit()
      
  # Set frames per second
  cam.set(cv2.CAP_PROP_FPS, 30)
  # Read facial landmarks
  face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

  # Read config file.
  config = read_config("config.txt")
  CONTROL_OPTION = config.get("CONTROL_OPTION")
  SMILE_LEVEL = config.get("SMILE_LEVEL")
  CURSOR_MOVE_SPEED_X = config.get("CURSOR_MOVE_SPEED")
  CURSOR_MOVE_SPEED_Y = (screen_h / screen_w) * CURSOR_MOVE_SPEED_X
  SCROLL_DELAY = config.get("SCROLL_DELAY")
  EYE_CLOSED_COUNTER = config.get("EYE_CLOSED_COUNTER")
  ENABLE_KEYBOARD_OPTION  = config.get("ENABLE_KEYBOARD_OPTION ")
  ENABLE_FAVOR_OPTION = config.get("ENABLE_FAVOR_OPTION")
  ENABLE_CLOSE_APPLICATION_OPTION = config.get("ENABLE_CLOSE_APPLICATION_OPTION")
  FAVOR_LINKS.append(config.get("FAVOR_1"))
  FAVOR_LINKS.append(config.get("FAVOR_2"))
  FAVOR_LINKS.append(config.get("FAVOR_3"))
  FAVOR_LINKS.append(config.get("FAVOR_4"))
  FAVOR_LINKS.append(config.get("FAVOR_5"))
  FAVOR_LINKS.append(config.get("FAVOR_6"))
  FAVOR_LINKS.append(config.get("FAVOR_7"))
  FAVOR_LINKS.append(config.get("FAVOR_8"))
  FAVOR_LINKS.append(config.get("FAVOR_9"))
  FAVOR_LINKS.append(config.get("FAVOR_10"))        
  
  # Let's begin.
  STATE = SM.PROGRAM_STARTED_STATE

  # Create a threading event to control the timer
  STOP_EVENT = threading.Event()
  
  # Start other threads now before getting into endless loop.
  t1 = threading.Thread(target=cursorMove, args=[])
  t3 = threading.Thread(target=displayMenuBar, args=[])
  t1.daemon = True  # Daemonize the thread so it terminates when the main thread terminates
  t3.daemon = True
  t1.start()
  t3.start()  

  IS_SMILE = False
  COUNT_AS_SMILE = False
  if SMILE_LEVEL == 1:  # Easy level
    SMILE_RATIO = 0.94
  else:
    SMILE_RATIO = 0.96  
  closedEyeCounter = 0

  #process = subprocess.Popen(['mushroom.exe'], creationflags=subprocess.CREATE_NO_WINDOW)
  if sys.platform == "win32":
    # Get the handle of the command window, then minimize it
    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

  while STATE.value < SM.PROGRAM_ENDED_STATE.value:
      while True:
        _, frame = cam.read()
        if frame is not None:
          break
      frame = cv2.flip(frame, 1)
      rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      output = face_mesh.process(rgb_frame)
      landmark_points = output.multi_face_landmarks
      frame_h, frame_w, _ = frame.shape
      if landmark_points:
        landmarks = landmark_points[0].landmark

        # Smile detection...
        if CONTROL_OPTION == 1:
          mouth_left = (landmarks[48].x, landmarks[48].y)
          mouth_right = (landmarks[54].x, landmarks[54].y)
          mouth_top = (landmarks[51].x, landmarks[51].y)
          mouth_bottom = (landmarks[57].x, landmarks[57].y)
        
          # Calculate the distance between the mouth corners horizontally and vertically
          horizontal_distance = mouth_left[0] - mouth_right[0]
          vertical_distance = mouth_bottom[1] - mouth_top[1]
        
          # Calculate the aspect ratio of the mouth
          mouth_aspect_ratio = horizontal_distance / vertical_distance


          if mouth_aspect_ratio > SMILE_RATIO:
            if not IS_SMILE:
              IS_SMILE = True
              COUNT_AS_SMILE = True
            else:
              COUNT_AS_SMILE = False
          else:
            IS_SMILE = False
            #print(mouth_left, mouth_right, mouth_bottom, mouth_top, vertical_distance)
            
        # Detect "eye blinking" (for left eye only).
        left = [landmarks[145], landmarks[159]]

        if (left[0].y - left[1].y) < 0.004:  # 0.004 is how close the eye are closed together.
            closedEyeCounter += 1
        else:
            closedEyeCounter = 0          
        if (closedEyeCounter >= EYE_CLOSED_COUNTER or
            (CONTROL_OPTION == 1 and IS_SMILE)):
          if (STATE == SM.PROGRAM_STARTED_STATE): # From initial menuBar selections
            if (BLINK_CHOICE == 1):
              STATE = SM.MINIMIZE_MENU_STATE
            elif (BLINK_CHOICE == 2):
              STATE = SM.CURSOR_SECTION_CHOICE_ROUND1_STATE
            elif (BLINK_CHOICE == 3):
              STATE = SM.SHOW_KEYBOARD_ALPHA_STATE
            elif (BLINK_CHOICE == 4):
              STATE = SM.FAVOR_SELECTION_STATE
            elif (BLINK_CHOICE == 5):
              STATE = SM.HOTKEY_SELECTION_STATE              
            elif (BLINK_CHOICE == 6):
              STATE = SM.CONFIRM_ENDED_STATE
            STOP_EVENT.set()  # stop any on-going timer sleep.
            time.sleep(1) # Delay 1 second to have enough time for next menu to show up

          # Resume the menu bar
          elif (STATE == SM.PARK_STATE):
            STATE = SM.PROGRAM_STARTED_STATE
            time.sleep(1) # Delay 1 second to have enough time for next menu to show up
              
          # Confirm to quit program (y/n)    
          elif (STATE == SM.CONFIRM_ENDED_STATE):
            if (BLINK_CHOICE == 1):           # yes, quit
              STATE = SM.PROGRAM_ENDED_STATE
              STOP_EVENT.set()
              sys.exit()
            elif (BLINK_CHOICE == 2):         # no, back to main menu
              STATE = SM.PROGRAM_STARTED_STATE
            STOP_EVENT.set()
            time.sleep(1)

          # User chooses the cursor move, show 4 icons (upper left/right, lower left/right)
          elif (STATE == SM.CURSOR_SECTION_CHOICE_ROUND1_STATE):
            if (BLINK_CHOICE == 1):           # Previous menu
              STATE = SM.PROGRAM_STARTED_STATE
            elif (BLINK_CHOICE == 2):           # Upper left cursor position
              FIRST_ROUND_QUAD_INDEX = 1
              STATE = SM.CURSOR_SECTION_CHOICE_ROUND2_STATE
            elif (BLINK_CHOICE == 3):           # Upper right cursor position
              FIRST_ROUND_QUAD_INDEX = 2
              STATE = SM.CURSOR_SECTION_CHOICE_ROUND2_STATE
            elif (BLINK_CHOICE == 4):           # Lower left cursor position
              FIRST_ROUND_QUAD_INDEX = 3
              STATE = SM.CURSOR_SECTION_CHOICE_ROUND2_STATE
            elif (BLINK_CHOICE == 5):           # Lower right cursor position
              FIRST_ROUND_QUAD_INDEX = 4
              STATE = SM.CURSOR_SECTION_CHOICE_ROUND2_STATE
            STOP_EVENT.set()
            time.sleep(1)

          # User chooses the cursor move (round 2), show 4 icons (upper left/right, lower left/right)
          elif (STATE == SM.CURSOR_SECTION_CHOICE_ROUND2_STATE):
            if (BLINK_CHOICE == 1):           # Previous menu
              STATE = SM.PROGRAM_STARTED_STATE
            elif (BLINK_CHOICE == 2):           # Upper left cursor position
              SECOND_ROUND_QUAD_INDEX = 1
              STATE = SM.CURSOR_SECTION_CONFIRMED_ROUND2_STATE
            elif (BLINK_CHOICE == 3):           # Upper right cursor position
              SECOND_ROUND_QUAD_INDEX = 2
              STATE = SM.CURSOR_SECTION_CONFIRMED_ROUND2_STATE
            elif (BLINK_CHOICE == 4):           # Lower left cursor position
              SECOND_ROUND_QUAD_INDEX = 3
              STATE = SM.CURSOR_SECTION_CONFIRMED_ROUND2_STATE
            elif (BLINK_CHOICE == 5):           # Lower right cursor position
              SECOND_ROUND_QUAD_INDEX = 4
              STATE = SM.CURSOR_SECTION_CONFIRMED_ROUND2_STATE
            STOP_EVENT.set()
            time.sleep(1)            
                
          # User chooses cursor move X-axis, show confirmation choice and move the cursor.
          elif (STATE == SM.MOVE_CURSOR_X_STATE):
            STATE = SM.CONFIRM_CURSOR_X_STATE
            STOP_EVENT.set()  # stop any on-going timer sleep.
            time.sleep(1) # Delay 1 second to have enough time for next menu to show up

          # Use confirmed the choice on X-axis, either move on or move X-axis again.
          elif (STATE == SM.CONFIRM_CURSOR_X_STATE):
            if (BLINK_CHOICE == 1):           # yes, move on to y-axis
              STATE = SM.MOVE_CURSOR_Y_STATE
            elif (BLINK_CHOICE == 2):         # no, back to cursor X movement state
              STATE = SM.MOVE_CURSOR_X_STATE
            STOP_EVENT.set()
            time.sleep(1)

          # User made decision on cursor move Y-axis already, show confirmation choice.
          elif (STATE == SM.MOVE_CURSOR_Y_STATE):
            STATE = SM.CONFIRM_CURSOR_Y_STATE
            STOP_EVENT.set()
            time.sleep(1)
              
          # User confirmed the choice on Y-axis, either move on or move Y-axis again.
          elif (STATE == SM.CONFIRM_CURSOR_Y_STATE):
            if (BLINK_CHOICE == 1):           # yes, move on to show mouse control options (auto or head spin).
              STATE = SM.CLICK_MOUSE_CHOICE_STATE
            elif (BLINK_CHOICE == 2):         # no, back to cursor Y movement state
              STATE = SM.MOVE_CURSOR_Y_STATE
            STOP_EVENT.set()
            time.sleep(1)

          # Use made a decision of which mouse button to use.
          elif (STATE == SM.CLICK_MOUSE_CHOICE_STATE):
            if (BLINK_CHOICE == 1):           # Previous menu (which is CURSOR_SECTION_CHOICE_ROUND1_STATE)
              STATE = SM.CURSOR_SECTION_CHOICE_ROUND1_STATE
            elif (BLINK_CHOICE == 2):           # Click left mouse button.
              STATE = SM.CLICK_LEFT_BUTTON_STATE
            elif (BLINK_CHOICE == 3):           # double click mouse button.
              STATE = SM.DOUBLE_CLICK_BUTTON_STATE              
            elif (BLINK_CHOICE == 4):         # Click middle mouse button to scroll up/down.
              STATE = SM.CLICK_MIDDLE_BUTTON_STATE
            elif (BLINK_CHOICE == 5):         # Click right mouse button.
              STATE = SM.CLICK_RIGHT_BUTTON_STATE
            elif (BLINK_CHOICE == 6):         # Drag mouse.
              STATE = SM.DRAG_MOUSE_STATE
            STOP_EVENT.set()
            time.sleep(1)


          ###################### KEYBOARD #####################
          # User chooses the keyboard menu.
          elif (STATE == SM.LIGHT_UP_TWO_COLUMNS_KEYBOARDS):
            if (BLINK_CHOICE == 1):
              SELECTED_TWO_COLUMNS = 1
            elif (BLINK_CHOICE == 2):
              SELECTED_TWO_COLUMNS = 2
            elif (BLINK_CHOICE == 3):
              SELECTED_TWO_COLUMNS = 3
            elif (BLINK_CHOICE == 4):
              SELECTED_TWO_COLUMNS = 4
            elif (BLINK_CHOICE == 5):
              SELECTED_TWO_COLUMNS = 5             
            STATE = SM.LIGHT_UP_ONE_COLUMN_KEYBOARDS
            STOP_EVENT.set()
            time.sleep(1)

          elif (STATE == SM.LIGHT_UP_ONE_COLUMN_KEYBOARDS):
            if (BLINK_CHOICE == 1):
              SELECTED_ONE_COLUMN = 1
            elif (BLINK_CHOICE == 2):
              SELECTED_ONE_COLUMN = 2
            STATE = SM.LIGHT_UP_FOUR_KEYBOARDS_CHOICE
            STOP_EVENT.set()
            time.sleep(1)

          elif (STATE == SM.LIGHT_UP_FOUR_KEYBOARDS_CHOICE):
            if (BLINK_CHOICE == 1):
              SELECTED_ONE_KEYBOARD = 1
            elif (BLINK_CHOICE == 2):
              SELECTED_ONE_KEYBOARD = 2
            elif (BLINK_CHOICE == 3):
              SELECTED_ONE_KEYBOARD = 3
            elif (BLINK_CHOICE == 4):
              SELECTED_ONE_KEYBOARD = 4              
            STATE = SM.SELECTED_KEY_STATE
            STOP_EVENT.set()
            time.sleep(1)
            
          ###################### FAVOR #####################
          # User chooses the favor menu, show all favor icons
          elif (STATE == SM.FAVOR_SELECTION_STATE):
            if (BLINK_CHOICE == 1):           # Previous menu
              STATE = SM.PROGRAM_STARTED_STATE
            elif (BLINK_CHOICE == 2):
              FAVOR_CHOICE = 1
              STATE = SM.FAVOR_SELECTED_STATE
            elif (BLINK_CHOICE == 3):
              FAVOR_CHOICE = 2
              STATE = SM.FAVOR_SELECTED_STATE
            elif (BLINK_CHOICE == 4):
              FAVOR_CHOICE = 3
              STATE = SM.FAVOR_SELECTED_STATE
            elif (BLINK_CHOICE == 5):
              FAVOR_CHOICE = 4
              STATE = SM.FAVOR_SELECTED_STATE
            elif (BLINK_CHOICE == 6):
              FAVOR_CHOICE = 5  # More
              STATE = SM.MORE_FAVOR_STATE
            STOP_EVENT.set()
            time.sleep(1)

          elif (STATE == SM.MORE_FAVOR_STATE):
            if (BLINK_CHOICE == 1):           # Previous menu
              STATE = SM.PROGRAM_STARTED_STATE
            elif (BLINK_CHOICE == 2):
              FAVOR_CHOICE = 6
              STATE = SM.FAVOR_SELECTED_STATE
            elif (BLINK_CHOICE == 3):
              FAVOR_CHOICE = 7
              STATE = SM.FAVOR_SELECTED_STATE
            elif (BLINK_CHOICE == 4):
              FAVOR_CHOICE = 8
              STATE = SM.FAVOR_SELECTED_STATE
            elif (BLINK_CHOICE == 5):
              FAVOR_CHOICE = 9
              STATE = SM.FAVOR_SELECTED_STATE
            elif (BLINK_CHOICE == 6):
              FAVOR_CHOICE = 10
              STATE = SM.FAVOR_SELECTED_STATE
            STOP_EVENT.set()
            time.sleep(1)

          ###################### HOTKEY #####################
          # User chooses the hotkey menu, show all hotkey icons
          elif (STATE == SM.HOTKEY_SELECTION_STATE):
            if (BLINK_CHOICE == 1):           # Previous menu
              STATE = SM.PROGRAM_STARTED_STATE
            elif (BLINK_CHOICE == 2):
              HOTKEY_CHOICE = 1
              STATE = SM.HOTKEY_SELECTED_STATE
            elif (BLINK_CHOICE == 3):
              HOTKEY_CHOICE = 2
              STATE = SM.HOTKEY_SELECTED_STATE
            elif (BLINK_CHOICE == 4):
              HOTKEY_CHOICE = 3
              STATE = SM.HOTKEY_SELECTED_STATE
            elif (BLINK_CHOICE == 5):
              HOTKEY_CHOICE = 4
              STATE = SM.HOTKEY_SELECTED_STATE
            elif (BLINK_CHOICE == 6):
              HOTKEY_CHOICE = 5  # More
              STATE = SM.MORE_HOTKEY_STATE
            STOP_EVENT.set()
            time.sleep(1)

          elif (STATE == SM.MORE_HOTKEY_STATE):
            if (BLINK_CHOICE == 1):           # Previous menu
              STATE = SM.PROGRAM_STARTED_STATE
            elif (BLINK_CHOICE == 2):
              HOTKEY_CHOICE = 6
              STATE = SM.HOTKEY_SELECTED_STATE
            elif (BLINK_CHOICE == 3):
              HOTKEY_CHOICE = 7
              STATE = SM.HOTKEY_SELECTED_STATE
            elif (BLINK_CHOICE == 4):
              HOTKEY_CHOICE = 8
              STATE = SM.HOTKEY_SELECTED_STATE
            elif (BLINK_CHOICE == 5):
              HOTKEY_CHOICE = 9
              STATE = SM.HOTKEY_SELECTED_STATE
            elif (BLINK_CHOICE == 6):
              HOTKEY_CHOICE = 10
              STATE = SM.HOTKEY_SELECTED_STATE
            STOP_EVENT.set()
            time.sleep(1)
 
detectResponse()    
