import os
from pathlib import Path
import time
import json
import platform
import random
import argparse
from keycloak import KeycloakOpenID
import requests
from pygame import mixer
import websocket
from websocket_server import WebsocketServer
import threading
import logging
from download import download
import shutil
import csv

sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
# '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
formatter = logging.Formatter('%(message)s')
sh.setFormatter(formatter)
logger=logging.getLogger()
logger.handlers.clear()
logger.setLevel(logging.INFO)
logger.addHandler(sh)






VERSION = '2.0.0'

DEFAULT_HOST_IP = '0.0.0.0'
DEFAULT_HOST_PORT = 8079
DEFAULT_CALLER = None
DEFAULT_DOWNLOADS = True
DEFAULT_DOWNLOADS_LIMIT = 0
DEFAULT_DOWNLOADS_PATH = 'downloads'
DEFAULT_EMPTY_PATH = ''
DEFAULT_MIXER_FREQUENCY = 44100
DEFAULT_MIXER_SIZE = 32
DEFAULT_MIXER_CHANNELS = 2
DEFAULT_MIXER_BUFFERSIZE = 4096

AUTODART_URL = 'https://autodarts.io'
AUTODART_AUTH_URL = 'https://login.autodarts.io/'
AUTODART_AUTH_TICKET_URL = 'https://api.autodarts.io/ms/v0/ticket'
AUTODART_CLIENT_ID = 'autodarts-app'
AUTODART_REALM_NAME = 'autodarts'
AUTODART_MATCHES_URL = 'https://api.autodarts.io/gs/v0/matches/'
AUTODART_BOARDS_URL = 'https://api.autodarts.io/bs/v0/boards/'
AUTODART_WEBSOCKET_URL = 'wss://api.autodarts.io/ms/v0/subscribe?ticket='

SUPPORTED_SOUND_FORMATS = ['.mp3', '.wav']
SUPPORTED_GAME_VARIANTS = ['X01', 'Cricket', 'Random Checkout']
SUPPORTED_CRICKET_FIELDS = [15, 16, 17, 18, 19, 20, 25]
BOGEY_NUMBERS = [169, 168, 166, 165, 163, 162, 159]



CALLER_PROFILES = {
    'charles-m-english-us-canada': 'https://download1499.mediafire.com/608rnh5p9segWvS6qIbsfdRyQ6tINm25As3-ltArJiqdXceGVPnE5ehFP1wSkZ42gRcNNkAHdXCbYrlv6SJQZNMeREI/65dnw202a3gzz1s/download.zip',

    
}



def ppi(message, info_object = None):
    logger.info('\r\n>>> ' + str(message))
    if info_object != None:
        print(str(info_object))
    
def ppe(message, error_object):
    ppi(message)
    if DEBUG:
        logger.exception("\r\n" + str(error_object))



def download_callers(): 
    if DOWNLOADS:
        download_list = CALLER_PROFILES
        if DOWNLOADS_LIMIT > 0:
            download_list = {k: CALLER_PROFILES[k] for k in list(CALLER_PROFILES.keys())[-DOWNLOADS_LIMIT:]}

        # Download and parse every caller-profile
        for cpr_name, cpr_download_url in download_list.items():
            try:
                # Check if caller-profile already present in users media-directory, yes ? -> stop for this caller-profile
                caller_profile_exists = os.path.exists(os.path.join(AUDIO_MEDIA_PATH, cpr_name))
                if caller_profile_exists == True:
                    # ppi('Caller-profile ' + cpr_name + ' already exists -> Skipping download')
                    continue

                # clean download-area!
                shutil.rmtree(DOWNLOADS_PATH, ignore_errors=True)
                if os.path.exists(DOWNLOADS_PATH) == False: os.mkdir(DOWNLOADS_PATH)
                
                # Download caller-profile and extract archive
                dest = os.path.join(DOWNLOADS_PATH, 'download.zip')

                # kind="zip", 
                path = download(cpr_download_url, dest, progressbar=True, replace=False, verbose=True)
 
                # TEMP Test!!
                # shutil.copyfile('C:\\Users\\Luca\\Desktop\\WORK\\charles-m-english-us-canada\\download.zip', os.path.join(DOWNLOADS_PATH, 'download.zip'))

                shutil.unpack_archive(dest, DOWNLOADS_PATH)
                os.remove(dest)
        
                # Find sound-file-archive und extract it
                zip_filename = [f for f in os.listdir(DOWNLOADS_PATH) if f.endswith('.zip')][0]
                dest = os.path.join(DOWNLOADS_PATH, zip_filename)
                shutil.unpack_archive(dest, DOWNLOADS_PATH)
                os.remove(dest)

                # Find folder and rename it to properly
                sound_folder = [dirs for root, dirs, files in sorted(os.walk(DOWNLOADS_PATH))][0][0]
                src = os.path.join(DOWNLOADS_PATH, sound_folder)
                dest = os.path.splitext(dest)[0]
                os.rename(src, dest)

                # Find template-file and parse it
                template_file = [f for f in os.listdir(DOWNLOADS_PATH) if f.endswith('.csv')][0]
                template_file = os.path.join(DOWNLOADS_PATH, template_file)
                san_list = list()
                with open(template_file, 'r', encoding='utf-8') as f:
                    tts = list(csv.reader(f, delimiter=';'))
                    for event in tts:
                        sanitized = list(filter(None, event))
                        if len(sanitized) == 1:
                            sanitized.append(sanitized[0].lower())
                        san_list.append(sanitized)
                    # print(san_list)

                # Find origin-file
                origin_file = None
                files = [f for f in os.listdir(DOWNLOADS_PATH) if f.endswith('.txt')]
                if len(files) >= 1:
                    origin_file = os.path.join(DOWNLOADS_PATH, files[0])

                # Move template- and origin-file to sound-dir
                shutil.move(origin_file, dest)
                shutil.move(template_file, dest)   

                # Find all supported sound-files and remember names 
                sounds = []
                for root, dirs, files in sorted(os.walk(dest)):
                    for file in files:
                        if file.endswith(tuple(SUPPORTED_SOUND_FORMATS)):
                            sounds.append(os.path.join(root, file))
                # print(sounds)

                # Rename sound-files and copy files according the defined caller-keys
                for i in range(len(san_list) - 1):
                    current_sound = sounds[i]
                    current_sound_splitted = os.path.splitext(current_sound)
                    current_sound_extension = current_sound_splitted[1]

                    try:
                        row = san_list[i]
                        caller_keys = row[1:]
                        # print(caller_keys)

                        for ck in caller_keys:
                            multiple_file_name = os.path.join(dest, ck + current_sound_extension)
                            exists = os.path.exists(multiple_file_name)
                            # print('Test existance: ' + multiple_file_name)

                            counter = 0
                            while exists == True:
                                counter = counter + 1
                                multiple_file_name = os.path.join(dest, ck + '+' + str(counter) + current_sound_extension)
                                exists = os.path.exists(multiple_file_name)
                                # print('Test (' + str(counter) + ') existance: ' + multiple_file_name)

                            shutil.copyfile(current_sound, multiple_file_name)
                    except Exception as ie:
                        ppe('Failed to process entry "' + row[0] + '"', ie)
                    finally:
                        os.remove(current_sound)

                shutil.move(dest, AUDIO_MEDIA_PATH)

            except Exception as e:
                ppe('Failed to process caller-profile: ' + cpr_name, e)
            finally:
                shutil.rmtree(DOWNLOADS_PATH, ignore_errors=True)

def load_callers():

    # load shared-sounds
    shared_sounds = {}
    if AUDIO_MEDIA_PATH_SHARED != DEFAULT_EMPTY_PATH: 
        for root, dirs, files in os.walk(AUDIO_MEDIA_PATH_SHARED):
            for filename in files:
                if filename.endswith(tuple(SUPPORTED_SOUND_FORMATS)):
                    full_path = os.path.join(root, filename)
                    base = os.path.splitext(filename)[0]
                    key = base.split('+', 1)[0]
                    if key in shared_sounds:
                        shared_sounds[key].append(full_path)
                    else:
                        shared_sounds[key] = [full_path]

    # load callers
    callers = []
    for root, dirs, files in os.walk(AUDIO_MEDIA_PATH):
        file_dict = {}
        for filename in files:
            if filename.endswith(tuple(SUPPORTED_SOUND_FORMATS)):
                full_path = os.path.join(root, filename)
                base = os.path.splitext(filename)[0]
                key = base.split('+', 1)[0]
                if key in file_dict:
                    file_dict[key].append(full_path)
                else:
                    file_dict[key] = [full_path]
        if file_dict:
            callers.append((root, file_dict))
        
    # add shared-sounds to callers
    for ss_k, ss_v in shared_sounds.items():
        for (root, c_keys) in callers:
            if ss_k in c_keys:
                for sound_variant in ss_v:
                    c_keys[ss_k].append(sound_variant)
            else:
                c_keys[ss_k] = ss_v

    return callers

def setup_caller():
    global caller
    caller = None

    callers = load_callers()
    ppi(str(len(callers)) + ' caller(s) ready to call out your Darts:')

    # specific caller
    if CALLER != DEFAULT_CALLER:
        wanted_caller = CALLER.lower()
        for c in callers:
            caller_name = os.path.basename(os.path.normpath(c[0])).lower()
            print(caller_name)
            if caller_name == wanted_caller:
                caller = c
     
    else:
        if RANDOM_CALLER == False:
            caller = callers[0]
        else:
            caller = random.choice(callers)

    if caller == None:
        raise Exception('A caller with name "' + wanted_caller + '" does NOT exist!')

    ppi("Your current caller: " + str(os.path.basename(os.path.normpath(caller[0]))) + " knows " + str(len(caller[1].values())) + " Sound(s)")
    # ppi(caller[1])
    caller = caller[1]

def receive_local_board_address():
    try:
        global accessToken
        global boardManagerAddress

        scheme = 'http://'    
        if boardManagerAddress == None or boardManagerAddress == scheme: 
            res = requests.get(AUTODART_BOARDS_URL + AUTODART_USER_BOARD_ID, headers={'Authorization': 'Bearer ' + accessToken})
            board_ip = res.json()['ip']
            boardManagerAddress = scheme + board_ip
            ppi('Board-address: ' + boardManagerAddress)  
    except Exception as e:
        ppe('Fetching local-board-address failed', e)



def play_sound(pathToFile, waitForLast, volumeMult):
    if waitForLast == True:
        while mixer.get_busy():
            time.sleep(0.1)

    sound = mixer.Sound(pathToFile)
    if AUDIO_CALLER_VOLUME is not None:
        sound.set_volume(AUDIO_CALLER_VOLUME * volumeMult)
    sound.play()
    # ppi('Playing: "' + pathToFile + '"')

def play_sound_effect(event, waitForLast = False, volumeMult = 1.0):
    try:
        global caller
        play_sound(random.choice(caller[event]), waitForLast, volumeMult)
        return True
    except Exception as e:
        ppe('Can not play soundfile for event "' + event + '" -> Ignore this or check existance; otherwise convert your file appropriate', e)
        return False


def listen_to_newest_match(m, ws):
    global currentMatch
    cm = str(currentMatch)

    # look for supported match that match my board-id and take it as ongoing match
    newMatch = None
    if m['variant'] in SUPPORTED_GAME_VARIANTS and m['finished'] == False:
        for p in m['players']:
            if 'boardId' in p and p['boardId'] == AUTODART_USER_BOARD_ID:
                newMatch = m['id']   
                break

    if cm == None or (cm != None and newMatch != None and cm != newMatch):
        ppi('Listen to match: ' + newMatch)

        if cm != None:
            paramsUnsubscribeMatchEvents = {
                "type": "unsubscribe",
                "channel": "autodarts.matches",
                "topic": cm + ".state"
            }
            ws.send(json.dumps(paramsUnsubscribeMatchEvents))

        paramsSubscribeMatchEvents = {
            "type": "subscribe",
            "channel": "autodarts.matches",
            "topic": newMatch + ".state"
        }
        ws.send(json.dumps(paramsSubscribeMatchEvents))
        currentMatch = newMatch
    
def process_match_x01(m):
    variant = m['variant']
    currentPlayerIndex = m['player']
    currentPlayer = m['players'][currentPlayerIndex]
    currentPlayerName = str(currentPlayer['name']).lower()
    remainingPlayerScore = m['gameScores'][currentPlayerIndex]
    turns = m['turns'][0]
    points = str(turns['points'])
    pcc_success = False

    isGameOn = False
    isGameFin = False
    global isGameFinished
    global lastPoints
    global accessToken
    global currentMatch

    busted = turns['busted'] == True
    matchshot = m['winner'] != -1 and isGameFinished == False
    gameshot = m['gameWinner'] != -1 and isGameFinished == False

    # Determine "baseScore"-Key
    base = 'baseScore'
    if 'target' in m['settings']:
        base = 'target'
    
    # and len(turns['throws']) == 3 or isGameFinished == True
    if turns != None and turns['throws'] != None:
        lastPoints = points

    # Call every thrown dart
    if CALL_EVERY_DART and turns != None and turns['throws'] != None and len(turns['throws']) >= 1 and busted == False and matchshot == False and gameshot == False: 

        throwAmount = len(turns['throws'])
        type = turns['throws'][throwAmount - 1]['segment']['bed'].lower()
        field_name = turns['throws'][throwAmount - 1]['segment']['name'].lower()

        if field_name == '25':
            field_name = 'sbull'

        # ppi("Type: " + str(type) + " - Field-name: " + str(field_name))

        if len(turns['throws']) <= 2:
            if CALL_EVERY_DART_SINGLE_FILE:
                if play_sound_effect(field_name) == False:
                    inner_outer = False
                    if type == 'singleouter' or type == 'singleinner':
                        inner_outer = play_sound_effect(type)
                        if inner_outer == False:
                            play_sound_effect('single')
                    else:
                        play_sound_effect(type)

            else:
                field_number = str(turns['throws'][throwAmount - 1]['segment']['number'])

                if type == 'single' or type == 'singleinner' or type == "singleouter":
                    play_sound_effect(field_number)
                elif type == 'double' or type == 'triple':
                    play_sound_effect(type)
                    play_sound_effect(field_number, True)
                else:
                    play_sound_effect('outside')

    # Check for matchshot
    if matchshot:
        isGameFin = True
        
        matchWon = {
                "event": "match-won",
                "player": currentPlayerName,
                "game": {
                    "mode": variant,
                    "dartsThrownValue": points
                } 
            }
        broadcast(matchWon)

        if play_sound_effect('matchshot') == False:
            play_sound_effect('gameshot')
        play_sound_effect(currentPlayerName, True)

        if AMBIENT_SOUNDS != 0.0:
            if play_sound_effect('ambient_matchshot', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS) == False:
                play_sound_effect('ambient_gameshot', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
        setup_caller()
        ppi('Gameshot and match')

    # Check for gameshot
    elif gameshot:
        isGameFin = True
        
        gameWon = {
                "event": "game-won",
                "player": currentPlayerName,
                "game": {
                    "mode": variant,
                    "dartsThrownValue": points
                } 
            }
        broadcast(gameWon)

        play_sound_effect('gameshot')
        play_sound_effect(currentPlayerName, True)
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect('ambient_gameshot', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
        if RANDOM_CALLER_EACH_LEG:
            setup_caller()
        ppi('Gameshot')

    # Check for matchon
    elif m['settings'][base] == m['gameScores'][0] and turns['throws'] == None and m['leg'] == 1 and m['set'] == 1:
        isGameOn = True
        isGameFinished = False

        matchStarted = {
            "event": "match-started",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                "pointsStart": str(base),
                # TODO: fix
                "special": "TODO"
                }     
            }
        broadcast(matchStarted)

        play_sound_effect(currentPlayerName, False)
        if play_sound_effect('matchon', True) == False:
            play_sound_effect('gameon', True)
        # play only if it is a real match not just legs!
        if AMBIENT_SOUNDS != 0.0 and ('legs' in m and 'sets'):
            if play_sound_effect('ambient_matchon', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS) == False:
                play_sound_effect('ambient_gameon', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)

        ppi('Matchon')

    # Check for gameon
    elif m['settings'][base] == m['gameScores'][0] and turns['throws'] == None:
        isGameOn = True
        isGameFinished = False

        gameStarted = {
            "event": "game-started",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                "pointsStart": str(base),
                # TODO: fix
                "special": "TODO"
                }     
            }
        broadcast(gameStarted)

        play_sound_effect(currentPlayerName)
        play_sound_effect('gameon', True)
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect('ambient_gameon', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)

        ppi('Gameon')
          
    # Check for busted turn
    elif busted:
        lastPoints = "B"
        isGameFinished = False
        busted = { 
                    "event": "busted",
                    "player": currentPlayerName,
                    "game": {
                        "mode": variant
                    }       
                }
        broadcast(busted)

        play_sound_effect('busted')
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect('ambient_noscore', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
        ppi('Busted')

    # Check for possible checkout
    elif POSSIBLE_CHECKOUT_CALL and m['player'] == currentPlayerIndex and remainingPlayerScore <= 170 and remainingPlayerScore not in BOGEY_NUMBERS and turns != None and turns['throws'] == None:
        isGameFinished = False
        play_sound_effect(currentPlayerName)

        remaining = str(remainingPlayerScore)

        if POSSIBLE_CHECKOUT_CALL_SINGLE_FILE:
            pcc_success = play_sound_effect('yr_' + remaining, True)
            if pcc_success == False:
                pcc_success = play_sound_effect(remaining, True)
        else:
            play_sound_effect('you_require', True)
            play_sound_effect(remaining, True)

        ppi('Checkout possible: ' + remaining)

    # Check for 1. Dart
    elif turns != None and turns['throws'] != None and len(turns['throws']) == 1:
        isGameFinished = False

    # Check for 2. Dart
    elif turns != None and turns['throws'] != None and len(turns['throws']) == 2:
        isGameFinished = False

    # Check for 3. Dart - points call
    elif turns != None and turns['throws'] != None and len(turns['throws']) == 3:
        isGameFinished = False
        
        dartsThrown = {
            "event": "darts-thrown",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                "pointsLeft": str(remainingPlayerScore),
                "dartNumber": "3",
                "dartValue": points,        

            }
        }
        broadcast(dartsThrown)

        play_sound_effect(points)
        if AMBIENT_SOUNDS != 0.0:
            if turns['points'] == 0:
                play_sound_effect('ambient_noscore', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
            elif turns['points'] == 180:
                play_sound_effect('ambient_180', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
            elif turns['points'] >= 153:
                play_sound_effect('ambient_150more', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)   
            elif turns['points'] >= 120:
                play_sound_effect('ambient_120more', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
            elif turns['points'] >= 100:
                play_sound_effect('ambient_100more', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
            elif turns['points'] >= 50:
                play_sound_effect('ambient_50more', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)


        ppi("Turn ended")

    # Playerchange
    if isGameOn == False and turns != None and turns['throws'] == None or isGameFinished == True:
        busted = "False"
        if lastPoints == "B":
            lastPoints = "0"
            busted = "True"

        dartsPulled = {
            "event": "darts-pulled",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                # TODO: fix
                "pointsLeft": str(remainingPlayerScore),
                # TODO: fix
                "dartsThrown": "3",
                "dartsThrownValue": lastPoints,
                "busted": busted
                # TODO: fix
                # "darts": [
                #     {"number": "1", "value": "60"},
                #     {"number": "2", "value": "60"},
                #     {"number": "3", "value": "60"}
                # ]
            }
        }
        broadcast(dartsPulled)

        if pcc_success == False:
            play_sound_effect('playerchange')

        ppi("Next player")


    if isGameFin == True:
        isGameFinished = True

def process_match_cricket(m):
    currentPlayerIndex = m['player']
    currentPlayer = m['players'][currentPlayerIndex]
    currentPlayerName = str(currentPlayer['name']).lower()
    turns = m['turns'][0]
    variant = m['variant']

    isGameOn = False
    isGameFin = False
    global isGameFinished
    global lastPoints

    # Call every thrown dart
    if CALL_EVERY_DART and turns != None and turns['throws'] != None and len(turns['throws']) >= 1: 
        throwAmount = len(turns['throws'])
        type = turns['throws'][throwAmount - 1]['segment']['bed'].lower()
        field_name = turns['throws'][throwAmount - 1]['segment']['name'].lower()
        field_number = turns['throws'][throwAmount - 1]['segment']['number']

        if field_name == '25':
            field_name = 'sbull'
            
        # ppi("Type: " + str(type) + " - Field-name: " + str(field_name))

        # TODO non single file
        if field_number in SUPPORTED_CRICKET_FIELDS and play_sound_effect(field_name) == False:
            inner_outer = False
            if type == 'singleouter' or type == 'singleinner':
                 inner_outer = play_sound_effect(type)
                 if inner_outer == False:
                    play_sound_effect('single')
            else:
                play_sound_effect(type)

    # Check for matchshot
    if m['winner'] != -1 and isGameFinished == False:
        isGameFin = True

        throwPoints = 0
        lastPoints = ''
        for t in turns['throws']:
            number = t['segment']['number']
            if number in SUPPORTED_CRICKET_FIELDS:
                throwPoints += (t['segment']['multiplier'] * number)
                lastPoints += 'x' + str(t['segment']['name'])
        lastPoints = lastPoints[1:]
        
        matchWon = {
                "event": "match-won",
                "player": currentPlayerName,
                "game": {
                    "mode": variant,
                    "dartsThrownValue": throwPoints                    
                } 
            }
        broadcast(matchWon)

        if play_sound_effect('matchshot') == False:
            play_sound_effect('gameshot')
        play_sound_effect(currentPlayerName, True)
        if AMBIENT_SOUNDS != 0.0:
            if play_sound_effect('ambient_matchshot', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS) == False:
                play_sound_effect('ambient_gameshot', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
        setup_caller()
        ppi('Gameshot and match')

    # Check for gameshot
    elif m['gameWinner'] != -1 and isGameFinished == False:
        isGameFin = True

        throwPoints = 0
        lastPoints = ''
        for t in turns['throws']:
            number = t['segment']['number']
            if number in SUPPORTED_CRICKET_FIELDS:
                throwPoints += (t['segment']['multiplier'] * number)
                lastPoints += 'x' + str(t['segment']['name'])
        lastPoints = lastPoints[1:]
        
        gameWon = {
                "event": "game-won",
                "player": currentPlayerName,
                "game": {
                    "mode": variant,
                    "dartsThrownValue": throwPoints
                } 
            }
        broadcast(gameWon)

        play_sound_effect('gameshot')
        play_sound_effect(currentPlayerName, True)
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect('ambient_gameshot', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
        if RANDOM_CALLER_EACH_LEG:
            setup_caller()
        ppi('Gameshot')
    
    # Check for matchon
    elif m['gameScores'][0] == 0 and m['scores'] == None and turns['throws'] == None and m['round'] == 1 and m['leg'] == 1 and m['set'] == 1:
        isGameOn = True
        isGameFinished = False
        
        matchStarted = {
            "event": "match-started",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                # TODO: fix
                "special": "TODO"
                }     
            }
        broadcast(matchStarted)

        play_sound_effect(currentPlayerName, False)
        if play_sound_effect('matchon', True) == False:
            play_sound_effect('gameon', True)
        # play only if it is a real match not just legs!
        if AMBIENT_SOUNDS != 0.0 and ('legs' in m and 'sets'):
            if play_sound_effect('ambient_matchon', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS) == False:
                play_sound_effect('ambient_gameon', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
        ppi('Matchon')

    # Check for gameon
    elif m['gameScores'][0] == 0 and m['scores'] == None and turns['throws'] == None and m['round'] == 1:
        isGameOn = True
        isGameFinished = False
        
        gameStarted = {
            "event": "game-started",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                # TODO: fix
                "special": "TODO"
                }     
            }
        broadcast(gameStarted)

        play_sound_effect(currentPlayerName, False)
        play_sound_effect('gameon', True)
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect('ambient_gameon', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
        ppi('Gameon')

    # Check for busted turn
    elif turns['busted'] == True:
        lastPoints = "B"
        isGameFinished = False
        busted = { 
                    "event": "busted",
                    "player": currentPlayerName,
                    "game": {
                        "mode": variant
                    }       
                }
        broadcast(busted)

        play_sound_effect('busted')
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect('ambient_noscore', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
        ppi('Busted')

    # Check for 1. Dart
    elif turns != None and turns['throws'] != None and len(turns['throws']) == 1:
        isGameFinished = False

    # Check for 2. Dart
    elif turns != None and turns['throws'] != None and len(turns['throws']) == 2:
        isGameFinished = False

    # Check for 3. Dart - points call
    elif turns != None and turns['throws'] != None and len(turns['throws']) == 3:
        isGameFinished = False

        throwPoints = 0
        lastPoints = ''
        for t in turns['throws']:
            number = t['segment']['number']
            if number in SUPPORTED_CRICKET_FIELDS:
                throwPoints += (t['segment']['multiplier'] * number)
                lastPoints += 'x' + str(t['segment']['name'])
        lastPoints = lastPoints[1:]

        dartsThrown = {
            "event": "darts-thrown",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                "dartNumber": "3",
                "dartValue": throwPoints,        

            }
        }
        broadcast(dartsThrown)

        play_sound_effect(str(throwPoints))
        if AMBIENT_SOUNDS != 0.0:
            if throwPoints == 0:
                play_sound_effect('ambient_noscore', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
            elif throwPoints == 180:
                play_sound_effect('ambient_180', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
            elif throwPoints >= 153:
                play_sound_effect('ambient_150more', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)   
            elif throwPoints >= 120:
                play_sound_effect('ambient_120more', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
            elif throwPoints >= 100:
                play_sound_effect('ambient_100more', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)
            elif throwPoints >= 50:
                play_sound_effect('ambient_50more', AMBIENT_SOUNDS_AFTER_CALLS, volumeMult = AMBIENT_SOUNDS)

        ppi("Turn ended")
    
    # Playerchange
    if isGameOn == False and turns != None and turns['throws'] == None or isGameFinished == True:
        dartsPulled = {
            "event": "darts-pulled",
            "player": str(currentPlayer['name']),
            "game": {
                "mode": variant,
                # TODO: fix
                "pointsLeft": "0",
                # TODO: fix
                "dartsThrown": "3",
                "dartsThrownValue": lastPoints,
                "busted": str(turns['busted'])
                # TODO: fix
                # "darts": [
                #     {"number": "1", "value": "60"},
                #     {"number": "2", "value": "60"},
                #     {"number": "3", "value": "60"}
                # ]
            }
        }
        broadcast(dartsPulled)

        play_sound_effect('playerchange')
        ppi("Next player")

    if isGameFin == True:
        isGameFinished = True


def broadcast(data):
    def process(*args):
        global server
        server.send_message_to_all(json.dumps(data, indent=2).encode('utf-8'))
    threading.Thread(target=process).start()
            

def connect_autodarts():
    def process(*args):
        global accessToken

        # Configure client
        keycloak_openid = KeycloakOpenID(server_url = AUTODART_AUTH_URL,
                                            client_id = AUTODART_CLIENT_ID,
                                            realm_name = AUTODART_REALM_NAME,
                                            verify = True)

        # Get Token
        token = keycloak_openid.token(AUTODART_USER_EMAIL, AUTODART_USER_PASSWORD)
        accessToken = token['access_token']
        # ppi(token)


        # Get Ticket
        ticket = requests.post(AUTODART_AUTH_TICKET_URL, headers={'Authorization': 'Bearer ' + token['access_token']})
        # ppi(ticket.text)


        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(AUTODART_WEBSOCKET_URL + ticket.text,
                                on_open = on_open_autodarts,
                                on_message = on_message_autodarts,
                                on_error = on_error_autodarts,
                                on_close = on_close_autodarts)

        ws.run_forever()
    threading.Thread(target=process).start()

def on_open_autodarts(ws):
    try:
        ppi('Receiving live information from ' + AUTODART_URL)
        ppi('!!! In case that calling is not working, please check your Board-ID (-B) for correctness !!!')
        paramsSubscribeMatchesEvents = {
            "channel": "autodarts.matches",
            "type": "subscribe",
            "topic": "*.state"
        }
        ws.send(json.dumps(paramsSubscribeMatchesEvents))

        receive_local_board_address()
    except Exception as e:
        ppe('WS-Open failed: ', e)

def on_message_autodarts(ws, message):
    def process(*args):
        try:
            global lastMessage
            m = json.loads(message)

            # ppi(json.dumps(data, indent = 4, sort_keys = True))

            if m['channel'] == 'autodarts.matches':
                global currentMatch
                data = m['data']
                listen_to_newest_match(data, ws)

                # ppi('Current Match: ' + currentMatch)
                if('turns' in data and len(data['turns']) >=1):
                    data['turns'][0].pop("id", None)
                    data['turns'][0].pop("createdAt", None)

                if lastMessage != data and currentMatch != None and data['id'] == currentMatch:
                    lastMessage = data
                    # ppi(json.dumps(data, indent = 4, sort_keys = True))

                    variant = data['variant']
                    if variant == 'X01' or variant == 'Random Checkout':
                        process_match_x01(data)
                    elif variant == 'Cricket':
                        process_match_cricket(data)
        except Exception as e:
            ppe('WS-Message failed: ', e)

    threading.Thread(target=process).start()

def on_close_autodarts(ws, close_status_code, close_msg):
    try:
        ppi("Websocket closed")
        ppi(close_msg)
        ppi(close_status_code)
        ppi("Retry : %s" % time.ctime())
        time.sleep(3)
        connect_autodarts()
    except Exception as e:
        ppe('WS-Close failed: ', e)
    
def on_error_autodarts(ws, error):
    try:
        ppi(error)
    except Exception as e:
        ppe('WS-Error failed: ', e)


def client_new_message(client, server, message):
    def process(*args):
        try:
            ppi('CLIENT MESSAGE: ' + str(message))

            if boardManagerAddress != None and boardManagerAddress != 'http://':
                if message.startswith('board-start'):
                    msg_splitted = message.split(':')
                    if len(msg_splitted) > 1:
                        time.sleep(float(msg_splitted[1]))
                    res = requests.put(boardManagerAddress + '/api/start')
                    # ppi(res)

                elif message == 'board-stop':
                    res = requests.put(boardManagerAddress + '/api/stop')
                    # ppi(res)
            else:
              ppi('Can not start board as board-address is unknown: ' + str(boardManagerAddress))  

        except Exception as e:
            ppe('WS-Message failed: ', e)
    threading.Thread(target=process).start()

def new_client(client, server):
    ppi('NEW CLIENT CONNECTED: ' + str(client))

def client_left(client, server):
    ppi('CLIENT DISCONNECTED: ' + str(client))





if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    
    ap.add_argument("-U", "--autodarts_email", required=True, help="Registered email address at " + AUTODART_URL)
    ap.add_argument("-P", "--autodarts_password", required=True, help="Registered password address at " + AUTODART_URL)
    ap.add_argument("-B", "--autodarts_board_id", required=True, help="Registered board-id at " + AUTODART_URL)
    ap.add_argument("-M", "--media_path", required=True, help="Absolute path to your media folder. You can download free sounds at https://freesound.org/")
    ap.add_argument("-MS", "--media_path_shared", required=False, default=DEFAULT_EMPTY_PATH, help="Absolute path to shared media folder (every caller get sounds)")
    ap.add_argument("-V", "--caller_volume", type=float, default=1.0, required=False, help="Set the caller volume between 0.0 (silent) and 1.0 (max)")
    ap.add_argument("-C", "--caller", default=DEFAULT_CALLER, required=False, help="Sets a particular caller")
    ap.add_argument("-R", "--random_caller", type=int, choices=range(0, 2), default=0, required=False, help="If '1', the application will randomly choose a caller each game. It only works when your base-media-folder has subfolders with its files")
    ap.add_argument("-L", "--random_caller_each_leg", type=int, choices=range(0, 2), default=0, required=False, help="If '1', the application will randomly choose a caller each leg instead of each game. It only works when 'random_caller=1'")
    ap.add_argument("-E", "--call_every_dart", type=int, choices=range(0, 2), default=0, required=False, help="If '1', the application will call every thrown dart")
    ap.add_argument("-ESF", "--call_every_dart_single_files", type=int, choices=range(0, 2), default=1, required=False, help="If '1', the application will call a every dart by using single, dou.., else it uses two separated sounds: single + x (score)")
    ap.add_argument("-PCC", "--possible_checkout_call", type=int, choices=range(0, 2), default=1, required=False, help="If '1', the application will call a possible checkout starting at 170")
    ap.add_argument("-PCCSF", "--possible_checkout_call_single_files", type=int, choices=range(0, 2), default=0, required=False, help="If '1', the application will call a possible checkout by using yr_2-yr_170, else it uses two separated sounds: you_require + x")
    ap.add_argument("-A", "--ambient_sounds", type=float, default=0.0, required=False, help="If > '0.0' (volume), the application will call a ambient_*-Sounds")
    ap.add_argument("-AAC", "--ambient_sounds_after_calls", type=int, choices=range(0, 2), default=0, required=False, help="If '1', the ambient sounds will appear after calling is finished") 
    ap.add_argument("-DL", "--downloads", type=int, choices=range(0, 2), default=DEFAULT_DOWNLOADS, required=False, help="If '1', the application will try to download a curated list of caller-voices")
    ap.add_argument("-DLL", "--downloads_limit", type=int, choices=range(0, 1000), default=DEFAULT_DOWNLOADS_LIMIT, required=False, help="If '1', the application will try to download a only the X newest caller-voices. -DLN needs to be activated.")
    ap.add_argument("-DLP", "--downloads_path", required=False, default=DEFAULT_DOWNLOADS_PATH, help="Absolute path for temporarly downloads")
    ap.add_argument("-HP", "--host_port", required=False, type=int, default=DEFAULT_HOST_PORT, help="Host-Port")
    ap.add_argument("-DEB", "--debug", type=int, choices=range(0, 2), default=False, required=False, help="If '1', the application will output additional information")
    ap.add_argument("-MIF", "--mixer_frequency", type=int, required=False, default=DEFAULT_MIXER_FREQUENCY, help="Pygame mixer frequency")
    ap.add_argument("-MIS", "--mixer_size", type=int, required=False, default=DEFAULT_MIXER_SIZE, help="Pygame mixer size")
    ap.add_argument("-MIC", "--mixer_channels", type=int, required=False, default=DEFAULT_MIXER_CHANNELS, help="Pygame mixer channels")
    ap.add_argument("-MIB", "--mixer_buffersize", type=int, required=False, default=DEFAULT_MIXER_BUFFERSIZE, help="Pygame mixer buffersize")
    

    args = vars(ap.parse_args())

    

    AUTODART_USER_EMAIL = args['autodarts_email']                          
    AUTODART_USER_PASSWORD = args['autodarts_password']              
    AUTODART_USER_BOARD_ID = args['autodarts_board_id']        
    AUDIO_MEDIA_PATH = Path(args['media_path'])
    AUDIO_MEDIA_PATH_SHARED = Path(args['media_path_shared']) 
    AUDIO_CALLER_VOLUME = args['caller_volume']
    CALLER = args['caller']
    RANDOM_CALLER = args['random_caller']   
    RANDOM_CALLER_EACH_LEG = args['random_caller_each_leg']   
    CALL_EVERY_DART = args['call_every_dart']
    CALL_EVERY_DART_SINGLE_FILE = args['call_every_dart_single_files']
    POSSIBLE_CHECKOUT_CALL = args['possible_checkout_call']
    POSSIBLE_CHECKOUT_CALL_SINGLE_FILE = args['possible_checkout_call_single_files']
    AMBIENT_SOUNDS = args['ambient_sounds']
    AMBIENT_SOUNDS_AFTER_CALLS = args['ambient_sounds_after_calls']
    DOWNLOADS = args['downloads']
    DOWNLOADS_LIMIT = args['downloads_limit']
    DOWNLOADS_PATH = args['downloads_path']
    HOST_PORT = args['host_port']
    DEBUG = args['debug']
    MIXER_FREQUENCY = args['mixer_frequency']
    MIXER_SIZE = args['mixer_size']
    MIXER_CHANNELS = args['mixer_channels']
    MIXER_BUFFERSIZE = args['mixer_buffersize']

    global server
    server = None

    global accessToken
    accessToken = None

    global boardManagerAddress
    boardManagerAddress = None

    global lastMessage
    lastMessage = None

    global currentMatch
    currentMatch = None

    global caller
    caller = None

    global lastPoints
    lastPoints = None

    global isGameFinished
    isGameFinished = False


    # Initialize sound-output
    mixer.pre_init(MIXER_FREQUENCY, MIXER_SIZE, MIXER_CHANNELS, MIXER_BUFFERSIZE) 
    mixer.init()

    if DEBUG:
        ppi('Started with following arguments:')
        ppi(json.dumps(args, indent=4))

    osType = platform.system()
    osName = os.name
    osRelease = platform.release()
    print('\r\n')
    print('##########################################')
    print('       WELCOME TO AUTODARTS-CALLER')
    print('##########################################')
    print('VERSION: ' + VERSION)
    print('RUNNING OS: ' + osType + ' | ' + osName + ' | ' + osRelease)
    print('SUPPORTED GAME-VARIANTS: ' + " ".join(str(x) for x in SUPPORTED_GAME_VARIANTS) )
    print('\r\n')
    
    try:
        download_callers()
    except Exception as e:
        ppe("Caller-profile fetching failed: ", e)

    try:  
        setup_caller()
        connect_autodarts()
        
        server = WebsocketServer(host=DEFAULT_HOST_IP, port=HOST_PORT, loglevel=logging.ERROR)
        server.set_fn_new_client(new_client)
        server.set_fn_client_left(client_left)
        server.set_fn_message_received(client_new_message)
        server.run_forever()
    except Exception as e:
        ppe("Connect failed: ", e)
   
