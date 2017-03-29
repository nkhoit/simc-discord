from simc_utils import *
import os
import sys
import asyncio


#A lot of these user settings don't make sense for a test file since it's about discord & stuff
#But we do need to grab the api key or we can't make calls to blizzard api
os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('user_data.json') as data_file:
    user_opt = json.load(data_file)
simc_opts = user_opt['simcraft_opt'][0]
api_key = simc_opts['api_key']


region = 'us'
realm = 'Haomarush'
char = 'Splaytree'

##
## TODO: make these actual tests instead of just printing things
##
async def test_role_api():
	role = await check_role(region, realm, char, api_key)
	print('Should be DPS: %s' % role)
	return role

async def test_gear_api():
	gear = await check_gear(region, realm, char, api_key)
	items = gear['items']
	for i in items.keys():
		#special cases...
		if (i == 'averageItemLevel' or i == 'averageItemLevelEquipped'):
			continue
		print("%s: %s" % (i, items[i]['name']))
	return gear


#async io loop
loop = asyncio.get_event_loop()
loop.run_until_complete(test_role_api())
loop.run_until_complete(test_gear_api())
loop.close()

