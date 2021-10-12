import socket
import random
import time
import json
import datetime
import requests
#import colorsys
#import os
colordict = {}
with open("/config/colordict.txt") as g:
    colordict = json.load(g)
UNKNOWN_COLORS_FILENAME = "/config/unknown_colors.js"
IRCSOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
with open('/config/conf.json') as json_data_file:
    data = json.load(json_data_file)
    SERVER = data['twitch']['server']
    CHANNEL = data['twitch']['channels'][0]
    BOTNICK = data['twitch']['botnick']
    PASSWORD = data['twitch']['passwd']
    ADMINNAME = data['twitch']['adminname']
    LIGHTGROUP = data['twitch']['lightgroup']
    SKYONE = data['twitch']['light1']
    SKYTWO = data['twitch']['light2']
    HUGO = data['twitch']['light5']
EXITCODE = "bye " + BOTNICK #Text that we will use
PINGTIME = datetime.datetime.now()
IRCSOCK.connect((SERVER, 6667)) # Here we connect to the SERVER using the port 6667
IRCSOCK.send(bytes("PASS "+ PASSWORD +"\n", "UTF-8"))
IRCSOCK.send(bytes("NICK "+ BOTNICK + "\n", "UTF-8")) # assign the nick to the bot
def joinchan(chan): # join CHANNEL(s).
    IRCSOCK.send(bytes("JOIN "+ chan +"\n", "UTF-8"))
    IRCSOCK.send(bytes("CAP REQ :twitch.tv/membership\r\n", "UTF-8"))
    IRCSOCK.send(bytes("CAP REQ :twitch.tv/commands\r\n", "UTF-8"))
    IRCSOCK.send(bytes("CAP REQ :twitch.tv/tags\r\n", "UTF-8"))
    ircmsg = ""
    while ircmsg.find("End of /NAMES list") == -1:
        ircmsg = IRCSOCK.recv(1024).decode("UTF-8")
        ircmsg = ircmsg.strip('\n\r')
        log(ircmsg)
def log(message):
    print(datetime.datetime.now(), " - ", message)
def ping(): # respond to SERVER Pings.
    log("i received a ping")
    IRCSOCK.send(bytes("PONG tmi.twitch.tv\r\n", "UTF-8"))
    global PINGTIME
    PINGTIME = datetime.datetime.now()
    #print("i attempted to send a pong")
def sendmsg(msg, target=CHANNEL): # sends messages to the target.
    IRCSOCK.send(bytes("PRIVMSG "+ target +" :"+ msg +"\n", "UTF-8"))
def handle_unknown_color(color):
    if color and len(color) > 2:
        with open(UNKNOWN_COLORS_FILENAME, 'r+') as f:
            unknown_colors = json.loads(f.read())
            color_count = unknown_colors.get(color, 0) + 1
            unknown_colors[color] = color_count
            f.seek(0)
            f.write(json.dumps(unknown_colors))
def handle_group(comm, comtext, dest):
    if not comtext:
        sendmsg("Try again.  Place the color you would like after !" + comm, dest)
        return
    color = colordict.get(comtext, None)
    if not color:
        if comtext:
            if comtext.lower() == "rainbow":
                PAYLOAD = {"effect":"colorloop"}
                PAYLOAD = json.dumps(PAYLOAD)
                RESPONSE = requests.put(LIGHTGROUP, data=PAYLOAD)
                sendmsg("Making the lights more fabulous.", dest)
                return
            elif comtext.lower() == "disco":
                sendmsg("Let's have a quick dance party.", dest)
                for _ in range(20):
                    PAYLOAD = {"sat":random.randint(129, 254), "bri":214, "hue":random.randint(1, 65536), "transitiontime":0, "effect":"none"}
                    PAYLOAD = json.dumps(PAYLOAD)
                    RESPONSE = requests.put(LIGHTGROUP, data=PAYLOAD)
                    time.sleep(1)
                return
        handle_unknown_color(comtext.lower())
        sendmsg("I don't know what color " + comtext + " is yet, but I'm learning.")
        return
    SAT, BRI, HUE = color
    PAYLOAD = {"sat":SAT, "BRI":BRI, "hue":HUE, "transitiontime":8, "effect":"none"}
    PAYLOAD = json.dumps(PAYLOAD)
    log(PAYLOAD)
    RESPONSE = requests.put(LIGHTGROUP, data=PAYLOAD)
    log(RESPONSE)
    sendmsg("Adjusting lights to the color named: " + comtext.title(), dest)
    time.sleep(2)
def handle_light(comm, comtext, dest):
    if not comtext:
        sendmsg("Try again.  Place which light and what color you would like after !" + comm, dest)
        return
    parts = comtext.split(' ', 1)
    if len(parts) == 2:
        bulb, colorname = parts
        color = colordict.get(colorname, None)
        bulbs = {'skyone' : SKYONE, 'skytwo' : SKYTWO, 'hugo' : HUGO}
        if bulb in bulbs.keys():
            if not color:
                if comtext:
                    if colorname == "rainbow":
                        PAYLOAD = {"effect":"colorloop"}
                        PAYLOAD = json.dumps(PAYLOAD)
                        RESPONSE = requests.put(bulbs[bulb], data=PAYLOAD)
                        sendmsg("Making this light more fabulous.", dest)
                        return
                    elif colorname == "disco":
                        sendmsg("Let's have a quick dance party.", dest)
                        for _ in range(20):
                            PAYLOAD = {"sat":random.randint(129, 254), "bri":214, "hue":random.randint(1, 65536), "transitiontime":0, "effect":"none"}
                            PAYLOAD = json.dumps(PAYLOAD)
                            RESPONSE = requests.put(bulbs[bulb], data=PAYLOAD)
                            time.sleep(1)
                        return
                handle_unknown_color(colorname)
                sendmsg("I don't know what color " + colorname + " is yet, but I'm learning.")
                return
            SAT, BRI, HUE = color
            PAYLOAD = {"sat":SAT, "BRI":BRI, "hue":HUE, "transitiontime":8, "effect":"none"}
            PAYLOAD = json.dumps(PAYLOAD)
            log(PAYLOAD)
            RESPONSE = requests.put(bulbs[bulb], data=PAYLOAD)
            log(RESPONSE)
            sendmsg("Adjusting that light to the color named: " + colorname.title(), dest)
            time.sleep(2)
        else:
            sendmsg("I don't know which light " + bulb.title() + " is.")
    else:
        sendmsg("Please specify which bulb (skyone, skytwo, or hugo) and which color you would like")
def handle_command(comm, comtext, dest):
    if comm == "lights":
        handle_group(comm, comtext, dest)
    elif comm == "light":
        handle_light(comm, comtext, dest)
def privmsg(nick, email, dest, text):
    log(" ".join([nick, email, dest, text]))
    if len(text) > 0 and text[0] == "!":
        parts = text[1:].lower().split(" ", 1)
        comtext = None
        comm = parts[0]
        if len(parts) > 1:
            comtext = parts[1]
        handle_command(comm, comtext, dest)
    if text.startswith("hi " + BOTNICK):
        sendmsg("Greetings " + nick + ".", dest)
        if nick.startswith("notso"):
            time.sleep(2)
            sendmsg("How was your date last night?", dest)
    elif text.startswith("!computer"):
        sendmsg("Command?", dest)
        time.sleep(2)
    elif text.startswith("hi @" + BOTNICK):
        sendmsg("Greetings @" + nick, dest)
        if nick.startswith("notso"):
            time.sleep(2)
            sendmsg("How was your date last night?", dest)
def main():
    while 1:
        joinchan(CHANNEL)
        while (datetime.datetime.now() - PINGTIME).seconds < 600:
            msg = IRCSOCK.recv(1024).decode("UTF-8")
            msg = msg.strip('\n\r')
            twitchcommand = None
            source = None
            log(" ".join(["MESSAGE: ", msg]))
            while msg != ":tmi.twitch.tv RECONNECT":
                part, rem = msg.split(' ', 1)
                if part[0] == "@":
                    twitchcommand = part
                    msg = rem
                elif part[0] == ":":
                    source = part
                    msg = rem
                else:
                    break

            if msg == ":tmi.twitch.tv RECONNECT":
                msg = ":"
                continue
            if twitchcommand:
                log(" ".join(["TWITCHCOM: ", twitchcommand]))
                log(" ".join(["SOURCE: ", source]))
            ircmsg = msg
            log(" ".join(["IRCMSG: ", ircmsg]))
            com, rem = ircmsg.split(' ', 1)
            log(" ".join(["COM: ", com]))
            log(" ".join(["REM: ", rem]))
            if com == "PRIVMSG":
                nick, email = source.split('!', 1)
                nick = nick.split(":", 1)[1]
                dest, text = rem.split(" :", 1)
                privmsg(nick, email, dest, text)
            elif com == "PING":
                ping()
main()
