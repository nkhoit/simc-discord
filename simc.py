import os
import sys
import subprocess
import discord
import aiohttp
import asyncio
import time
import json
from urllib.parse import quote

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('user_data.json') as data_file:
    user_opt = json.load(data_file)

bot = discord.Client()
simc_opts = user_opt['simcraft_opt'][0]
server_opts = user_opt['server_opt'][0]
threads = os.cpu_count()
if 'threads' in simc_opts:
    threads = simc_opts['threads']
process_priority = 'below_normal'
if 'process_priority' in simc_opts:
    process_priority = simc_opts['process_priority']
htmldir = simc_opts['htmldir']
website = simc_opts['website']
os.makedirs(os.path.dirname(os.path.join(htmldir + 'debug', 'test.file')), exist_ok=True)


def check_simc():
    null = open(os.devnull, 'w')
    stdout = open(os.path.join(htmldir, 'debug', 'simc.ver'), "w")
    subprocess.Popen(simc_opts['executable'], universal_newlines=True, stderr=null, stdout=stdout)
    time.sleep(1)
    readversion = open(os.path.join(htmldir, 'debug', 'simc.ver'), 'r')
    return readversion.readline().rstrip('\n')


async def check_spec(region, realm, char, api_key):
    url = "https://%s.api.battle.net/wow/character/%s/%s?fields=talents&locale=en_GB&apikey=%s" % (region, realm,
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


async def sim(realm, char, scale, filename, data, addon, region, iterations, fightstyle, enemy, length, l_fixed,
              api_key, message):
    loop = True
    scale_stats = 'agility,strength,intellect,crit_rating,haste_rating,mastery_rating,versatility_rating'
    options = 'calculate_scale_factors=%s scale_only=%s html=%ssims/%s/%s.html threads=%s iterations=%s ' \
              'fight_style=%s enemy=%s apikey=%s process_priority=%s max_time=%s' % (scale, scale_stats, htmldir, char,
                                                                                     filename, threads, iterations,
                                                                                     fightstyle, enemy, api_key,
                                                                                     process_priority, length)
    if data == 'addon':
        options += ' input=%s' % addon
    else:
        options += ' armory=%s,%s,%s' % (region, realm, char)

    if l_fixed == 1:
        options += ' vary_combat_length=0.0 fixed_time=1'

    load = await bot.send_message(message.channel, 'Simulating: Starting...')
    command = "%s %s" % (simc_opts['executable'], options)
    stout = open(os.path.join(htmldir, 'debug', 'simc.stout'), "w")
    sterr = open(os.path.join(htmldir, 'debug', 'simc.sterr'), "w")
    process = subprocess.Popen(command.split(" "), universal_newlines=True, stdout=stout, stderr=sterr)
    await asyncio.sleep(1)
    while loop:
        readstout = open(os.path.join(htmldir, 'debug', 'simc.stout'), "r")
        readsterr = open(os.path.join(htmldir, 'debug', 'simc.sterr'), "r")
        await asyncio.sleep(1)
        process_check = readstout.readlines()
        err_check = readsterr.readlines()
        if len(err_check) > 0:
            if 'ERROR' in err_check[-1]:
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Sim: Ready'))
                await bot.edit_message(load, 'Error, something went wrong: ' + website + 'debug/simc.sterr')
                process.terminate()
                return
        if len(process_check) > 1:
            if 'report took' in process_check[-2]:
                loop = False
                link = 'Simulation: %ssims/%s/%s.html' % (website, char, filename)
                await bot.change_presence(status=discord.Status.online, game=discord.Game(name='Sim: Ready'))
                await bot.edit_message(load, link + ' {0.author.mention}'.format(message))
                process.terminate()
            else:
                if 'Generating' in process_check[-1]:
                    done = '█' * (20 - process_check[-1].count('.'))
                    missing = '░' * (process_check[-1].count('.'))
                    progressbar = done + missing
                    procent = 100 - process_check[-1].count('.') * 5
                    load = await bot.edit_message(load, process_check[-1].split()[1] + ' ' + progressbar + ' ' +
                                                  str(procent) + '%')


def check(addon_data):
    return addon_data.content.endswith('DONE')


@bot.event
async def on_message(message):
    server = bot.get_server(server_opts['serverid'])
    channel = bot.get_channel(server_opts['channelid'])
    api_key = simc_opts['api_key']
    realm = simc_opts['default_realm']
    region = simc_opts['region']
    iterations = simc_opts['default_iterations']
    timestr = time.strftime("%Y%m%d-%H%M%S")
    scale = 0
    scaling = 'no'
    data = 'armory'
    char = ''
    addon = ''
    aoe = 'no'
    enemy = ''
    fightstyle = simc_opts['fightstyles'][0]
    movements = ''
    length = simc_opts['length']
    l_fixed = 0
    args = message.content.lower()

    if message.author == bot.user:
        return
    elif args.startswith('!simc'):
        args = args.split('-')
        if args:
            if args[1].startswith(('h', 'help')):
                msg = open('help.file', 'r', encoding='utf8').read()
                await bot.send_message(message.author, msg)
            elif args[1].startswith(('v', 'version')):
                await bot.send_message(message.channel, check_simc())
            else:
                if message.channel != channel:
                    await bot.send_message(message.channel, 'Please use the correct channel.')
                    return
                for i in range(len(args)):
                    if args[i] != '!simc ':
                        if args[i].startswith(('r ', 'realm ')):
                            temp = args[i].split()
                            realm = temp[1]
                        elif args[i].startswith(('c ', 'char ', 'character ')):
                            temp = args[i].split()
                            char = temp[1]
                        elif args[i].startswith(('s ', 'scaling ')):
                            temp = args[i].split()
                            scaling = temp[1]
                        elif args[i].startswith(('d ', 'data ')):
                            temp = args[i].split()
                            data = temp[1]
                        elif args[i].startswith(('i ', 'iterations ')):
                            if simc_opts['allow_iteration_parameter']:
                                temp = args[i].split()
                                iterations = temp[1]
                            else:
                                await bot.send_message(message.channel, 'Custom iterations is disabled')
                                return
                        elif args[i].startswith(('f ', 'fight ', 'fightstyle ')):
                            fstyle = False
                            temp = args[i].split()
                            for opt in range(len(simc_opts['fightstyles'])):
                                if temp[1] == simc_opts['fightstyles'][opt].lower():
                                    fightstyle = temp[1]
                                    fstyle = True
                            if fstyle is not True:
                                await bot.send_message(message.channel, 'Unknown fightstyle.\nSupported Styles: ' +
                                                       ', '.join(simc_opts['fightstyles']))
                                return
                        elif args[i].startswith(('a ', 'aoe ')):
                            temp = args[i].split()
                            aoe = temp[1]
                        elif args[i].startswith(('l ', 'length ')):
                            temp = args[i].split()
                            length = temp[1]
                            if len(temp) > 2:
                                if temp[2] == 'fixed':
                                    l_fixed = 1
                        else:
                            await bot.send_message(message.channel, 'Unknown command. Use !simc -h/help for commands')
                            return
                if server.me.status != discord.Status.online:
                    err_msg = 'Only one simulation can run at the same time.'
                    await bot.send_message(message.channel, err_msg)
                    return
                else:
                    if char == '':
                        await bot.send_message(message.channel, 'Character name is needed')
                        return
                    if scaling == 'yes':
                        scale = 1
                    if aoe == 'yes':
                        for targets in range(0, simc_opts['aoe_targets']):
                            targets += + 1
                            enemy += 'enemy=target%s ' % targets

                    os.makedirs(os.path.dirname(os.path.join(htmldir + 'sims', char, 'test.file')), exist_ok=True)
                    if data == 'addon':
                        await bot.change_presence(status=discord.Status.idle, game=discord.Game(name='Sim: Waiting...'))
                        msg = 'Please paste the output of your simulationcraft addon here and finish with DONE'
                        await bot.send_message(message.author, msg)
                        addon_data = await bot.wait_for_message(author=message.author, check=check, timeout=60)
                        if addon_data is None:
                            await bot.send_message(message.channel, 'No data given. Resetting session.')
                            await bot.change_presence(status=discord.Status.online,
                                                      game=discord.Game(name='Sim: Ready'))
                            return
                        else:
                            healing_roles = ['restoration', 'holy', 'discipline', 'mistweaver']
                            addon = '%ssims/%s/%s-%s.simc' % (htmldir, char, char, timestr)
                            f = open(addon, 'w')
                            f.write(addon_data.content[:-4])
                            f.close()
                            for crole in healing_roles:
                                crole = 'spec=' + crole
                                if crole in addon_data.content:
                                    await bot.send_message(message.channel,
                                                           'SimulationCraft does not support healing.')
                                    await bot.change_presence(status=discord.Status.online,
                                                              game=discord.Game(name='Sim: Ready'))
                                    return

                    if data != 'addon':
                        api = await check_spec(region, realm, char, api_key)
                        if api == 'HEALING':
                            await bot.send_message(message.channel, 'SimulationCraft does not support healing.')
                            return
                        elif not api == 'DPS' and not api == 'TANK':
                            msg = 'Something went wrong: %s' % (api)
                            await bot.send_message(message.channel, msg)
                            return
                    for item in simc_opts['fightstyles']:
                        if item.lower() == fightstyle.lower():
                            movements = movements + '**__' + item + '__**, '
                        else:
                            movements = movements + item + ', '
                    await bot.change_presence(status=discord.Status.dnd, game=discord.Game(name='Sim: In Progress'))
                    msg = '\nSimulationCraft:\nRealm: %s\nCharacter: %s\nFightstyle: %s\nFight Length: %s\nAoE: %s\n' \
                          'Iterations: %s\nScaling: %s\nData: %s' % (realm.capitalize(), char.capitalize(), movements,
                                                                     length, aoe.capitalize(), iterations,
                                                                     scaling.capitalize(), data.capitalize())
                    filename = '%s-%s' % (char, timestr)
                    await bot.send_message(message.channel, msg)
                    bot.loop.create_task(sim(realm, char, scale, filename, data, addon, region, iterations, fightstyle,
                                             enemy, length, l_fixed, api_key, message))


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(check_simc())
    print('--------------')
    await bot.change_presence(game=discord.Game(name='Simulation: Ready'))


bot.run(server_opts['token'])
