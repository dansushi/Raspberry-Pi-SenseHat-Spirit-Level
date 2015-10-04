#!/usr/bin/python
import sys
import math
import colorsys
from random import randint
import time
from sys import exit

import pygame

from sense_hat import SenseHat
sense = SenseHat()
sense.low_light = False     # Makes sure the SenseHat isn't in low light mode. This screws with the RGB values.
sense.clear()               # Clear the SenseHat screen

''' -----------------------------
Spirit Level for Raspberry Pi
For use with the Sense Hat
And using the pygame library.

Remember to run with sudo: "sudo python3 spirit-level-plus.py"

DISCLAIMER:
I am not by any reach of the imagination a professional programmer.
My code is very messy and there are very likely much better ways to do this.
If you have any recommendations about how to clean up my code, or just any
questions in general, feel free to reach out to me via my github account.

Authored by Dan Schneider (2015), along with some
helpful coding techniques borrowed from
Paul Brown's Snake for Raspberry Pi
-------------------------------'''


#CONSTANTS
#Colors     r    g    b
black =     0,   0,   0
white =   255, 255, 255
BLACK =  (  0,   0,   0)
WHITE =  (255, 255, 255)
GREEN =  (  0, 255,   0)
RED =    (255,   0,   0)
BLUE =   (  0,   0, 255)
YELLOW = (255, 255,   0)
PURPLE = (255,   0, 255)
CYAN =   (  0, 255, 255)
X = WHITE
O = BLACK
#screen size, used for pygame input events and to display instructions 
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540


#SET GLOBALS AND ASSIGN DEFAULT VALUES:
#Lets the while loops know that it's initially on the first loop
global first_color_loop
first_color_loop = True
global first_led_loop
first_led_loop = 1

global color_0,color_1,color_2,color_3,color_4,color_5,color_6,color_7,color_8
global pixel_0,pixel_1,pixel_2,pixel_3,pixel_4,pixel_5,pixel_6,pixel_7,pixel_8,pixel_9
global speed_in_ms,difficulty,dot_type,color_type,show_display,display_paused,x_rad,y_rad,centered


#Default Configuration:
show_display = True
display_paused = False      # Sets display as being unpaused be default
centered = False
speed_in_ms = 0             # Higher is slower, delay in milliseconds, 20 is default
difficulty = 42             # 7 is lowest, for full 90 degrees; 42 is default
dot_type = "dot_bubble"      # Use either dot_bubble or dot_ball
color_type = "by_yaw"

#Dot-Type Toggle Swapper
def dot_direction(dot):
    global dot_type
    if dot_type == "dot_bubble":
        if dot == "dot_x":
            return 1
        if dot == "dot_y":
            return -1
    if dot_type == "dot_ball":
        if dot == "dot_x":
            return -1
        if dot == "dot_y":
            return 1

#Gradient Calculator for luminosity drop over time 
def grad_calc(time,color_letter):
    if color_letter >= 175:
        adjusted_rbg_num = int( ((50 - color_letter) / 8) * time + color_letter)
    elif color_letter >= 50 and color_letter < 175:
        adjusted_rbg_num = int( ((40 - color_letter) / 8) * time + color_letter)
    else: #if color_letter is less than 50
        adjusted_rbg_num = int( (color_letter / 8) * ( 8 - time ) )
    return adjusted_rbg_num 

#Look for joystick actions or keystrokes
def check_joystick_keystrokes():
    global speed_in_ms,difficulty,dot_type,color_type,display_paused
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return True # Ends the loop and closes the program properly
        if event.type == pygame.KEYDOWN:
            # Controls
            #JOYSTICK RETURN DOT-TYPE
            if event.key == pygame.K_RETURN:    # Toggles dot type
                if dot_type == "dot_bubble":   # Is it in bubble mode?
                    dot_type = "dot_ball"      # Then change to ball mode
                else:                           # Is it in ball mode?
                    dot_type = "dot_bubble"    # Then change to bubble mode
            #JOYSTICK LEFT/RIGHT SENSITIVITY
            if event.key == pygame.K_LEFT:  # Makes less difficult/sensitive
                if difficulty > 7:          # Limits sensitivity to 7 units min (lower is less sensitive)
                    difficulty -= 7         # Decreases sensitivity by 7 units
                else:
                    difficulty = 7
            if event.key == pygame.K_RIGHT: # Makes more difficult/sensitive
                if difficulty < 10000:      # Limits sensitivity to 10000 units max (higher is more sensitive)
                    difficulty += 7         # Increases sensitivity by 7 units
                else:
                    difficulty = 7
            #JOYSTICK UP/DOWN SPEED
            if event.key == pygame.K_UP:    # Adds more of a delay (i.e. slower refresh rate)
                if speed_in_ms < 1000:      # Limits delay to 1000ms (one second) maximum
                    speed_in_ms += 10       # Increases delay by 10ms
                else:
                    speed_in_ms = 1000
            if event.key == pygame.K_DOWN:  # Reduces delay (i.e. faster refresh rate)
                if speed_in_ms > 0:         # Limits delay rate to 0ms minimum, program runs as fast as possible
                    speed_in_ms -= 10       # Decreases delay by 10ms
                else:
                    speed_in_ms = 0
            #COLOR MODE
            if event.key == pygame.K_r or event.key == pygame.K_c: # Toggles color type with 'y' or 'c' key
                global color_type
                if color_type == "by_yaw":  # Is it in by_yaw mode?
                    color_type = "random"   # Then change to random mode
                elif color_type == "random":                       # Is it in random mode?
                    color_type = "by_yaw"  # Then change to by_yaw mode
            #SHOW PYGAME DISPLAY??
            if event.key == pygame.K_d:     # Toggles pygame display on and off with the 'd' key
                global show_display
                if show_display == True:    # Is display on?
                    show_display = False   # Then turn it off
                    display_paused = False # Sets display_paused to False so that it runs the elif statement below displaying pause for the first time, and then not repetitively.
                else:                       # Is display off?
                    show_display = True    # Then turn it on

#####-----------------------BEGIN COLOR SECTION-----------------------#####

def calc_color_randomly():
    r = randint(0, 255)
    g = randint(0, 255)
    b = randint(0, 255)
    if r > 50 and g > 50 and b > 50: # This makes sure the color doesn't show up as black (If all R,G and B are below 50, the SenseHat won't display it.
        r = randint(50, 255)
        g = randint(50, 255)
        b = randint(50, 255)        
    color_0 = r, g, b
    return color_0
    
def calc_color_by_yaw(yaw_raw):
    yaw_range_0_to_1 = ( 1 / math.pi * .5 * yaw_raw + 1/2)
    color_0_unrounded = colorsys.hsv_to_rgb(yaw_range_0_to_1,1,255)
    #With colorsys.hsv_to_rgb: hue from 0->1, saturation from 0->1, value from 0->255
    r_yaw = round(color_0_unrounded[0]) # Rounds R value within color_0
    g_yaw = round(color_0_unrounded[1]) # Rounds G value within color_0
    b_yaw = round(color_0_unrounded[2]) # Rounds B value within color_0
    color_0 = r_yaw, g_yaw, b_yaw
    return color_0
    
def calculate_color():
    global color_0,color_1,color_2,color_3,color_4,color_5,color_6,color_7,color_8
    global color_type
    if color_type == "by_yaw":
        color_0 = calc_color_by_yaw(yaw_raw)
    if color_type == "random":
        color_0 = calc_color_randomly() # PARTY MODE! May give seizures!

    r = color_0[0] # Sets r value as rounded color_0 value
    g = color_0[1] # Sets g value as rounded color_0 value
    b = color_0[2] # Sets b value as rounded color_0 value
    
    t = 1
    color_1 = grad_calc(t,r), grad_calc(t,g), grad_calc(t,b)
    t += 1
    color_2 = grad_calc(t,r), grad_calc(t,g), grad_calc(t,b)
    t += 1
    color_3 = grad_calc(t,r), grad_calc(t,g), grad_calc(t,b)
    t += 1
    color_4 = grad_calc(t,r), grad_calc(t,g), grad_calc(t,b)
    t += 1
    color_5 = grad_calc(t,r), grad_calc(t,g), grad_calc(t,b)
    t += 1
    color_6 = grad_calc(t,r), grad_calc(t,g), grad_calc(t,b)
    t += 1
    color_7 = grad_calc(t,r), grad_calc(t,g), grad_calc(t,b)
    t += 1
    color_8 = grad_calc(t,r), grad_calc(t,g), grad_calc(t,b)
    black = 0,0,0
    #print(color_0,color_1,color_2,color_3,color_4,color_5,color_6,color_7,color_8,black) # Uncomment for trailing dot color info

#####-----------------------END COLOR SECTION-------------------------#####

def run_logic():
    global first_color_loop # Lets run_logic know to use global variable 'first_color_loop'
    global first_led_loop # Lets run_logic know to use global variable 'first_led_loop'
    global yaw_raw # Lets run_logic know to use global variable 'yaw_raw'
    global x_rad,y_rad
    global color_0,color_1,color_2,color_3,color_4,color_5,color_6,color_7,color_8
    global pixel_0,pixel_1,pixel_2,pixel_3,pixel_4,pixel_5,pixel_6,pixel_7,pixel_8,pixel_9,centered

    time.sleep(speed_in_ms / 1000)
    
# The following line is needed in order to request new readings from the accelerometer:
    orientation_rad = sense.get_orientation_radians()

# PITCH
    x_rad = float("{pitch}".format(**orientation_rad)) # float() makes sure the pitch is a number and not a string
    x_led = ( difficulty / math.pi * dot_direction("dot_x") * x_rad + 3.5 )
    x_int = round(x_led,0)
    x_round = round(x_led,2)
    #Makes sure the the sense hat is happy with x values between 0 and 7:
    if x_int > 7:
        x_int = 7
    elif x_int < 0:
        x_int = 0
# ROLL
    y_rad = float("{roll}".format(**orientation_rad)) # float() makes sure the roll is a number and not a string
    y_led = ( difficulty / math.pi * dot_direction("dot_y") * y_rad + 3.5 )
    y_int = round(y_led,0)
    y_round = round(y_led,2)
    #Makes sure the the sense hat is happy with y values between 0 and 7:
    if y_int > 7:
        y_int = 7
    elif y_int < 0:
        y_int = 0
# YAW
    yaw_raw = float("{yaw}".format(**orientation_rad))
    calculate_color()
    
    #Initial Setting of first x & y co-ords, will only happen on first loop through
    
    if first_color_loop == True:
        pixel_0 = [x_int,y_int,color_0]
        pixel_1 = pixel_2 = pixel_3 = pixel_4 = pixel_5 = pixel_6 = pixel_7 = pixel_8 = pixel_9 = [0,0,black] # Sets all other pixels to 0,0 and Black
        first_color_loop = False
    
    #Sets the trailing pixels as the co-ords of the original pixel
    pixel_9 = [pixel_8[0],pixel_8[1],black]
    pixel_8 = [pixel_7[0],pixel_7[1],color_8]
    pixel_7 = [pixel_6[0],pixel_6[1],color_7]
    pixel_6 = [pixel_5[0],pixel_5[1],color_6]
    pixel_5 = [pixel_4[0],pixel_4[1],color_5]
    pixel_4 = [pixel_3[0],pixel_3[1],color_4]
    pixel_3 = [pixel_2[0],pixel_2[1],color_3]
    pixel_2 = [pixel_1[0],pixel_1[1],color_2]
    pixel_1 = [pixel_0[0],pixel_0[1],color_1]
    
    #Subsequent setting of first x & y co-ords after first loop through
    pixel_0 = [x_int,y_int,color_0]
    
    # print( "x =" , x_round, " y =" , y_round, " hue =" , color_0) # Uncomment for info in the terminal

    if 3.45 <= x_round <= 3.55 and 3.45 <= y_round <= 3.55: #Sets the white centered notification if x&y co-ords are close enough to center
        sense.set_pixels([
            X, O, O, O, O, O, O, X,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, X, X, O, O, O,
            O, O, O, X, X, O, O, O,
            O, O, O, O, O, O, O, O,
            O, O, O, O, O, O, O, O,
            X, O, O, O, O, O, O, X
        ])
        #time.sleep(500 / 1000)
        centered = True
    else:
        previous_center = centered          # Sets previous_center as whatever centered currently is
        centered = False                    # Changes centered to False
        if previous_center != centered:     # if the previous_center is not the same as the changed center. I.E. the centered variable has literally just changed
            sense.clear()                   # Clears screen since we know we need to display the dot next
    
    if centered == False:
        if first_led_loop > 7: #Sets all non-black pixels
            if pixel_8[0] != pixel_9[0] or pixel_8[1] != pixel_9[1]:
                sense.set_pixel(pixel_9[0],pixel_9[1],pixel_9[2])
            if pixel_7[0] != pixel_8[0] or pixel_7[1] != pixel_8[1]:
                sense.set_pixel(pixel_8[0],pixel_8[1],pixel_8[2])
            if pixel_6[0] != pixel_7[0] or pixel_6[1] != pixel_7[1]:
                sense.set_pixel(pixel_7[0],pixel_7[1],pixel_7[2])
            if pixel_5[0] != pixel_6[0] or pixel_5[1] != pixel_6[1]:
                sense.set_pixel(pixel_6[0],pixel_6[1],pixel_6[2])
            if pixel_4[0] != pixel_5[0] or pixel_4[1] != pixel_5[1]:
                sense.set_pixel(pixel_5[0],pixel_5[1],pixel_5[2])
            if pixel_3[0] != pixel_4[0] or pixel_3[1] != pixel_4[1]:
                sense.set_pixel(pixel_4[0],pixel_4[1],pixel_4[2])
            if pixel_2[0] != pixel_3[0] or pixel_2[1] != pixel_3[1]:
                sense.set_pixel(pixel_3[0],pixel_3[1],pixel_3[2])
            if pixel_1[0] != pixel_2[0] or pixel_1[1] != pixel_2[1]:
                sense.set_pixel(pixel_2[0],pixel_2[1],pixel_2[2])
            if pixel_0[0] != pixel_1[0] or pixel_0[1] != pixel_1[1]:
                sense.set_pixel(pixel_1[0],pixel_1[1],pixel_1[2])
        first_led_loop += 1
        sense.set_pixel(pixel_0[0],pixel_0[1],pixel_0[2])

def display_frame(screen):
    global speed_in_ms,difficulty,dot_type,color_type,x_rad,y_rad
    #screen used to display information to the player, also required to detect pygame events
    screen.fill(WHITE)
    
    rel_step = SCREEN_HEIGHT / 200
    
    #Make Fonts:
    font_xbig = pygame.font.SysFont('sans', 40)
    font_big = pygame.font.SysFont('sans', 30)
    font_med = pygame.font.SysFont('sans', 22)
    font_sm = pygame.font.SysFont('sans', 17)
    font_xsm = pygame.font.SysFont('sans', 13)
    font_xxsm = pygame.font.SysFont('sans', 11)
    
    #Make Text:
    ### TOP-CENTER ###
    title =             font_xbig.render('Raspberry Pi Spirit Level', True, BLACK)
    sub_title =         font_sm.render('(Created by Dan Schneider - 2015)', True, BLACK)
    ### LEFT SIDE OF SCREEN ###
    instruct_title =    font_big.render('Instructions:', True, BLACK)
    instruct_1 =   font_sm.render('Use either the Raspberry Pi Joystick or Keyboard Arrow Keys.', True, BLACK)
    instruct_2 =   font_sm.render('Use UP/DOWN to adjust the Delay in milliseconds between screen refreshes', True, BLACK)
    instruct_3 =   font_sm.render('Use LEFT/RIGHT to adjust the Sensitivity ', True, BLACK)
    instruct_4 =   font_xsm.render('7 refers to 180 degrees from side to side fitting the 8x8 LED screen exactly', True, BLACK)
    instruct_5 =   font_xsm.render('Any higher than 7 will be more sensitive, and the dot will get stuck on the sides more easily', True, BLACK)
    instruct_6 =   font_sm.render('Use CENTER (or ENTER key) to toggle between Bubble and Ball dot-type', True, BLACK)
    instruct_7 =   font_sm.render('Tap \'d\' key to pause display', True, BLACK)
    instruct_8 =   font_sm.render('Tap \'r\' key for random colors', True, BLACK)
    ### RIGHT SIDE OF SCREEN ###
    readings_title =    font_big.render('Readings:', True, BLACK)
    readings_t_rad =    font_sm.render('Radians:', True, BLACK)
    readings_t_deg =    font_sm.render('Degrees:', True, BLACK)
    readings_1a =   font_med.render("Pitch:    ", True, BLACK)
    readings_1b =   font_med.render(format(x_rad, '.4f'), True, BLACK)
    deg_1c = "{pitch}".format(**sense.get_orientation_degrees()) #Gets pitch in degrees
    readings_1c =   font_med.render(deg_1c[0:2+deg_1c.find('.')] + "\N{DEGREE SIGN}", True, BLACK)
    readings_2a =   font_med.render("Roll:     ", True, BLACK)
    readings_2b =   font_med.render(format(y_rad, '.4f'), True, BLACK)
    deg_2c = "{roll}".format(**sense.get_orientation_degrees()) #Gets roll in degrees
    readings_2c =   font_med.render(deg_2c[0:2+deg_2c.find('.')] + "\N{DEGREE SIGN}", True, BLACK)
    readings_3a =   font_med.render("Yaw:     ", True, BLACK)
    readings_3b =   font_med.render(format(yaw_raw, '.4f'), True, BLACK)
    deg_3c = "{yaw}".format(**sense.get_orientation_degrees()) #Gets yaw in degrees
    readings_3c =   font_med.render(deg_3c[0:2+deg_3c.find('.')] + "\N{DEGREE SIGN}", True, BLACK)
    mode_title =    font_big.render('Mode:', True, BLACK)
    mode_1 =    font_med.render("Delay: " + str(speed_in_ms) + "ms", True, BLACK)
    mode_2 =    font_sm.render('', True, BLACK)
    mode_3 =    font_med.render("Sensitivity: " + str(difficulty), True, BLACK)
    mode_4 =    font_sm.render('', True, BLACK)
    mode_5 =    font_med.render("Dot-type: " + str(dot_type), True, BLACK)
    mode_6 =    font_sm.render('', True, BLACK)
        
    #Make Locations on the screen:
    title_center_x = (SCREEN_WIDTH // 2) - (title.get_width() // 2)
    instruct_title_center_x = (SCREEN_WIDTH // 4) - (instruct_title.get_width() // 2)
    readings_title_center_x = (SCREEN_WIDTH // (1.23) ) - (readings_title.get_width() // 2)
    mode_title_center_x = (SCREEN_WIDTH // (1.23)  ) - (mode_title.get_width() // 2)
    
    #Print Text:
    screen.blit( title, [title_center_x, rel_step * 4] )
    screen.blit( instruct_title, [instruct_title_center_x, rel_step * 25] )
    screen.blit( instruct_1, [rel_step * 6, rel_step * 40] )
    screen.blit( instruct_2, [rel_step * 6, rel_step * 50] )
    screen.blit( instruct_3, [rel_step * 6, rel_step * 60] )
    screen.blit( instruct_4, [rel_step * 6, rel_step * 70] )
    screen.blit( instruct_5, [rel_step * 6, rel_step * 78] )
    screen.blit( instruct_6, [rel_step * 6, rel_step * 86] )
    screen.blit( instruct_7, [rel_step * 6, rel_step * 96] )
    screen.blit( instruct_8, [rel_step * 6, rel_step * 106] )
    
    screen.blit( readings_title, [readings_title_center_x, rel_step * 25] )
    screen.blit( readings_t_rad, [rel_step * 278, rel_step * 45] )
    screen.blit( readings_t_deg, [rel_step * 307, rel_step * 45] )
    screen.blit( readings_1a, [rel_step * 250, rel_step * 55] )
    screen.blit( readings_1b, [SCREEN_WIDTH // (1.18) - readings_1b.get_width(), rel_step * 55] )
    screen.blit( readings_1c, [SCREEN_WIDTH // (1.07) - readings_1c.get_width(), rel_step * 55] )
    screen.blit( readings_2a, [rel_step * 250, rel_step * 70] )
    screen.blit( readings_2b, [SCREEN_WIDTH // (1.18) - readings_2b.get_width(), rel_step * 70] )
    screen.blit( readings_2c, [SCREEN_WIDTH // (1.07) - readings_2c.get_width(), rel_step * 70] )
    readings_3_bg = pygame.draw.rect(screen, color_0, [rel_step * 249, rel_step * 84.4, rel_step * 84, rel_step * 10.5])
    screen.blit( readings_3a, [rel_step * 250, rel_step * 85] )
    screen.blit( readings_3b, [SCREEN_WIDTH // (1.18) - readings_3b.get_width(), rel_step * 85] )
    screen.blit( readings_3c, [SCREEN_WIDTH // (1.07) - readings_3c.get_width(), rel_step * 85] )

    
    screen.blit( mode_title, [mode_title_center_x, rel_step * 100] )
    screen.blit( mode_1, [rel_step * 250, rel_step * 120] )
    screen.blit( mode_2, [rel_step * 250, rel_step * 130] )
    screen.blit( mode_3, [rel_step * 250, rel_step * 140] )
    screen.blit( mode_4, [rel_step * 250, rel_step * 150] )
    screen.blit( mode_5, [rel_step * 250, rel_step * 160] )
    screen.blit( mode_6, [rel_step * 250, rel_step * 170] )
    
    
    
    pygame.display.flip()
    
def display_pause(screen):
    screen.fill(WHITE)
    font_xxbig = pygame.font.SysFont('sans', 80)
    #Make Text:
    pause_title =             font_xxbig.render('DISPLAY PAUSED', True, BLACK)
    #Make Locations on the screen:
    pause_center_x = (SCREEN_WIDTH // 2) - (pause_title.get_width() // 2)
    pause_center_y = (SCREEN_HEIGHT // 2) - (pause_title.get_height() // 2)
    #Print Text:
    screen.blit( pause_title, [pause_center_x, pause_center_y] )
    pygame.display.flip()


#Main function and loop
def main():
    #Set up PyGame
    
    pygame.init()

    size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Raspberry Pi Level')

    clock = pygame.time.Clock()
    
    done = False

    global show_display,display_paused
    
    while not done:
        done = check_joystick_keystrokes()

        run_logic()

        if show_display == True:
            display_frame(screen)
        elif display_paused == False:
            display_pause(screen)
            display_paused = True
        else: # display_paused must be true; therefore no longer keeps refreshing display pause screen.
            continue

    sense.clear()
    pygame.quit()

#Runs Main Program:
main() 
