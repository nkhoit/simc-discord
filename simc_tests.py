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

async def test_sim_api():
	os.chdir(os.path.dirname(os.path.abspath(__file__)))
	with open('user_data.json') as data_file:
		user_opt = json.load(data_file)
	simc_opts = user_opt['simcraft_opt'][0]
	api_key = simc_opts['api_key']
	realm = simc_opts['default_realm']
	region = simc_opts['region']
	iterations = simc_opts['default_iterations']
	timestr = time.strftime("%Y%m%d-%H%M%S")
	scale = 0
	scaling = 'no'
	data = 'armory'
	char = 'Splaytree'
	addon = ''
	aoe = 'no'
	enemy = ''
	fightstyle = simc_opts['fightstyles'][0]
	movements = ''
	length = simc_opts['length']
	l_fixed = 0
	threads = os.cpu_count()
	if 'threads' in simc_opts:
		threads = simc_opts['threads']
		process_priority = 'below_normal'
	if 'process_priority' in simc_opts:
		process_priority = simc_opts['process_priority']
	executable = simc_opts['executable']
	simresult = await sim_nohtml(realm, char, scale, data, 
    	addon, region, iterations, fightstyle, enemy, length, 
    	l_fixed, api_key, threads, process_priority, executable)
	print(trim_report_string(simresult))


#async io loop
loop = asyncio.get_event_loop()
loop.run_until_complete(test_role_api())
loop.run_until_complete(test_gear_api())
loop.run_until_complete(test_sim_api())
loop.close()
