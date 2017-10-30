from __future__ import print_function
import yaml
import subprocess
import re
import argparse

from gammago.model import GoModel
from gammago.processor import SevenPlaneProcessor
from gammago.gtp.board import gtp_position_to_coords, coords_to_gtp_position

class Model(GoModel):
    pass

    
pachi_cmd = ["pachi"]
p = subprocess.Popen(pachi_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def send_command(gtpStream, cmd):
    gtpStream.stdin.write(cmd)
    print(cmd.strip())


def get_response(gtpStream):
    succeeded = False
    result = ''
    while succeeded == False:
        line = gtpStream.stdout.readline()
        if line[0] == '=':
            succeeded = True
            line = line.strip()
            print("Response is: " + line)
            result = re.sub('^= ?', '', line)
    return result

letters = 'abcdefghijklmnopqrs'


def sgfCoord(coords):
    row, col = coords
    return letters[col] + letters[18 - row]

# deal with handicap.  Parse multi-stone response to see where it was placed.
handicap = args.handicap[0]

send_command(p, "boardsize 19\n")
get_response(p)

sgf = "(;GM[1]FF[4]CA[UTF-8]SZ[19]RU[Chinese]\n"

if(handicap == 0):
    send_command(p, "komi 7.5\n")
    get_response(p)
    sgf = sgf + "KM[7.5]\n"
else:
    send_command(p, "fixed_handicap " + str(handicap) + "\n")
    stones = get_response(p)
    sgf_handicap = "HA[" + str(handicap) + "]AB"
    for pos in stones.split(" "):
        move = gtp_position_to_coords(pos)
        bot.apply_move('b', move)
        sgf_handicap = sgf_handicap + "[" + sgfCoord(move) + "]"
    sgf = sgf + sgf_handicap + "\n"

passes = 0
our_color = 'b'   # assume we are black for now
their_color = 'w'   # assume we are black for now
last_color = 'w'

if(handicap > 1):
    last_color = 'b'

colors = {}
colors['w'] = 'white'
colors['b'] = 'black'

while passes < 2:
    if(last_color != our_color):
        move = bot.select_move(our_color)  # applies the move too
        if move is None:
            send_command(p, "play " + colors[our_color] + " pass\n")
            sgf = sgf + ";" + our_color.upper() + "[]\n"
            passes = passes + 1
        else:
            pos = coords_to_gtp_position(move)
            send_command(p, "play " + colors[our_color] + " " + pos + "\n")
            sgf = sgf + ";" + our_color.upper() + "[" + sgfCoord(move) + "]\n"
            passes = 0
        resp = get_response(p)
        last_color = our_color
    else:
        send_command(p, "genmove " + colors[their_color] + "\n")
        pos = get_response(p)
        if(pos == 'resign'):
            passes = 2
        elif(pos == 'pass'):
            sgf = sgf + ";" + their_color.upper() + "[]\n"
            passes = passes + 1
        else:
            move = gtp_position_to_coords(pos)
            bot.apply_move(their_color, move)
            sgf = sgf + ";" + their_color.upper() + "[" + sgfCoord(move) + "]\n"
            passes = 0
        last_color = their_color

sgf = sgf + ")\n"

with open(args.output_sgf, 'w') as out_h:
    out_h.write(sgf)
