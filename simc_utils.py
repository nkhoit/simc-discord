import os
import sys
import subprocess
import aiohttp
import asyncio
import time
import json
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

