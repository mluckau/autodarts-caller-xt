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
import socket
from websocket_server import WebsocketServer
import threading
import logging
from download import download
import shutil
import csv
import math
import ssl
import certifi
from mask import mask
from urllib.parse import quote, unquote
from flask import Flask, render_template, send_from_directory

os.environ["SSL_CERT_FILE"] = certifi.where()

plat = platform.system()
if plat == "Windows":
    from pycaw.pycaw import AudioUtilities


sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
sh.setFormatter(formatter)
logger = logging.getLogger()
logger.handlers.clear()
logger.setLevel(logging.INFO)
logger.addHandler(sh)

app = Flask(__name__)
main_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(main_directory)


VERSION = "2.4.6"

DEFAULT_HOST_IP = "0.0.0.0"
DEFAULT_HOST_PORT = 8079
DEFAULT_CALLER = None
DEFAULT_RANDOM_CALLER_LANGUAGE = 0
DEFAULT_RANDOM_CALLER_GENDER = 0
DEFAULT_WEB_CALLER_PORT = 5000
DEFAULT_DOWNLOADS = True
DEFAULT_DOWNLOADS_LANGUAGE = 1
DEFAULT_DOWNLOADS_LIMIT = 0
DEFAULT_DOWNLOADS_PATH = "caller-downloads-temp"
DEFAULT_CALLERS_BANNED_FILE = "autodarts-caller-banned.txt"
DEFAULT_EMPTY_PATH = ""
DEFAULT_MIXER_FREQUENCY = 44100
DEFAULT_MIXER_SIZE = 32
DEFAULT_MIXER_CHANNELS = 2
DEFAULT_MIXER_BUFFERSIZE = 4096

AUTODART_URL = "https://autodarts.io"
AUTODART_AUTH_URL = "https://login.autodarts.io/"
AUTODART_AUTH_TICKET_URL = "https://api.autodarts.io/ms/v0/ticket"
AUTODART_CLIENT_ID = "autodarts-app"
AUTODART_REALM_NAME = "autodarts"
AUTODART_MATCHES_URL = "https://api.autodarts.io/gs/v0/matches/"
AUTODART_BOARDS_URL = "https://api.autodarts.io/bs/v0/boards/"
AUTODART_WEBSOCKET_URL = "wss://api.autodarts.io/ms/v0/subscribe?ticket="

SUPPORTED_SOUND_FORMATS = [".mp3", ".wav"]
SUPPORTED_GAME_VARIANTS = ["X01", "Cricket", "Random Checkout"]
SUPPORTED_CRICKET_FIELDS = [15, 16, 17, 18, 19, 20, 25]
BOGEY_NUMBERS = [169, 168, 166, 165, 163, 162, 159]
SCHNAPSZAHLEN = [111, 222, 333, 444, 555, 666, 777, 888]

CALLER_LANGUAGES = {
    1: [
        "english",
        "en",
    ],
    2: [
        "french",
        "fr",
    ],
    3: [
        "russian",
        "ru",
    ],
    4: [
        "german",
        "de",
    ],
    5: [
        "spanish",
        "es",
    ],
    6: [
        "dutch",
        "nl",
    ],
}
CALLER_GENDERS = {
    1: ["female", "f"],
    2: ["male", "m"],
}
CALLER_PROFILES = {
    # murf
    "charles-m-english-us-canada": "https://drive.google.com/file/d/1-CrWSFHBoT_I9kzDuo7PR7FLCfEO-Qg-/view?usp=sharing",
    "clint-m-english-us-canada": "https://drive.google.com/file/d/1-IQ9Bvp1i0jG6Bu9fMWhlbyAj9SkoVGb/view?usp=sharing",
    "alicia-f-english-us-canada": "https://drive.google.com/file/d/1-Cvk-IczRjOphDOCA14NwE1hy4DAB8Tt/view?usp=sharing",
    "kushal-m-english-india": "https://drive.google.com/file/d/1-GavAG_oa3MrrremanvfYSfMI0U784EN/view?usp=sharing",
    "kylie-f-english-australia": "https://drive.google.com/file/d/1-Y6XpdFjOotSLBi0sInf5CGpAAV3mv0b/view?usp=sharing",
    "ruby-f-english-uk": "https://drive.google.com/file/d/1-kqVwCd4HJes0EVNda5EOF6tTwUxql3z/view?usp=sharing",
    "ethan-m-english-us-canada": "https://drive.google.com/file/d/106PG96DLzcHHusbQ2zRfub2ZVXbz5TPs/view?usp=sharing",
    "mitch-m-english-australia": "https://drive.google.com/file/d/10XEf0okustuoHnu2h_4eqRA6G-2d2mH1/view?usp=sharing",
    "ava-f-english-us-canada": "https://drive.google.com/file/d/10XtdjfORUreALkcUxbDhjb0Bo6ym7IDK/view?usp=sharing",
    "aiden-m-english-uk": "https://drive.google.com/file/d/10bYvcqp1nzqJnBDC7B6u7s8aequ5wGat/view?usp=sharing",
    "theo-m-english-uk": "https://drive.google.com/file/d/10eQaYMZM3tkIA2PIDsb0r-5NhyDU86-C/view?usp=sharing",
    "emily-f-english-scottish": "https://drive.google.com/file/d/10mOzTjA5tqBZCKI3EqxJ0YvQptqtMNQg/view?usp=sharing",
    # google
    "en-US-Wavenet-E-FEMALE": "https://drive.google.com/file/d/1GdhQRbNeHW2vyTmn3g67SiWDDh8_7Erq/view?usp=sharing",
    "en-US-Wavenet-G-FEMALE": "https://drive.google.com/file/d/1pWVKOgx-4V-1TKOi-g8rJDOlcyWE4zdq/view?usp=sharing",
    "en-US-Wavenet-H-FEMALE": "https://drive.google.com/file/d/1c2FO385Fb7d4Q8xeVd-f8WnkCVh-KqDs/view?usp=sharing",
    "en-US-Wavenet-I-MALE": "https://drive.google.com/file/d/1UZqw_KIGBqCJynftLuWi-b2p5ONOS6ue/view?usp=sharing",
    "en-US-Wavenet-J-MALE": "https://drive.google.com/file/d/16wiopEwx56NrBcnMt0LSZqsgemHkJhvR/view?usp=sharing",
    "en-US-Wavenet-A-MALE": "https://drive.google.com/file/d/1v1EfisMblN68GDbdHa-9Qg9xryGFM7mD/view?usp=sharing",
    "en-US-Wavenet-F-FEMALE": "https://drive.google.com/file/d/1iJ1duwQVFBCMGhqHdLmoz20s7uFfLhoA/view?usp=sharing",
    "fr-FR-Wavenet-E-FEMALE": "https://drive.google.com/file/d/1G39Cet8MrY_KqXUHS8q8cDRYJ9lPHxpj/view?usp=sharing",
    "fr-FR-Wavenet-B-MALE": "https://drive.google.com/file/d/1feFvXtrB5EKD72g3qc1DPrLTUUW7yHK0/view?usp=sharing",
    "ru-RU-Wavenet-E-FEMALE": "https://drive.google.com/file/d/1A_4iAsmPkmC2BBWaUGQ7xwFeueAMszhj/view?usp=sharing",
    "ru-RU-Wavenet-B-MALE": "https://drive.google.com/file/d/1-3SNrGeDwyTuGgt0hEKFpMpJyT_idF_0/view?usp=sharing",
    "de-DE-Wavenet-F-FEMALE": "https://drive.google.com/file/d/1o_l--T7YEvGWcRlUvhwPWxWqNFN3LGMz/view?usp=sharing",
    "de-DE-Wavenet-B-MALE": "https://drive.google.com/file/d/1IhPiCyZoRP1jLZGEvBe1N4HAV1vQhD1t/view?usp=sharing",
    "es-ES-Wavenet-C-FEMALE": "https://drive.google.com/file/d/1h6RrJxTT1vZfecOG84UOpLP_2FYsDtES/view?usp=sharing",
    "es-ES-Wavenet-B-MALE": "https://drive.google.com/file/d/1ErnbxFXJa69ccJVfSzAvqmD49QLz3Rez/view?usp=sharing",
    "nl-NL-Wavenet-B-MALE": "https://drive.google.com/file/d/12mlrKqjEO87W10lmZiDAqcTnwzc8bUCv/view?usp=sharing",
    "nl-NL-Wavenet-D-FEMALE": "https://drive.google.com/file/d/1tTe9viNMPXPsQIrZtPRF0KuBXkgeESA3/view?usp=sharing",
    # amazon
    "en-US-Stephen-Male": "https://drive.google.com/file/d/1IkE-y53J_eNLE7l137rH2__qHvByN2Pf/view?usp=sharing",
    "en-US-Ivy-Female": "https://drive.google.com/file/d/1heQP6pWgEhuMGd4f4WpPD3wmXwQQq7J5/view?usp=sharing",
    "de-DE-Vicki-Female": "https://drive.google.com/file/d/1AZKSHs4XjFicR7FeppBjwJ6u-dDt8h7L/view?usp=sharing",
    "de-DE-Daniel-Male": "https://drive.google.com/file/d/1yRoEknlGOtmDb_rwh0WmDmWFPU3aXhcy/view?usp=sharing",
    "en-US-Kendra-Female": "https://drive.google.com/file/d/1G6nfnh7srepaVrkey0_C4D5HunfXeRAn/view?usp=sharing",
    "en-US-Joey-Male": "https://drive.google.com/file/d/1XS6FcxmpaxzStLcAW8G5l0nQz3f5CrAT/view?usp=sharing"
    # 'TODONAME': 'TODOLINK',
    # 'TODONAME': 'TODOLINK',
}
FIELD_COORDS = {
    "0": {"x": 0.016160134143785285, "y": 1.1049884720184449},
    "S1": {"x": 0.2415216935652902, "y": 0.7347516243974009},
    "D1": {"x": 0.29786208342066656, "y": 0.9359673024523162},
    "T1": {"x": 0.17713267658771747, "y": 0.5818277090756655},
    "S2": {"x": 0.4668832529867955, "y": -0.6415636134982183},
    "D2": {"x": 0.5876126598197445, "y": -0.7783902745755609},
    "T2": {"x": 0.35420247327604254, "y": -0.4725424439320897},
    "S3": {"x": 0.008111507021588693, "y": -0.7864389016977573},
    "D3": {"x": -0.007985747222804492, "y": -0.9715573255082791},
    "T3": {"x": -0.007985747222804492, "y": -0.5932718507650387},
    "S4": {"x": 0.6439530496751206, "y": 0.4530496751205198},
    "D4": {"x": 0.7888283378746596, "y": 0.5657304548312723},
    "T4": {"x": 0.48298050723118835, "y": 0.36451477677635713},
    "S5": {"x": -0.23334730664430925, "y": 0.7508488786417943},
    "D5": {"x": -0.31383357786627536, "y": 0.9279186753301195},
    "T5": {"x": -0.1850555439111297, "y": 0.5737790819534688},
    "S6": {"x": 0.7888283378746596, "y": -0.013770697966883233},
    "D6": {"x": 0.9739467616851814, "y": 0.010375183399706544},
    "T6": {"x": 0.5956612869419406, "y": -0.005722070844686641},
    "S7": {"x": -0.4506602389436176, "y": -0.6335149863760215},
    "D7": {"x": -0.5713896457765667, "y": -0.7703416474533641},
    "T7": {"x": -0.3540767134772585, "y": -0.4725424439320897},
    "S8": {"x": -0.7323621882204988, "y": -0.239132257388388},
    "D8": {"x": -0.9255292391532174, "y": -0.2954726472437643},
    "T8": {"x": -0.5713896457765667, "y": -0.18279186753301202},
    "S9": {"x": -0.627730035631943, "y": 0.4691469293649132},
    "D9": {"x": -0.7726053238314818, "y": 0.5657304548312723},
    "T9": {"x": -0.48285474743240414, "y": 0.34841752253196395},
    "S10": {"x": 0.7244393208970865, "y": -0.23108363026619158},
    "D10": {"x": 0.9256549989520018, "y": -0.28742402012156787},
    "T10": {"x": 0.5715154055753511, "y": -0.19084049465520878},
    "S11": {"x": -0.7726053238314818, "y": -0.005722070844686641},
    "D11": {"x": -0.9657723747642004, "y": -0.005722070844686641},
    "T11": {"x": -0.5955355271431566, "y": 0.0023265562775099512},
    "S12": {"x": -0.4506602389436176, "y": 0.6140222175644519},
    "D12": {"x": -0.5633410186543703, "y": 0.7910920142527772},
    "T12": {"x": -0.3540767134772585, "y": 0.4932928107315028},
    "S13": {"x": 0.7244393208970865, "y": 0.24378536994340808},
    "D13": {"x": 0.917606371829805, "y": 0.308174386920981},
    "T13": {"x": 0.5634667784531546, "y": 0.18744498008803193},
    "S14": {"x": 0.6278557954307273, "y": -0.46449381680989327},
    "D14": {"x": -0.9255292391532174, "y": 0.308174386920981},
    "T14": {"x": -0.5713896457765667, "y": 0.19549360721022835},
    "S15": {"x": 0.6278557954307273, "y": -0.46449381680989327},
    "D15": {"x": 0.7888283378746596, "y": -0.5771745965206456},
    "T15": {"x": 0.4910291343533851, "y": -0.34376440997694424},
    "S16": {"x": -0.6196814085097464, "y": -0.4725424439320897},
    "D16": {"x": -0.7967512051980717, "y": -0.5610773422762524},
    "T16": {"x": -0.49090337455460076, "y": -0.33571578285474746},
    "S17": {"x": 0.2415216935652902, "y": -0.730098511842381},
    "D17": {"x": 0.29786208342066656, "y": -0.9152169356529029},
    "T17": {"x": 0.18518130370991423, "y": -0.5691259693984492},
    "S18": {"x": 0.48298050723118835, "y": 0.6462167260532384},
    "D18": {"x": 0.5554181513309578, "y": 0.799140641374974},
    "T18": {"x": 0.3292712798530314, "y": 0.49608083282302506},
    "S19": {"x": -0.2586037966932027, "y": -0.7658909981628906},
    "D19": {"x": -0.3134721371708513, "y": -0.9148193508879362},
    "T19": {"x": -0.19589712186160443, "y": -0.562094304960196},
    "S20": {"x": 0.00006123698714003468, "y": 0.7939375382731171},
    "D20": {"x": 0.01119619445411297, "y": 0.9726766446223462},
    "T20": {"x": 0.00006123698714003468, "y": 0.6058175137783223},
    "25": {"x": 0.06276791181873864, "y": 0.01794243723208814},
    "50": {"x": -0.007777097366809472, "y": 0.0022657685241886157},
}


def ppi(message, info_object=None, prefix="\r\n"):
    logger.info(prefix + str(message))
    if info_object != None:
        logger.info(str(info_object))


def ppe(message, error_object):
    ppi(message)
    if DEBUG:
        logger.exception("\r\n" + str(error_object))


def get_local_ip_address(target="8.8.8.8"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((target, 80))
        ip_address = s.getsockname()[0]
        s.close()
    except:
        ip_address = DEFAULT_HOST_IP
    return ip_address


def download_callers():
    if DOWNLOADS:
        download_list = CALLER_PROFILES

        downloads_filtered = {}
        for speaker_name, speaker_download_url in download_list.items():
            if speaker_name.lower() not in caller_profiles_banned:
                downloads_filtered[speaker_name] = speaker_download_url
        download_list = downloads_filtered

        if DOWNLOADS_LANGUAGE > 0:
            downloads_filtered = {}
            for speaker_name, speaker_download_url in download_list.items():
                caller_language_key = grab_caller_language(speaker_name)
                if caller_language_key != DOWNLOADS_LANGUAGE:
                    continue
                downloads_filtered[speaker_name] = speaker_download_url
            download_list = downloads_filtered

        if (
            DOWNLOADS_LIMIT > 0
            and len(download_list) > 0
            and DOWNLOADS_LIMIT < len(download_list)
        ):
            download_list = {
                k: download_list[k]
                for k in list(download_list.keys())[-DOWNLOADS_LIMIT:]
            }

        if len(download_list) > 0:
            if os.path.exists(AUDIO_MEDIA_PATH) == False:
                os.mkdir(AUDIO_MEDIA_PATH)

        # Download and parse every caller-profile
        for cpr_name, cpr_download_url in download_list.items():
            try:
                # Check if caller-profile already present in users media-directory, yes ? -> stop for this caller-profile
                caller_profile_exists = os.path.exists(
                    os.path.join(AUDIO_MEDIA_PATH, cpr_name)
                )
                if caller_profile_exists == True:
                    # ppi('Caller-profile ' + cpr_name + ' already exists -> Skipping download')
                    continue

                # clean download-area!
                shutil.rmtree(DOWNLOADS_PATH, ignore_errors=True)
                if os.path.exists(DOWNLOADS_PATH) == False:
                    os.mkdir(DOWNLOADS_PATH)

                # Download caller-profile and extract archive
                dest = os.path.join(DOWNLOADS_PATH, "download.zip")

                # kind="zip",
                path = download(
                    cpr_download_url,
                    dest,
                    progressbar=True,
                    replace=False,
                    verbose=DEBUG,
                )

                # TEMP Test!!
                # shutil.copyfile('C:\\Users\\Luca\\Desktop\\WORK\\charles-m-english-us-canada\\download.zip', os.path.join(DOWNLOADS_PATH, 'download.zip'))

                shutil.unpack_archive(dest, DOWNLOADS_PATH)
                os.remove(dest)

                # Find sound-file-archive und extract it
                zip_filename = [
                    f for f in os.listdir(DOWNLOADS_PATH) if f.endswith(".zip")
                ][0]
                dest = os.path.join(DOWNLOADS_PATH, zip_filename)
                shutil.unpack_archive(dest, DOWNLOADS_PATH)
                os.remove(dest)

                # Find folder and rename it properly
                sound_folder = [
                    dirs for root, dirs, files in sorted(os.walk(DOWNLOADS_PATH))
                ][0][0]
                src = os.path.join(DOWNLOADS_PATH, sound_folder)
                dest = os.path.splitext(dest)[0]
                os.rename(src, dest)

                # Find template-file and parse it
                template_file = [
                    f for f in os.listdir(DOWNLOADS_PATH) if f.endswith(".csv")
                ][0]
                template_file = os.path.join(DOWNLOADS_PATH, template_file)
                san_list = list()
                with open(template_file, "r", encoding="utf-8") as f:
                    tts = list(csv.reader(f, delimiter=";"))
                    for event in tts:
                        sanitized = list(filter(None, event))
                        if len(sanitized) == 1:
                            sanitized.append(sanitized[0].lower())
                        san_list.append(sanitized)
                    # ppi(san_list)

                # Find origin-file
                origin_file = None
                files = [f for f in os.listdir(DOWNLOADS_PATH) if f.endswith(".txt")]
                if len(files) >= 1:
                    origin_file = os.path.join(DOWNLOADS_PATH, files[0])

                # Move template- and origin-file to sound-dir
                if origin_file != None:
                    shutil.move(origin_file, dest)
                shutil.move(template_file, dest)

                # Find all supported sound-files and remember names
                sounds = []
                for root, dirs, files in os.walk(dest):
                    for file in sorted(files):
                        if file.endswith(tuple(SUPPORTED_SOUND_FORMATS)):
                            sounds.append(os.path.join(root, file))
                # ppi(sounds)

                # Rename sound-files and copy files according the defined caller-keys
                for i in range(len(san_list) - 1):
                    current_sound = sounds[i]
                    current_sound_splitted = os.path.splitext(current_sound)
                    current_sound_extension = current_sound_splitted[1]

                    try:
                        row = san_list[i]
                        caller_keys = row[1:]
                        # ppi(caller_keys)

                        for ck in caller_keys:
                            multiple_file_name = os.path.join(
                                dest, ck + current_sound_extension
                            )
                            exists = os.path.exists(multiple_file_name)
                            # ppi('Test existance: ' + multiple_file_name)

                            counter = 0
                            while exists == True:
                                counter = counter + 1
                                multiple_file_name = os.path.join(
                                    dest,
                                    ck + "+" + str(counter) + current_sound_extension,
                                )
                                exists = os.path.exists(multiple_file_name)
                                # ppi('Test (' + str(counter) + ') existance: ' + multiple_file_name)

                            shutil.copyfile(current_sound, multiple_file_name)
                    except Exception as ie:
                        ppe('Failed to process entry "' + row[0] + '"', ie)
                    finally:
                        os.remove(current_sound)

                shutil.move(dest, AUDIO_MEDIA_PATH)
                ppi("A new caller was added: " + cpr_name)

            except Exception as e:
                ppe("Failed to process caller: " + cpr_name, e)
            finally:
                shutil.rmtree(DOWNLOADS_PATH, ignore_errors=True)


def ban_caller(only_change):
    global caller_title

    # ban/change not possible as caller is specified by user or current caller is 'None'
    if (
        CALLER != DEFAULT_CALLER
        and CALLER != ""
        and caller_title != ""
        and caller_title != None
    ):
        return

    if only_change:
        ccc_success = play_sound_effect(
            "control_change_caller", wait_for_last=False, volume_mult=1.0
        )
        if not ccc_success:
            play_sound_effect("control", wait_for_last=False, volume_mult=1.0)

    else:
        cbc_success = play_sound_effect(
            "control_ban_caller", wait_for_last=False, volume_mult=1.0
        )
        if not cbc_success:
            play_sound_effect("control", wait_for_last=False, volume_mult=1.0)

        global caller_profiles_banned
        caller_profiles_banned.append(caller_title)
        path_to_callers_banned_file = os.path.join(
            parent_directory, DEFAULT_CALLERS_BANNED_FILE
        )
        with open(path_to_callers_banned_file, "w") as bcf:
            for cpb in caller_profiles_banned:
                bcf.write(cpb.lower() + "\n")

    mirror_sounds()
    setup_caller()


def load_callers_banned():
    global caller_profiles_banned
    path_to_callers_banned_file = os.path.join(
        parent_directory, DEFAULT_CALLERS_BANNED_FILE
    )
    if os.path.exists(path_to_callers_banned_file):
        with open(path_to_callers_banned_file, "r") as bcf:
            caller_profiles_banned = list(set(line.strip() for line in bcf))
    else:
        caller_profiles_banned = []


def load_callers():
    # load shared-sounds
    shared_sounds = {}
    if AUDIO_MEDIA_PATH_SHARED != DEFAULT_EMPTY_PATH:
        for root, dirs, files in os.walk(AUDIO_MEDIA_PATH_SHARED):
            for filename in files:
                if filename.endswith(tuple(SUPPORTED_SOUND_FORMATS)):
                    full_path = os.path.join(root, filename)
                    base = os.path.splitext(filename)[0]
                    key = base.split("+", 1)[0]
                    if key in shared_sounds:
                        shared_sounds[key].append(full_path)
                    else:
                        shared_sounds[key] = [full_path]

    load_callers_banned()

    # load callers
    callers = []
    for root, dirs, files in os.walk(AUDIO_MEDIA_PATH):
        file_dict = {}
        for filename in files:
            if filename.endswith(tuple(SUPPORTED_SOUND_FORMATS)):
                full_path = os.path.join(root, filename)
                base = os.path.splitext(filename)[0]
                key = base.split("+", 1)[0]
                if key in file_dict:
                    file_dict[key].append(full_path)
                else:
                    file_dict[key] = [full_path]
        if file_dict:
            callers.append((root, file_dict))

    # add shared-sounds to callers
    for ss_k, ss_v in shared_sounds.items():
        for root, c_keys in callers:
            if ss_k in c_keys:
                # for sound_variant in ss_v:
                #     c_keys[ss_k].append(sound_variant)
                if CALL_EVERY_DART == True and CALL_EVERY_DART_SINGLE_FILE == True:
                    c_keys[ss_k] = ss_v
                else:
                    for sound_variant in ss_v:
                        c_keys[ss_k].append(sound_variant)
            else:
                c_keys[ss_k] = ss_v

    return callers


def grab_caller_name(caller_root):
    return os.path.basename(os.path.normpath(caller_root[0])).lower()


def grab_caller_language(caller_name):
    first_occurrences = []
    caller_name = "-" + caller_name + "-"
    for key in CALLER_LANGUAGES:
        for tag in CALLER_LANGUAGES[key]:
            tag_with_dashes = "-" + tag + "-"
            index = caller_name.find(tag_with_dashes)
            if index != -1:  # find returns -1 if the tag is not found
                first_occurrences.append((index, key))

    if not first_occurrences:  # if the list is empty
        return None

    # Sort the list of first occurrences and get the language of the tag that appears first
    first_occurrences.sort(key=lambda x: x[0])
    return first_occurrences[0][1]


def grab_caller_gender(caller_name):
    first_occurrences = []
    caller_name = "-" + caller_name + "-"
    for key in CALLER_GENDERS:
        for tag in CALLER_GENDERS[key]:
            tag_with_dashes = "-" + tag + "-"
            index = caller_name.find(tag_with_dashes)
            if index != -1:  # find returns -1 if the tag is not found
                first_occurrences.append((index, key))

    if not first_occurrences:  # if the list is empty
        return None

    # Sort the list of first occurrences and get the gender of the tag that appears first
    first_occurrences.sort(key=lambda x: x[0])
    return first_occurrences[0][1]

    first_occurrences = []
    for key in CALLER_GENDERS:
        for tag in CALLER_GENDERS[key]:
            index = caller_name.find(tag)
            if index != -1:  # find returns -1 if the tag is not found
                first_occurrences.append((index, key))

    if not first_occurrences:  # if the list is empty
        return None

    # Sort the list of first occurrences and get the gender of the tag that appears first
    first_occurrences.sort(key=lambda x: x[0])
    return first_occurrences[0][1]


def setup_caller():
    global caller
    global caller_title
    global caller_profiles_banned
    caller = None
    caller_title = ""

    callers = load_callers()
    ppi(str(len(callers)) + " caller(s) found.")

    if CALLER != DEFAULT_CALLER and CALLER != "":
        wished_caller = CALLER.lower()
        for c in callers:
            caller_name = os.path.basename(os.path.normpath(c[0])).lower()
            ppi(caller_name, None, "")
            if caller == None and caller_name == wished_caller:
                caller = c

    else:
        for c in callers:
            caller_name = grab_caller_name(c)
            ppi(caller_name, None, "")

        if RANDOM_CALLER == False:
            caller = callers[0]
        else:
            callers_filtered = []
            for c in callers:
                caller_name = grab_caller_name(c)

                if caller_name in caller_profiles_banned:
                    continue

                if RANDOM_CALLER_LANGUAGE != 0:
                    caller_language_key = grab_caller_language(caller_name)
                    if caller_language_key != RANDOM_CALLER_LANGUAGE:
                        continue

                if RANDOM_CALLER_GENDER != 0:
                    caller_gender_key = grab_caller_gender(caller_name)
                    if caller_gender_key != RANDOM_CALLER_GENDER:
                        continue
                callers_filtered.append(c)

            if len(callers_filtered) > 0:
                caller = random.choice(callers_filtered)

    if caller != None:
        for sound_file_key, sound_file_values in caller[1].items():
            sound_list = list()
            for sound_file_path in sound_file_values:
                sound_list.append(sound_file_path)
            caller[1][sound_file_key] = sound_list

        caller_title = str(os.path.basename(os.path.normpath(caller[0])))
        ppi(
            "Your current caller: "
            + caller_title
            + " knows "
            + str(len(caller[1].values()))
            + " Sound-file-key(s)"
        )
        # ppi(caller[1])
        caller = caller[1]


def receive_local_board_address():
    try:
        global accessToken
        global boardManagerAddress

        if boardManagerAddress == None:
            res = requests.get(
                AUTODART_BOARDS_URL + AUTODART_USER_BOARD_ID,
                headers={"Authorization": "Bearer " + accessToken},
            )
            board_ip = res.json()["ip"]
            if board_ip != None and board_ip != "":
                boardManagerAddress = "http://" + board_ip
                ppi("Board-address: " + boardManagerAddress)
            else:
                boardManagerAddress = None
                ppi("Board-address: UNKNOWN")

    except Exception as e:
        boardManagerAddress = None
        ppe("Fetching local-board-address failed", e)


def play_sound(sound, wait_for_last, volume_mult):
    if WEB > 0:
        global mirror_files

        mirror_file = {
            "path": quote(sound, safe=""),
            "wait": wait_for_last,
        }
        mirror_files.append(mirror_file)

    if WEB == 0 or WEB == 2:
        if wait_for_last == True:
            while mixer.get_busy():
                time.sleep(0.01)

        s = mixer.Sound(sound)

        if AUDIO_CALLER_VOLUME is not None:
            s.set_volume(AUDIO_CALLER_VOLUME * volume_mult)
        s.play()

    ppi('Playing: "' + sound + '"')


def play_sound_effect(sound_file_key, wait_for_last=False, volume_mult=1.0):
    try:
        global caller
        play_sound(random.choice(caller[sound_file_key]), wait_for_last, volume_mult)
        return True
    except Exception as e:
        ppe(
            'Can not play sound for sound-file-key "'
            + sound_file_key
            + '" -> Ignore this or check existance; otherwise convert your file appropriate',
            e,
        )
        return False


def mirror_sounds():
    global mirror_files
    if WEB > 0 and len(mirror_files) != 0:
        # Example
        # {
        #     "event": "mirror",
        #     "files": [
        #         {
        #             "path": "C:\sounds\luca.mp3",
        #             "wait": False,
        #         },
        #         {
        #             "path": "C:\sounds\you_require.mp3",
        #             "wait": True,
        #         },
        #         {
        #             "path": "C:\sounds\40.mp3",
        #             "wait": True,
        #         }
        #     ]
        # }
        mirror = {"event": "mirror", "files": mirror_files}
        broadcast(mirror)
        mirror_files = []


def next_game():
    if (
        play_sound_effect("control_next_game", wait_for_last=False, volume_mult=1.0)
        == False
    ):
        play_sound_effect("control", wait_for_last=False, volume_mult=1.0)
    mirror_sounds()

    # post
    # https://api.autodarts.io/gs/v0/matches/<match-id>/games/next
    try:
        global accessToken
        global currentMatch

        receive_token_autodarts()

        if currentMatch != None:
            requests.post(
                AUTODART_MATCHES_URL + currentMatch + "/games/next",
                headers={"Authorization": "Bearer " + accessToken},
            )

    except Exception as e:
        ppe("Next game failed", e)


def next_throw():
    if play_sound_effect("control_next", wait_for_last=False, volume_mult=1.0) == False:
        play_sound_effect("control", wait_for_last=False, volume_mult=1.0)
    mirror_sounds()

    # post
    # https://api.autodarts.io/gs/v0/matches/<match-id>/players/next
    try:
        global accessToken
        global currentMatch

        receive_token_autodarts()

        if currentMatch != None:
            requests.post(
                AUTODART_MATCHES_URL + currentMatch + "/players/next",
                headers={"Authorization": "Bearer " + accessToken},
            )

    except Exception as e:
        ppe("Next throw failed", e)


def undo_throw():
    if play_sound_effect("control_undo", wait_for_last=False, volume_mult=1.0) == False:
        play_sound_effect("control", wait_for_last=False, volume_mult=1.0)
    mirror_sounds()

    # post
    # https://api.autodarts.io/gs/v0/matches/<match-id>/undo
    try:
        global accessToken
        global currentMatch

        receive_token_autodarts()

        if currentMatch != None:
            requests.post(
                AUTODART_MATCHES_URL + currentMatch + "/undo",
                headers={"Authorization": "Bearer " + accessToken},
            )
    except Exception as e:
        ppe("Undo throw failed", e)


def correct_throw(throw_indices, score):
    global currentMatch

    score = FIELD_COORDS[score]
    if currentMatch == None or len(throw_indices) > 3 or score == None:
        return

    cdcs_success = False
    cdcs_global = False
    for tii, ti in enumerate(throw_indices):
        wait = False
        if tii > 0 and cdcs_global == True:
            wait = True
        cdcs_success = play_sound_effect(
            f"control_dart_correction_{(int(ti) + 1)}",
            wait_for_last=wait,
            volume_mult=1.0,
        )
        if cdcs_success:
            cdcs_global = True

    if (
        cdcs_global == False
        and play_sound_effect(
            "control_dart_correction", wait_for_last=False, volume_mult=1.0
        )
        == False
    ):
        play_sound_effect("control", wait_for_last=False, volume_mult=1.0)
    mirror_sounds()

    # patch
    # https://api.autodarts.io/gs/v0/matches/<match-id>/throws
    # {
    #     "changes": {
    #         "1": {
    #             "x": x-coord,
    #             "y": y-coord
    #         },
    #         "2": {
    #             "x": x-coord,
    #             "y": y-coord
    #         }
    #     }
    # }
    try:
        global accessToken
        global lastCorrectThrow

        receive_token_autodarts()

        data = {"changes": {}}
        for ti in throw_indices:
            data["changes"][ti] = score

        # ppi(f'Data: {data}')
        if lastCorrectThrow == None or lastCorrectThrow != data:
            requests.patch(
                AUTODART_MATCHES_URL + currentMatch + "/throws",
                json=data,
                headers={"Authorization": "Bearer " + accessToken},
            )
            lastCorrectThrow = data
        else:
            lastCorrectThrow = None

    except Exception as e:
        lastCorrectThrow = None
        ppe("Correcting throw failed", e)


def listen_to_newest_match(m, ws):
    global currentMatch

    # EXAMPLE
    # {
    #     "channel": "autodarts.boards",
    #     "data": {
    #         "event": "start",
    #         "id": "82f917d0-0308-2c27-c4e9-f53ef2e98ad2"
    #     },
    #     "topic": "1ba2df53-9a04-51bc-9a5f-667b2c5f315f.matches"
    # }

    if m["event"] == "start":
        currentMatch = m["id"]
        ppi("Listen to match: " + currentMatch)

        try:
            setup_caller()
        except Exception as e:
            ppe("Setup callers failed!", e)

        try:
            global accessToken
            res = requests.get(
                AUTODART_MATCHES_URL + currentMatch,
                headers={"Authorization": "Bearer " + accessToken},
            )
            m = res.json()
            mode = m["variant"]

            # ppi(json.dumps(m, indent = 4, sort_keys = True))

            if mode == "X01":
                # Determine "baseScore"-Key
                base = "baseScore"
                if "target" in m["settings"]:
                    base = "target"

                matchStarted = {
                    "event": "match-started",
                    "player": m["players"][0]["name"],
                    "game": {
                        "mode": mode,
                        "pointsStart": str(m["settings"][base]),
                        # TODO: fix
                        "special": "TODO",
                    },
                }
                broadcast(matchStarted)

            elif mode == "Cricket":
                matchStarted = {
                    "event": "match-started",
                    "player": m["players"][0]["name"],
                    "game": {
                        "mode": mode,
                        # TODO: fix
                        "special": "TODO",
                    },
                }
                broadcast(matchStarted)

            callPlayerNameState = play_sound_effect(m["players"][0]["name"])
            if play_sound_effect("matchon", callPlayerNameState) == False:
                play_sound_effect("gameon", callPlayerNameState)

            if (
                AMBIENT_SOUNDS != 0.0
                and play_sound_effect(
                    "ambient_matchon",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
                == False
            ):
                play_sound_effect(
                    "ambient_gameon",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )

            mirror_sounds()
            ppi("Matchon")

        except Exception as e:
            ppe("Fetching initial match-data failed", e)

        global isGameFinished
        isGameFinished = False

        receive_local_board_address()
        # if boardManagerAddress != None:
        #     res = requests.post(boardManagerAddress + '/api/reset')
        #     time.sleep(0.25)
        #     res = requests.put(boardManagerAddress + '/api/start')

        paramsSubscribeMatchesEvents = {
            "channel": "autodarts.matches",
            "type": "subscribe",
            "topic": currentMatch + ".state",
        }

        ws.send(json.dumps(paramsSubscribeMatchesEvents))

    elif m["event"] == "finish" or m["event"] == "delete":
        ppi("Stop listening to match: " + m["id"])

        paramsUnsubscribeMatchEvents = {
            "type": "unsubscribe",
            "channel": "autodarts.matches",
            "topic": m["id"] + ".state",
        }
        ws.send(json.dumps(paramsUnsubscribeMatchEvents))

        if m["event"] == "delete":
            play_sound_effect("matchcancel")
            mirror_sounds()


def reset_checkouts_counter():
    global checkoutsCounter
    checkoutsCounter = {}


def increase_checkout_counter(player_index, remaining_score):
    global checkoutsCounter

    if player_index not in checkoutsCounter:
        checkoutsCounter[player_index] = {
            "remaining_score": remaining_score,
            "checkout_count": 1,
        }
    else:
        if checkoutsCounter[player_index]["remaining_score"] == remaining_score:
            checkoutsCounter[player_index]["checkout_count"] += 1
        else:
            checkoutsCounter[player_index]["remaining_score"] = remaining_score
            checkoutsCounter[player_index]["checkout_count"] = 1

    return checkoutsCounter[player_index]["checkout_count"] <= POSSIBLE_CHECKOUT_CALL


def checkout_only_yourself(currentPlayer):
    if POSSIBLE_CHECKOUT_CALL_YOURSELF_ONLY:
        if (
            "boardId" in currentPlayer
            and currentPlayer["boardId"] == AUTODART_USER_BOARD_ID
        ):
            return True
        else:
            return False
    return True


def process_match_x01(m):
    global accessToken
    global currentMatch
    global isGameFinished
    global lastPoints

    variant = m["variant"]
    currentPlayerIndex = m["player"]
    currentPlayer = m["players"][currentPlayerIndex]
    currentPlayerName = str(currentPlayer["name"]).lower()
    remainingPlayerScore = m["gameScores"][currentPlayerIndex]

    turns = m["turns"][0]
    points = str(turns["points"])
    busted = turns["busted"] == True
    matchshot = m["winner"] != -1 and isGameFinished == False
    gameshot = m["gameWinner"] != -1 and isGameFinished == False

    # Determine "baseScore"-Key
    base = "baseScore"
    if "target" in m["settings"]:
        base = "target"

    matchon = (
        m["settings"][base] == m["gameScores"][0]
        and turns["throws"] == None
        and m["leg"] == 1
        and m["set"] == 1
    )
    gameon = m["settings"][base] == m["gameScores"][0] and turns["throws"] == None

    # ppi('matchon: '+ str(matchon) )
    # ppi('gameon: '+ str(gameon) )
    # ppi('isGameFinished: ' + str(isGameFinished))

    pcc_success = False
    isGameFin = False

    if turns != None and turns["throws"] != None:
        lastPoints = points

    # Darts pulled (Playerchange and Possible-checkout)
    if (
        gameon == False
        and turns != None
        and turns["throws"] == None
        or isGameFinished == True
    ):
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
            },
        }
        # ppi(dartsPulled)
        broadcast(dartsPulled)

        if gameon == False and isGameFinished == False:
            # Check for possible checkout
            if (
                POSSIBLE_CHECKOUT_CALL
                and m["player"] == currentPlayerIndex
                and remainingPlayerScore <= 170
                and remainingPlayerScore not in BOGEY_NUMBERS
                and checkout_only_yourself(currentPlayer)
            ):
                if not increase_checkout_counter(
                    currentPlayerIndex, remainingPlayerScore
                ):
                    if AMBIENT_SOUNDS != 0.0:
                        play_sound_effect(
                            "ambient_checkout_call_limit",
                            AMBIENT_SOUNDS_AFTER_CALLS,
                            volume_mult=AMBIENT_SOUNDS,
                        )
                else:
                    play_sound_effect(currentPlayerName)

                    remaining = str(remainingPlayerScore)

                    if POSSIBLE_CHECKOUT_CALL_SINGLE_FILE:
                        pcc_success = play_sound_effect("yr_" + remaining, True)
                        if pcc_success == False:
                            pcc_success = play_sound_effect(remaining, True)
                    else:
                        pcc_success = play_sound_effect(
                            "you_require", True
                        ) and play_sound_effect(remaining, True)

                    ppi("Checkout possible: " + remaining)

            # Player`s turn-call
            if (
                CALL_CURRENT_PLAYER
                and m["player"] == currentPlayerIndex
                and pcc_success == False
            ):
                pcc_success = play_sound_effect(currentPlayerName)

            # Player-change
            if pcc_success == False and AMBIENT_SOUNDS != 0.0:
                play_sound_effect(
                    "ambient_playerchange",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )

            ppi("Next player")

    # Call every thrown dart
    elif (
        CALL_EVERY_DART == True
        and turns != None
        and turns["throws"] != None
        and len(turns["throws"]) >= 1
        and busted == False
        and matchshot == False
        and gameshot == False
    ):
        throwAmount = len(turns["throws"])
        type = turns["throws"][throwAmount - 1]["segment"]["bed"].lower()
        field_name = turns["throws"][throwAmount - 1]["segment"]["name"].lower()

        if field_name == "25":
            field_name = "sbull"

        # ppi("Type: " + str(type) + " - Field-name: " + str(field_name))

        if CALL_EVERY_DART_SINGLE_FILE == True:
            if play_sound_effect(field_name) == False:
                inner_outer = False
                if type == "singleouter" or type == "singleinner":
                    inner_outer = play_sound_effect(type)
                    if inner_outer == False:
                        play_sound_effect("single")
                else:
                    play_sound_effect(type)

        elif len(turns["throws"]) <= 2:
            field_number = str(turns["throws"][throwAmount - 1]["segment"]["number"])

            if type == "single" or type == "singleinner" or type == "singleouter":
                play_sound_effect(field_number)
            elif type == "double" or type == "triple":
                play_sound_effect(type)
                play_sound_effect(field_number, True)
            else:
                play_sound_effect("outside")

    # Check for matchshot
    if matchshot == True:
        isGameFin = True

        matchWon = {
            "event": "match-won",
            "player": currentPlayerName,
            "game": {"mode": variant, "dartsThrownValue": points},
        }
        broadcast(matchWon)

        if play_sound_effect("matchshot") == False:
            play_sound_effect("gameshot")

        play_sound_effect(currentPlayerName, True)

        if (
            play_sound_effect(
                "ambient_matchshot",
                AMBIENT_SOUNDS_AFTER_CALLS,
                volume_mult=AMBIENT_SOUNDS,
            )
            == False
        ):
            play_sound_effect(
                "ambient_gameshot",
                AMBIENT_SOUNDS_AFTER_CALLS,
                volume_mult=AMBIENT_SOUNDS,
            )

        if RANDOM_CALLER_EACH_LEG:
            setup_caller()
        ppi("Gameshot and match")

    # Check for gameshot
    elif gameshot == True:
        isGameFin = True

        gameWon = {
            "event": "game-won",
            "player": currentPlayerName,
            "game": {"mode": variant, "dartsThrownValue": points},
        }
        broadcast(gameWon)

        gameshotState = play_sound_effect("gameshot")

        currentPlayerScoreLegs = m["scores"][currentPlayerIndex]["legs"]
        # currentPlayerScoreSets = m['scores'][currentPlayerIndex]['sets']
        currentLeg = m["leg"]
        currentSet = m["set"]
        maxLeg = m["legs"]
        # maxSets = m['sets']

        # ppi('currentLeg: ' + str(currentLeg))
        # ppi('currentSet: ' + str(currentSet))

        if "sets" not in m:
            play_sound_effect("leg_" + str(currentLeg), gameshotState)
        else:
            if currentPlayerScoreLegs == 0:
                play_sound_effect("set_" + str(currentSet), gameshotState)
            else:
                play_sound_effect("leg_" + str(currentLeg), gameshotState)

        play_sound_effect(currentPlayerName, True)

        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect(
                "ambient_gameshot",
                AMBIENT_SOUNDS_AFTER_CALLS,
                volume_mult=AMBIENT_SOUNDS,
            )

        if RANDOM_CALLER_EACH_LEG:
            setup_caller()
        ppi("Gameshot")

    # Check for matchon
    elif matchon == True:
        isGameFinished = False

        reset_checkouts_counter()

        matchStarted = {
            "event": "match-started",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                "pointsStart": str(base),
                # TODO: fix
                "special": "TODO",
            },
        }
        broadcast(matchStarted)

        callPlayerNameState = play_sound_effect(currentPlayerName)
        if play_sound_effect("matchon", callPlayerNameState) == False:
            play_sound_effect("gameon", callPlayerNameState)

        if (
            AMBIENT_SOUNDS != 0.0
            and play_sound_effect(
                "ambient_matchon",
                AMBIENT_SOUNDS_AFTER_CALLS,
                volume_mult=AMBIENT_SOUNDS,
            )
            == False
        ):
            play_sound_effect(
                "ambient_gameon", AMBIENT_SOUNDS_AFTER_CALLS, volume_mult=AMBIENT_SOUNDS
            )

        ppi("Matchon")

    # Check for gameon
    elif gameon == True:
        isGameFinished = False

        reset_checkouts_counter()

        gameStarted = {
            "event": "game-started",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                "pointsStart": str(base),
                # TODO: fix
                "special": "TODO",
            },
        }
        broadcast(gameStarted)

        callPlayerNameState = play_sound_effect(currentPlayerName)
        play_sound_effect("gameon", callPlayerNameState)

        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect(
                "ambient_gameon", AMBIENT_SOUNDS_AFTER_CALLS, volume_mult=AMBIENT_SOUNDS
            )

        ppi("Gameon")

    # Check for busted turn
    elif busted == True:
        lastPoints = "B"
        isGameFinished = False

        busted = {
            "event": "busted",
            "player": currentPlayerName,
            "game": {"mode": variant},
        }
        broadcast(busted)

        play_sound_effect("busted")

        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect(
                "ambient_noscore",
                AMBIENT_SOUNDS_AFTER_CALLS,
                volume_mult=AMBIENT_SOUNDS,
            )

        ppi("Busted")

    # Check for 1. Dart
    elif turns != None and turns["throws"] != None and len(turns["throws"]) == 1:
        isGameFinished = False

    # Check for 2. Dart
    elif turns != None and turns["throws"] != None and len(turns["throws"]) == 2:
        isGameFinished = False

    # Check for 3. Dart - Score-call
    elif turns != None and turns["throws"] != None and len(turns["throws"]) == 3:
        isGameFinished = False

        dartsThrown = {
            "event": "darts-thrown",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                "pointsLeft": str(remainingPlayerScore),
                "dartNumber": "3",
                "dartValue": points,
            },
        }
        broadcast(dartsThrown)

        if remainingPlayerScore in SCHNAPSZAHLEN:
            schnapszahl = {
                "event": "schnapszahl",
                "player": currentPlayerName,
                "game": {
                    "mode": variant,
                    "pointsLeft": str(remainingPlayerScore),
                },
            }

            broadcast(schnapszahl)
            ppi(f"Schnapszahl! [{remainingPlayerScore}, {currentPlayerName}]")
            play_sound_effect("schnaps")

        play_sound_effect(points)

        if AMBIENT_SOUNDS != 0.0:
            ambient_x_success = False

            throw_combo = ""
            for t in turns["throws"]:
                throw_combo += t["segment"]["name"].lower()
            # ppi(throw_combo)

            if turns["points"] != 0:
                ambient_x_success = play_sound_effect(
                    "ambient_" + str(throw_combo),
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
                if ambient_x_success == False:
                    ambient_x_success = play_sound_effect(
                        "ambient_" + str(turns["points"]),
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )

            if ambient_x_success == False:
                if turns["points"] >= 150:
                    play_sound_effect(
                        "ambient_150more",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                elif turns["points"] >= 120:
                    play_sound_effect(
                        "ambient_120more",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                elif turns["points"] >= 100:
                    play_sound_effect(
                        "ambient_100more",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                elif turns["points"] >= 50:
                    play_sound_effect(
                        "ambient_50more",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                elif turns["points"] >= 1:
                    play_sound_effect(
                        "ambient_1more",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                else:
                    play_sound_effect(
                        "ambient_noscore",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )

            # Koordinaten der Pfeile
            coords = []
            for t in turns["throws"]:
                if "coords" in t:
                    coords.append({"x": t["coords"]["x"], "y": t["coords"]["y"]})

            # ppi(str(coords))

            # Suche das Koordinatenpaar, das am weitesten von den beiden Anderen entfernt ist

            if len(coords) > 0:
                # Liste mit allen möglichen Kombinationen von Koordinatenpaaren erstellen
                combinations = [
                    (coords[0], coords[1]),
                    (coords[0], coords[2]),
                    (coords[1], coords[2]),
                ]

                # Variablen für das ausgewählte Koordinatenpaar und die maximale Gesamtdistanz initialisieren
                selected_coord = None
                max_total_distance = 0

                # Gesamtdistanz für jede Kombination von Koordinatenpaaren berechnen
                for combination in combinations:
                    dist1 = math.sqrt(
                        (combination[0]["x"] - combination[1]["x"]) ** 2
                        + (combination[0]["y"] - combination[1]["y"]) ** 2
                    )
                    dist2 = math.sqrt(
                        (combination[1]["x"] - combination[0]["x"]) ** 2
                        + (combination[1]["y"] - combination[0]["y"]) ** 2
                    )
                    total_distance = dist1 + dist2

                    # Überprüfen, ob die Gesamtdistanz größer als die bisher größte Gesamtdistanz ist
                    if total_distance > max_total_distance:
                        max_total_distance = total_distance
                        selected_coord = combination[0]

                group_score = 100.0
                if selected_coord != None:
                    # Distanz von selected_coord zu coord2 berechnen
                    dist1 = math.sqrt(
                        (selected_coord["x"] - coords[1]["x"]) ** 2
                        + (selected_coord["y"] - coords[1]["y"]) ** 2
                    )

                    # Distanz von selected_coord zu coord3 berechnen
                    dist2 = math.sqrt(
                        (selected_coord["x"] - coords[2]["x"]) ** 2
                        + (selected_coord["y"] - coords[2]["y"]) ** 2
                    )

                    # Durchschnitt der beiden Distanzen berechnen
                    avg_dist = (dist1 + dist2) / 2

                    group_score = (1.0 - avg_dist) * 100

                # ppi("Distance by max_dis_coord to coord2: " + str(dist1))
                # ppi("Distance by max_dis_coord to coord3: " + str(dist2))
                # ppi("Group-score: " + str(group_score))

                if group_score >= 98:
                    play_sound_effect(
                        "ambient_group_legendary",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                elif group_score >= 95:
                    play_sound_effect(
                        "ambient_group_perfect",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                elif group_score >= 92:
                    play_sound_effect(
                        "ambient_group_very_nice",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                elif group_score >= 89:
                    play_sound_effect(
                        "ambient_group_good",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )
                elif group_score >= 86:
                    play_sound_effect(
                        "ambient_group_normal",
                        AMBIENT_SOUNDS_AFTER_CALLS,
                        volume_mult=AMBIENT_SOUNDS,
                    )

        ppi("Turn ended")

    mirror_sounds()
    if isGameFin == True:
        isGameFinished = True


def process_match_cricket(m):
    currentPlayerIndex = m["player"]
    currentPlayer = m["players"][currentPlayerIndex]
    currentPlayerName = str(currentPlayer["name"]).lower()
    turns = m["turns"][0]
    variant = m["variant"]

    isGameOn = False
    isGameFin = False
    global isGameFinished
    global lastPoints

    # Call every thrown dart
    if (
        CALL_EVERY_DART
        and turns != None
        and turns["throws"] != None
        and len(turns["throws"]) >= 1
    ):
        throwAmount = len(turns["throws"])
        type = turns["throws"][throwAmount - 1]["segment"]["bed"].lower()
        field_name = turns["throws"][throwAmount - 1]["segment"]["name"].lower()
        field_number = turns["throws"][throwAmount - 1]["segment"]["number"]

        if field_name == "25":
            field_name = "sbull"

        # ppi("Type: " + str(type) + " - Field-name: " + str(field_name))

        # TODO non single file
        if (
            field_number in SUPPORTED_CRICKET_FIELDS
            and play_sound_effect(field_name) == False
        ):
            inner_outer = False
            if type == "singleouter" or type == "singleinner":
                inner_outer = play_sound_effect(type)
                if inner_outer == False:
                    play_sound_effect("single")
            else:
                play_sound_effect(type)

    # Check for matchshot
    if m["winner"] != -1 and isGameFinished == False:
        isGameFin = True

        throwPoints = 0
        lastPoints = ""
        for t in turns["throws"]:
            number = t["segment"]["number"]
            if number in SUPPORTED_CRICKET_FIELDS:
                throwPoints += t["segment"]["multiplier"] * number
                lastPoints += "x" + str(t["segment"]["name"])
        lastPoints = lastPoints[1:]

        matchWon = {
            "event": "match-won",
            "player": currentPlayerName,
            "game": {"mode": variant, "dartsThrownValue": throwPoints},
        }
        broadcast(matchWon)

        if play_sound_effect("matchshot") == False:
            play_sound_effect("gameshot")
        play_sound_effect(currentPlayerName, True)
        if AMBIENT_SOUNDS != 0.0:
            if (
                play_sound_effect(
                    "ambient_matchshot",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
                == False
            ):
                play_sound_effect(
                    "ambient_gameshot",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
        setup_caller()
        ppi("Gameshot and match")

    # Check for gameshot
    elif m["gameWinner"] != -1 and isGameFinished == False:
        isGameFin = True

        throwPoints = 0
        lastPoints = ""
        for t in turns["throws"]:
            number = t["segment"]["number"]
            if number in SUPPORTED_CRICKET_FIELDS:
                throwPoints += t["segment"]["multiplier"] * number
                lastPoints += "x" + str(t["segment"]["name"])
        lastPoints = lastPoints[1:]

        gameWon = {
            "event": "game-won",
            "player": currentPlayerName,
            "game": {"mode": variant, "dartsThrownValue": throwPoints},
        }
        broadcast(gameWon)

        play_sound_effect("gameshot")
        play_sound_effect(currentPlayerName, True)
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect(
                "ambient_gameshot",
                AMBIENT_SOUNDS_AFTER_CALLS,
                volume_mult=AMBIENT_SOUNDS,
            )
        if RANDOM_CALLER_EACH_LEG:
            setup_caller()
        ppi("Gameshot")

    # Check for matchon
    elif (
        m["gameScores"][0] == 0
        and m["scores"] == None
        and turns["throws"] == None
        and m["round"] == 1
        and m["leg"] == 1
        and m["set"] == 1
    ):
        isGameOn = True
        isGameFinished = False

        matchStarted = {
            "event": "match-started",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                # TODO: fix
                "special": "TODO",
            },
        }
        broadcast(matchStarted)

        play_sound_effect(currentPlayerName, False)
        if play_sound_effect("matchon", True) == False:
            play_sound_effect("gameon", True)
        # play only if it is a real match not just legs!
        if AMBIENT_SOUNDS != 0.0 and ("legs" in m and "sets"):
            if (
                play_sound_effect(
                    "ambient_matchon",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
                == False
            ):
                play_sound_effect(
                    "ambient_gameon",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
        ppi("Matchon")

    # Check for gameon
    elif (
        m["gameScores"][0] == 0
        and m["scores"] == None
        and turns["throws"] == None
        and m["round"] == 1
    ):
        isGameOn = True
        isGameFinished = False

        gameStarted = {
            "event": "game-started",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                # TODO: fix
                "special": "TODO",
            },
        }
        broadcast(gameStarted)

        play_sound_effect(currentPlayerName, False)
        play_sound_effect("gameon", True)
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect(
                "ambient_gameon", AMBIENT_SOUNDS_AFTER_CALLS, volume_mult=AMBIENT_SOUNDS
            )
        ppi("Gameon")

    # Check for busted turn
    elif turns["busted"] == True:
        lastPoints = "B"
        isGameFinished = False
        busted = {
            "event": "busted",
            "player": currentPlayerName,
            "game": {"mode": variant},
        }
        broadcast(busted)

        play_sound_effect("busted")
        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect(
                "ambient_noscore",
                AMBIENT_SOUNDS_AFTER_CALLS,
                volume_mult=AMBIENT_SOUNDS,
            )
        ppi("Busted")

    # Check for 1. Dart
    elif turns != None and turns["throws"] != None and len(turns["throws"]) == 1:
        isGameFinished = False

    # Check for 2. Dart
    elif turns != None and turns["throws"] != None and len(turns["throws"]) == 2:
        isGameFinished = False

    # Check for 3. Dart - points call
    elif turns != None and turns["throws"] != None and len(turns["throws"]) == 3:
        isGameFinished = False

        throwPoints = 0
        lastPoints = ""
        for t in turns["throws"]:
            number = t["segment"]["number"]
            if number in SUPPORTED_CRICKET_FIELDS:
                throwPoints += t["segment"]["multiplier"] * number
                lastPoints += "x" + str(t["segment"]["name"])
        lastPoints = lastPoints[1:]

        dartsThrown = {
            "event": "darts-thrown",
            "player": currentPlayerName,
            "game": {
                "mode": variant,
                "dartNumber": "3",
                "dartValue": throwPoints,
            },
        }
        broadcast(dartsThrown)

        play_sound_effect(str(throwPoints))
        if AMBIENT_SOUNDS != 0.0:
            if throwPoints == 0:
                play_sound_effect(
                    "ambient_noscore",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
            elif throwPoints == 180:
                play_sound_effect(
                    "ambient_180",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
            elif throwPoints >= 153:
                play_sound_effect(
                    "ambient_150more",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
            elif throwPoints >= 120:
                play_sound_effect(
                    "ambient_120more",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
            elif throwPoints >= 100:
                play_sound_effect(
                    "ambient_100more",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )
            elif throwPoints >= 50:
                play_sound_effect(
                    "ambient_50more",
                    AMBIENT_SOUNDS_AFTER_CALLS,
                    volume_mult=AMBIENT_SOUNDS,
                )

        ppi("Turn ended")

    # Playerchange
    if (
        isGameOn == False
        and turns != None
        and turns["throws"] == None
        or isGameFinished == True
    ):
        dartsPulled = {
            "event": "darts-pulled",
            "player": str(currentPlayer["name"]),
            "game": {
                "mode": variant,
                # TODO: fix
                "pointsLeft": "0",
                # TODO: fix
                "dartsThrown": "3",
                "dartsThrownValue": lastPoints,
                "busted": str(turns["busted"])
                # TODO: fix
                # "darts": [
                #     {"number": "1", "value": "60"},
                #     {"number": "2", "value": "60"},
                #     {"number": "3", "value": "60"}
                # ]
            },
        }
        broadcast(dartsPulled)

        if AMBIENT_SOUNDS != 0.0:
            play_sound_effect(
                "ambient_playerchange",
                AMBIENT_SOUNDS_AFTER_CALLS,
                volume_mult=AMBIENT_SOUNDS,
            )

        ppi("Next player")

    mirror_sounds()
    if isGameFin == True:
        isGameFinished = True


def process_common(m):
    broadcast(m)


def receive_token_autodarts():
    try:
        global accessToken

        # Configure client
        keycloak_openid = KeycloakOpenID(
            server_url=AUTODART_AUTH_URL,
            client_id=AUTODART_CLIENT_ID,
            realm_name=AUTODART_REALM_NAME,
            verify=True,
        )
        token = keycloak_openid.token(AUTODART_USER_EMAIL, AUTODART_USER_PASSWORD)
        accessToken = token["access_token"]
        # ppi(token)
    except Exception as e:
        ppe("Receive token failed", e)


def connect_autodarts():
    def process(*args):
        global accessToken

        receive_token_autodarts()

        # Get Ticket
        ticket = requests.post(
            AUTODART_AUTH_TICKET_URL, headers={"Authorization": "Bearer " + accessToken}
        )
        # ppi(ticket.text)

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            AUTODART_WEBSOCKET_URL + ticket.text,
            on_open=on_open_autodarts,
            on_message=on_message_autodarts,
            on_error=on_error_autodarts,
            on_close=on_close_autodarts,
        )

        ws.run_forever()

    threading.Thread(target=process).start()


def on_open_autodarts(ws):
    try:
        global accessToken
        res = requests.get(
            AUTODART_BOARDS_URL + AUTODART_USER_BOARD_ID,
            headers={"Authorization": "Bearer " + accessToken},
        )
        # ppi(json.dumps(res.json(), indent = 4, sort_keys = True))

        match_id = res.json()["matchId"]
        if match_id != None and match_id != "":
            m = {"event": "start", "id": match_id}
            listen_to_newest_match(m, ws)

    except Exception as e:
        ppe("Fetching matches failed", e)

    try:
        ppi("Receiving live information from " + AUTODART_URL)

        # EXAMPLE:
        # const unsub = MessageBroker.getInstance().subscribe<{ id: string; event: 'start' | 'finish' | 'delete' }>(
        # 'autodarts.boards',
        # id + '.matches',

        # (msg) => {
        #     if (msg.event === 'start') {
        #     setMatchId(msg.id);
        #     } else {
        #     setMatchId(undefined);
        #     }
        # }
        # );
        paramsSubscribeMatchesEvents = {
            "channel": "autodarts.boards",
            "type": "subscribe",
            "topic": AUTODART_USER_BOARD_ID + ".matches",
        }
        ws.send(json.dumps(paramsSubscribeMatchesEvents))

    except Exception as e:
        ppe("WS-Open-boards failed: ", e)

    try:
        paramsSubscribeLobbiesEvents = {
            "channel": "autodarts.lobbies",
            "type": "subscribe",
            "topic": "*.state",
        }
        ws.send(json.dumps(paramsSubscribeLobbiesEvents))
    except Exception as e:
        ppe("WS-Open-lobbies failed: ", e)


def on_message_autodarts(ws, message):
    def process(*args):
        try:
            global lastMessage
            m = json.loads(message)

            # ppi(json.dumps(m, indent = 4, sort_keys = True))

            if m["channel"] == "autodarts.matches":
                data = m["data"]
                # ppi(json.dumps(data, indent = 4, sort_keys = True))
                global currentMatch
                # ppi('Current Match: ' + currentMatch)

                if "turns" in data and len(data["turns"]) >= 1:
                    data["turns"][0].pop("id", None)
                    data["turns"][0].pop("createdAt", None)

                if (
                    lastMessage != data
                    and currentMatch != None
                    and data["id"] == currentMatch
                ):
                    lastMessage = data

                    # ppi(json.dumps(data, indent = 4, sort_keys = True))

                    process_common(data)

                    variant = data["variant"]
                    if variant == "X01" or variant == "Random Checkout":
                        process_match_x01(data)

                    elif variant == "Cricket":
                        process_match_cricket(data)

            elif m["channel"] == "autodarts.boards":
                data = m["data"]
                # ppi(json.dumps(data, indent = 4, sort_keys = True))

                listen_to_newest_match(data, ws)

            elif m["channel"] == "autodarts.lobbies":
                data = m["data"]
                # ppi(json.dumps(data, indent = 4, sort_keys = True))

                players = data["players"]
                if players is not None:
                    for p in players:
                        if "boardId" in p and p["boardId"] == AUTODART_USER_BOARD_ID:
                            play_sound_effect("lobbychanged")
                            mirror_sounds()
                            break

        except Exception as e:
            ppe("WS-Message failed: ", e)

    threading.Thread(target=process).start()


def on_close_autodarts(ws, close_status_code, close_msg):
    try:
        ppi(
            "Websocket ["
            + str(ws.url)
            + "] closed! "
            + str(close_msg)
            + " - "
            + str(close_status_code)
        )
        ppi("Retry : %s" % time.ctime())
        time.sleep(3)
        connect_autodarts()
    except Exception as e:
        ppe("WS-Close failed: ", e)


def on_error_autodarts(ws, error):
    try:
        ppi(error)
    except Exception as e:
        ppe("WS-Error failed: ", e)


def on_open_client(client, server):
    ppi("NEW CLIENT CONNECTED: " + str(client))


def on_message_client(client, server, message):
    def process(*args):
        try:
            ppi("CLIENT MESSAGE: " + str(message))

            if message.startswith("board"):
                receive_local_board_address()

                if boardManagerAddress != None:
                    if message.startswith("board-start"):
                        msg_splitted = message.split(":")

                        wait = 0.1
                        if len(msg_splitted) > 1:
                            wait = float(msg_splitted[1])
                        if wait == 0.0:
                            wait = 0.5
                        time.sleep(wait)

                        res = requests.put(boardManagerAddress + "/api/detection/start")
                        # res = requests.put(boardManagerAddress + '/api/start')
                        # ppi(res)

                    elif message == "board-stop":
                        res = requests.put(boardManagerAddress + "/api/detection/stop")
                        # res = requests.put(boardManagerAddress + '/api/stop')
                        # ppi(res)

                    elif message == "board-reset":
                        res = requests.post(boardManagerAddress + "/api/reset")
                        # ppi(res)

                    else:
                        ppi("This message is not supported")
                else:
                    ppi("Can not change board-state as board-address is unknown!")

            elif message.startswith("correct"):
                msg_splitted = message.split(":")
                msg_splitted.pop(0)
                throw_indices = msg_splitted[:-1]
                score = msg_splitted[len(msg_splitted) - 1]
                correct_throw(throw_indices, score)

            elif message.startswith("next"):
                if message.startswith("next-game"):
                    next_game()
                else:
                    next_throw()

            elif message.startswith("undo"):
                undo_throw()

            elif message.startswith("ban"):
                msg_splitted = message.split(":")
                if len(msg_splitted) > 1:
                    ban_caller(True)
                else:
                    ban_caller(False)

            elif message.startswith("call"):
                msg_splitted = message.split(":")
                to_call = msg_splitted[1]
                call_parts = to_call.split(" ")
                for cp in call_parts:
                    play_sound_effect(cp, wait_for_last=False, volume_mult=1.0)
                mirror_sounds()

        except Exception as e:
            ppe("WS-Client-Message failed: ", e)

    t = threading.Thread(target=process).start()


def on_left_client(client, server):
    ppi("CLIENT DISCONNECTED: " + str(client))


def broadcast(data):
    def process(*args):
        global server
        server.send_message_to_all(json.dumps(data, indent=2).encode("utf-8"))

    t = threading.Thread(target=process)
    t.start()
    t.join()


def mute_audio_background(vol):
    global background_audios
    session_fails = 0
    for session in background_audios:
        try:
            volume = session.SimpleAudioVolume
            if session.Process and session.Process.name() != "autodarts-caller.exe":
                volume.SetMasterVolume(vol, None)
        # Exception as e:
        except:
            session_fails += 1
            # ppe('Failed to mute audio-process', e)

    return session_fails


def unmute_audio_background(mute_vol):
    global background_audios
    current_master = mute_vol
    steps = 0.1
    wait = 0.1
    while current_master < 1.0:
        time.sleep(wait)
        current_master += steps
        for session in background_audios:
            try:
                if session.Process and session.Process.name() != "autodarts-caller.exe":
                    volume = session.SimpleAudioVolume
                    volume.SetMasterVolume(current_master, None)
            #  Exception as e:
            except:
                continue
                # ppe('Failed to unmute audio-process', e)


def mute_background(mute_vol):
    global background_audios

    muted = False
    waitDefault = 0.1
    waitForMore = 1.0
    wait = waitDefault

    while True:
        time.sleep(wait)
        if mixer.get_busy() == True and muted == False:
            muted = True
            wait = waitForMore
            session_fails = mute_audio_background(mute_vol)

            if session_fails >= 3:
                # ppi('refreshing background audio sessions')
                background_audios = AudioUtilities.GetAllSessions()

        elif mixer.get_busy() == False and muted == True:
            muted = False
            wait = waitDefault
            unmute_audio_background(mute_vol)


@app.route("/")
def index():
    return render_template("index.html", host=WEB_HOST, ws_port=HOST_PORT, state=WEB)


@app.route("/sounds/<path:file_id>", methods=["GET"])
def sound(file_id):
    file_id = unquote(file_id)
    file_path = file_id
    if os.name == "posix":  # Unix/Linux/MacOS
        directory = "/" + os.path.dirname(file_path)
    else:  # Windows
        directory = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    return send_from_directory(directory, file_name)


@app.route("/scoreboard")
def scoreboard():
    return render_template(
        "scoreboard.html", host=WEB_HOST, ws_port=HOST_PORT, state=WEB_SCOREBOARD
    )


def start_websocket_server(host, port):
    global server
    server = WebsocketServer(host=host, port=port, loglevel=logging.ERROR)
    server.set_fn_new_client(on_open_client)
    server.set_fn_client_left(on_left_client)
    server.set_fn_message_received(on_message_client)
    server.run_forever()


def start_flask_app(host, port):
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "-U",
        "--autodarts_email",
        required=True,
        help="Registered email address at " + AUTODART_URL,
    )
    ap.add_argument(
        "-P",
        "--autodarts_password",
        required=True,
        help="Registered password address at " + AUTODART_URL,
    )
    ap.add_argument(
        "-B",
        "--autodarts_board_id",
        required=True,
        help="Registered board-id at " + AUTODART_URL,
    )
    ap.add_argument(
        "-M",
        "--media_path",
        required=True,
        help="Absolute path to your media folder. You can download free sounds at https://freesound.org/",
    )
    ap.add_argument(
        "-MS",
        "--media_path_shared",
        required=False,
        default=DEFAULT_EMPTY_PATH,
        help="Absolute path to shared media folder (every caller get sounds)",
    )
    ap.add_argument(
        "-V",
        "--caller_volume",
        type=float,
        default=1.0,
        required=False,
        help="Set the caller volume between 0.0 (silent) and 1.0 (max)",
    )
    ap.add_argument(
        "-C",
        "--caller",
        default=DEFAULT_CALLER,
        required=False,
        help="Sets a particular caller",
    )
    ap.add_argument(
        "-R",
        "--random_caller",
        type=int,
        choices=range(0, 2),
        default=0,
        required=False,
        help="If '1', the application will randomly choose a caller each game. It only works when your base-media-folder has subfolders with its files",
    )
    ap.add_argument(
        "-L",
        "--random_caller_each_leg",
        type=int,
        choices=range(0, 2),
        default=0,
        required=False,
        help="If '1', the application will randomly choose a caller each leg instead of each game. It only works when 'random_caller=1'",
    )
    ap.add_argument(
        "-RL",
        "--random_caller_language",
        type=int,
        choices=range(0, len(CALLER_LANGUAGES) + 1),
        default=DEFAULT_RANDOM_CALLER_LANGUAGE,
        required=False,
        help="If '0', the application will allow every language.., else it will limit caller selection by specific language",
    )
    ap.add_argument(
        "-RG",
        "--random_caller_gender",
        type=int,
        choices=range(0, len(CALLER_GENDERS) + 1),
        default=DEFAULT_RANDOM_CALLER_GENDER,
        required=False,
        help="If '0', the application will allow every gender.., else it will limit caller selection by specific gender",
    )
    ap.add_argument(
        "-CCP",
        "--call_current_player",
        type=int,
        choices=range(0, 2),
        default=0,
        required=False,
        help="If '1', the application will call who is the current player to throw",
    )
    ap.add_argument(
        "-E",
        "--call_every_dart",
        type=int,
        choices=range(0, 2),
        default=0,
        required=False,
        help="If '1', the application will call every thrown dart",
    )
    ap.add_argument(
        "-ESF",
        "--call_every_dart_single_files",
        type=int,
        choices=range(0, 2),
        default=1,
        required=False,
        help="If '1', the application will call a every dart by using single, dou.., else it uses two separated sounds: single + x (score)",
    )
    ap.add_argument(
        "-PCC",
        "--possible_checkout_call",
        type=int,
        default=1,
        required=False,
        help="If '1', the application will call a possible checkout starting at 170",
    )
    ap.add_argument(
        "-PCCSF",
        "--possible_checkout_call_single_files",
        type=int,
        choices=range(0, 2),
        default=0,
        required=False,
        help="If '1', the application will call a possible checkout by using yr_2-yr_170, else it uses two separated sounds: you_require + x",
    )
    ap.add_argument(
        "-PCCYO",
        "--possible_checkout_call_yourself_only",
        type=int,
        choices=range(0, 2),
        default=0,
        required=False,
        help="If '1' the caller will only call if there is a checkout possibility if the current player is you",
    )
    ap.add_argument(
        "-A",
        "--ambient_sounds",
        type=float,
        default=0.0,
        required=False,
        help="If > '0.0' (volume), the application will call a ambient_*-Sounds",
    )
    ap.add_argument(
        "-AAC",
        "--ambient_sounds_after_calls",
        type=int,
        choices=range(0, 2),
        default=0,
        required=False,
        help="If '1', the ambient sounds will appear after calling is finished",
    )
    ap.add_argument(
        "-DL",
        "--downloads",
        type=int,
        choices=range(0, 2),
        default=DEFAULT_DOWNLOADS,
        required=False,
        help="If '1', the application will try to download a curated list of caller-voices",
    )
    ap.add_argument(
        "-DLL",
        "--downloads_limit",
        type=int,
        default=DEFAULT_DOWNLOADS_LIMIT,
        required=False,
        help="If '1', the application will try to download a only the X newest caller-voices. -DLN needs to be activated.",
    )
    ap.add_argument(
        "-DLLA",
        "--downloads_language",
        type=int,
        choices=range(0, len(CALLER_LANGUAGES) + 1),
        default=DEFAULT_DOWNLOADS_LANGUAGE,
        required=False,
        help="If '0', the application will download speakers of every language.., else it will limit speaker downloads by specific language",
    )
    ap.add_argument(
        "-DLP",
        "--downloads_path",
        required=False,
        default=DEFAULT_DOWNLOADS_PATH,
        help="Absolute path for temporarly downloads",
    )
    ap.add_argument(
        "-BAV",
        "--background_audio_volume",
        required=False,
        type=float,
        default=0.0,
        help="Set background-audio-volume between 0.1 (silent) and 1.0 (no mute)",
    )
    ap.add_argument(
        "-WEB",
        "--web_caller",
        required=False,
        type=int,
        choices=range(0, 3),
        default=0,
        help="If '1' the application will host an web-endpoint, '2' it will do '1' and default caller-functionality.",
    )
    ap.add_argument(
        "-WEBSB",
        "--web_caller_scoreboard",
        required=False,
        type=int,
        choices=range(0, 2),
        default=0,
        help="If '1' the application will host an web-endpoint, right to web-caller-functionality.",
    )
    ap.add_argument(
        "-WEBP",
        "--web_caller_port",
        required=False,
        type=int,
        default=DEFAULT_WEB_CALLER_PORT,
        help="Web-Caller-Port",
    )
    ap.add_argument(
        "-HP",
        "--host_port",
        required=False,
        type=int,
        default=DEFAULT_HOST_PORT,
        help="Host-Port",
    )
    ap.add_argument(
        "-DEB",
        "--debug",
        type=int,
        choices=range(0, 2),
        default=False,
        required=False,
        help="If '1', the application will output additional information",
    )
    ap.add_argument(
        "-CC",
        "--cert_check",
        type=int,
        choices=range(0, 2),
        default=True,
        required=False,
        help="If '0', the application won't check any ssl certification",
    )
    ap.add_argument(
        "-MIF",
        "--mixer_frequency",
        type=int,
        required=False,
        default=DEFAULT_MIXER_FREQUENCY,
        help="Pygame mixer frequency",
    )
    ap.add_argument(
        "-MIS",
        "--mixer_size",
        type=int,
        required=False,
        default=DEFAULT_MIXER_SIZE,
        help="Pygame mixer size",
    )
    ap.add_argument(
        "-MIC",
        "--mixer_channels",
        type=int,
        required=False,
        default=DEFAULT_MIXER_CHANNELS,
        help="Pygame mixer channels",
    )
    ap.add_argument(
        "-MIB",
        "--mixer_buffersize",
        type=int,
        required=False,
        default=DEFAULT_MIXER_BUFFERSIZE,
        help="Pygame mixer buffersize",
    )

    args = vars(ap.parse_args())

    AUTODART_USER_EMAIL = args["autodarts_email"]
    AUTODART_USER_PASSWORD = args["autodarts_password"]
    AUTODART_USER_BOARD_ID = args["autodarts_board_id"]
    AUDIO_MEDIA_PATH = Path(args["media_path"])
    if args["media_path_shared"] != DEFAULT_EMPTY_PATH:
        AUDIO_MEDIA_PATH_SHARED = Path(args["media_path_shared"])
    else:
        AUDIO_MEDIA_PATH_SHARED = DEFAULT_EMPTY_PATH
    AUDIO_CALLER_VOLUME = args["caller_volume"]
    CALLER = args["caller"]
    RANDOM_CALLER = args["random_caller"]
    RANDOM_CALLER_EACH_LEG = args["random_caller_each_leg"]
    RANDOM_CALLER_LANGUAGE = args["random_caller_language"]
    if RANDOM_CALLER_LANGUAGE < 0:
        RANDOM_CALLER_LANGUAGE = DEFAULT_RANDOM_CALLER_LANGUAGE
    RANDOM_CALLER_GENDER = args["random_caller_gender"]
    if RANDOM_CALLER_GENDER < 0:
        RANDOM_CALLER_GENDER = DEFAULT_RANDOM_CALLER_GENDER
    CALL_CURRENT_PLAYER = args["call_current_player"]
    CALL_EVERY_DART = args["call_every_dart"]
    CALL_EVERY_DART_SINGLE_FILE = args["call_every_dart_single_files"]
    POSSIBLE_CHECKOUT_CALL = args["possible_checkout_call"]
    if POSSIBLE_CHECKOUT_CALL < 0:
        POSSIBLE_CHECKOUT_CALL = 0
    POSSIBLE_CHECKOUT_CALL_SINGLE_FILE = args["possible_checkout_call_single_files"]
    POSSIBLE_CHECKOUT_CALL_YOURSELF_ONLY = args["possible_checkout_call_yourself_only"]
    AMBIENT_SOUNDS = args["ambient_sounds"]
    AMBIENT_SOUNDS_AFTER_CALLS = args["ambient_sounds_after_calls"]
    DOWNLOADS = args["downloads"]
    DOWNLOADS_LANGUAGE = args["downloads_language"]
    if DOWNLOADS_LANGUAGE < 0:
        DOWNLOADS_LANGUAGE = DEFAULT_DOWNLOADS_LANGUAGE
    DOWNLOADS_LIMIT = args["downloads_limit"]
    if DOWNLOADS_LIMIT < 0:
        DOWNLOADS_LIMIT = DEFAULT_DOWNLOADS_LIMIT
    DOWNLOADS_PATH = args["downloads_path"]
    BACKGROUND_AUDIO_VOLUME = args["background_audio_volume"]
    WEB = args["web_caller"]
    WEB_SCOREBOARD = args["web_caller_scoreboard"]
    WEB_PORT = args["web_caller_port"]
    HOST_PORT = args["host_port"]
    DEBUG = args["debug"]
    CERT_CHECK = args["cert_check"]
    MIXER_FREQUENCY = args["mixer_frequency"]
    MIXER_SIZE = args["mixer_size"]
    MIXER_CHANNELS = args["mixer_channels"]
    MIXER_BUFFERSIZE = args["mixer_buffersize"]

    if DEBUG:
        ppi("Started with following arguments:")
        data_to_mask = {
            "autodarts_email": "email",
            "autodarts_password": "str",
            "autodarts_board_id": "str",
        }
        masked_args = mask(args, data_to_mask)
        ppi(json.dumps(masked_args, indent=4))

    args_post_check = None
    try:
        if os.path.commonpath([AUDIO_MEDIA_PATH, main_directory]) == main_directory:
            args_post_check = (
                "AUDIO_MEDIA_PATH resides inside MAIN-DIRECTORY! It is not allowed!"
            )
        if AUDIO_MEDIA_PATH_SHARED != DEFAULT_EMPTY_PATH:
            if (
                os.path.commonpath([AUDIO_MEDIA_PATH_SHARED, main_directory])
                == main_directory
            ):
                args_post_check = "AUDIO_MEDIA_PATH_SHARED resides inside MAIN-DIRECTORY! It is not allowed!"
            elif (
                os.path.commonpath([AUDIO_MEDIA_PATH_SHARED, AUDIO_MEDIA_PATH])
                == AUDIO_MEDIA_PATH
            ):
                args_post_check = "AUDIO_MEDIA_PATH_SHARED resides inside AUDIO_MEDIA_PATH! It is not allowed!"
            elif (
                os.path.commonpath([AUDIO_MEDIA_PATH, AUDIO_MEDIA_PATH_SHARED])
                == AUDIO_MEDIA_PATH_SHARED
            ):
                args_post_check = "AUDIO_MEDIA_PATH resides inside AUDIO_MEDIA_SHARED! It is not allowed!"
            elif AUDIO_MEDIA_PATH == AUDIO_MEDIA_PATH_SHARED:
                args_post_check = "AUDIO_MEDIA_PATH is equal to AUDIO_MEDIA_SHARED! It is not allowed!"
    except:
        pass

    global server
    server = None

    global accessToken
    accessToken = None

    global boardManagerAddress
    boardManagerAddress = None

    global lastMessage
    lastMessage = None

    global lastCorrectThrow
    lastCorrectThrow = None

    global currentMatch
    currentMatch = None

    global caller
    caller = None

    global caller_title
    caller_title = ""

    global caller_profiles_banned
    caller_profiles_banned = []

    global lastPoints
    lastPoints = None

    global isGameFinished
    isGameFinished = False

    global background_audios
    background_audios = None

    global mirror_files
    mirror_files = []

    global checkoutsCounter
    checkoutsCounter = {}

    # Initialize sound-mixer
    mixer.pre_init(MIXER_FREQUENCY, MIXER_SIZE, MIXER_CHANNELS, MIXER_BUFFERSIZE)
    mixer.init()

    osType = plat
    osName = os.name
    osRelease = platform.release()
    ppi("\r\n", None, "")
    ppi("##########################################", None, "")
    ppi("       WELCOME TO AUTODARTS-CALLER", None, "")
    ppi("##########################################", None, "")
    ppi("VERSION: " + VERSION, None, "")
    ppi("RUNNING OS: " + osType + " | " + osName + " | " + osRelease, None, "")
    ppi(
        "SUPPORTED GAME-VARIANTS: " + " ".join(str(x) for x in SUPPORTED_GAME_VARIANTS),
        None,
        "",
    )
    ppi("\r\n", None, "")

    if CERT_CHECK:
        ssl._create_default_https_context = ssl.create_default_context
    else:
        ppi("WARNING: SSL-cert-verification disabled!")
        ssl._create_default_https_context = ssl._create_unverified_context
        os.environ["PYTHONHTTPSVERIFY"] = "0"

    if args_post_check is not None:
        ppi("Please check your arguments: " + args_post_check)

    else:
        if plat == "Windows" and BACKGROUND_AUDIO_VOLUME > 0.0:
            try:
                background_audios = AudioUtilities.GetAllSessions()
                audio_muter = threading.Thread(
                    target=mute_background, args=[BACKGROUND_AUDIO_VOLUME]
                )
                audio_muter.start()
            except Exception as e:
                ppe("Background-muter failed!", e)

        try:
            load_callers_banned()
            download_callers()
        except Exception as e:
            ppe("Caller-profile fetching failed!", e)

        try:
            setup_caller()
        except Exception as e:
            ppe("Setup callers failed!", e)

        if caller == None:
            ppi(
                'A caller with name "'
                + str(CALLER)
                + '" does NOT exist! Please compare your input with list of available callers.'
            )
        else:
            try:
                websocket_server_thread = threading.Thread(
                    target=start_websocket_server, args=(DEFAULT_HOST_IP, HOST_PORT)
                )
                websocket_server_thread.start()

                if WEB > 0 or WEB_SCOREBOARD:
                    WEB_HOST = get_local_ip_address()
                    flask_app_thread = threading.Thread(
                        target=start_flask_app, args=(DEFAULT_HOST_IP, WEB_PORT)
                    )
                    flask_app_thread.start()

                connect_autodarts()

                websocket_server_thread.join()

                if WEB > 0 or WEB_SCOREBOARD:
                    flask_app_thread.join()

            except Exception as e:
                ppe("Connect failed: ", e)


time.sleep(30)
