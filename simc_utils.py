import os
import sys
import subprocess
import aiohttp
import asyncio
import time
import json
import re
from urllib.parse import quote

#
# A utils file for simc that is not dependent on Discord
# For testing functionality
#

## Returns the role of the character, e.g. 'DPS'
async def check_role(region, realm, char, api_key):
    url = "https://%s.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_US&apikey=%s" % (region, realm,
                                                                                                   quote(char), api_key)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if 'reason' in data:
                return data['reason']
            else:
                spec = 0
                for i in range(len(data['talents'])):
                    for line in data['talents']:
                        if 'selected' in line:
                            role = data['talents'][spec]['spec']['role']
                            return role
                        else:
                            spec += +1

## Returns the gear of the character as given by the blizzard api
async def check_gear(region, realm, char, api_key):
    url = "https://%s.api.battle.net/wow/character/%s/%s?fields=items&locale=en_US&apikey=%s" % (region, realm,
                                                                                                   quote(char), api_key)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data

## Return sim for the character, but without html report. Differences from main sim function:
##removed 'message' argument
##added 'threads' argument
##added 'process_priority' argument
##added executable
async def sim_nohtml(realm, char, scale, data, addon, region, iterations, fightstyle, enemy, length, l_fixed,
              api_key, threads, process_priority, executable):
    loop = True
    scale_stats = 'agility,strength,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating'
    options = 'calculate_scale_factors=%s scale_only=%s threads=%s iterations=%s ' \
              'fight_style=%s enemy=%s apikey=%s process_priority=%s max_time=%s' % (scale, scale_stats, threads, iterations,
                                                                                     fightstyle, enemy, api_key,
                                                                                     process_priority, length)
    if data == 'addon':
        options += ' input=%s' % addon
    else:
        options += ' armory=%s,%s,%s' % (region, realm, char)

    if l_fixed == 1:
        options += ' vary_combat_length=0.0 fixed_time=1'

    command_inner = "%s %s" % (executable, options)
    proc = subprocess.Popen(command_inner.split(" "), stdout=subprocess.PIPE)
    result_str = proc.stdout.read().decode() #decodes as ascii
    proc.terminate()
    return result_str

#Trims the report to only include the player information and their DPS
def trim_report_string(result_str):
    playerLine = re.search('Player:.*\n',result_str).group()
    dps = re.search('DPS:.*\n', result_str).group()
    return (playerLine + dps)
