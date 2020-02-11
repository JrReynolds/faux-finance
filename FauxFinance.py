import os
import discord
import json
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('AUTH')

MESSAGE_SAVE_COUNT = 10
STOCK_UPDATE_COUNT = 5

WORK_XP_MULT = 0.2
WORK_MONEY_MULT = 2

WORK_COOLDOWN_TIME = 300  # in seconds

STOCK_INIT_VAL = 1000

UsersDirectory = {}
Counters = {'save': 0, 'update-stocks': 0}
MainStocks = {}

# Be sure to use in try|except context!
def CreateUser(name, funds, xp, stocks):
    assert type(name) == str, "Name in CreateUser must be type str."
    assert type(funds) in [int, float], "Funds in CreateUser must be numeric."
    assert type(xp) in [int, float], "XP in CreateUser must be numeric."
    assert type(stocks) == dict, "Stocks in CreateUser must be type dict."

    UsersDirectory.update({name: {'funds': funds, 'xp': xp, 'stocks': stocks}})

# loads both the most recently saved stock prices and most recently saved user directory.
def load():
    try:
        book = open('book.json', 'r')   # load users
    except Exception as e:
        print(f'Error in loading book.json, {e}')
        return
    jsonobj = json.load(book)
    UsersDirectory.update(jsonobj)
    book.close()
    print('Loaded Profiles!')
    try:
        stocklist = open('stocks.json', 'r')  # load stocks from last save point
    except Exception as e:
        print(f'Error in loading stocks.json, {e}')
        return
    MainStocks.update(json.load(stocklist))
    stocklist.close()
    print('Stocks Initialized!')


def save():
    try:
        book = open('book.json', 'w')
    except Exception as e:
        print(f'Error in loading book.json, {e}')
        return
    json.dump(UsersDirectory, book)
    book.close()
    try:
        stocks = open('stocks.json', 'w')
    except Exception as e:
        print(f'Error in loading stocks.json, {e}')
        return
    json.dump(MainStocks, stocks)
    stocks.close()
    print('Saved!')

############################
# DISCORD STUFF DOWN HERE! #
############################
# --------------------------------------------------------------------------------------------------------------------
bot = commands.Bot(command_prefix='%')


@bot.event
async def on_ready():
    print(f'logged in as {bot.user.display_name}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'Command on cooldown, please wait {error.retry_after:.0f} seconds.')
    if isinstance(error, NameError):
        await ctx.send(NameError)
    else:
        print(error)


@bot.event
async def on_message(message):
    if message.author == bot:
        return
    else:
        e = message.content.split()
        for word in e:
            if word in MainStocks:
                MainStocks.update({word: MainStocks[word] + 1})

        Counters.update({'save': Counters['save'] + 1})
        Counters.update({'update-stocks': Counters['update-stocks'] + 1})
        # Saves based on how many messages have been sent.
        if Counters['save'] >= MESSAGE_SAVE_COUNT:
            save()
            Counters.update({'save': 0})
        # Updates stocks based on how many messages have been sent.
        if Counters['update-stocks'] >= STOCK_UPDATE_COUNT:
            print(MainStocks)
            Counters.update({'update-stocks': 0})


@commands.cooldown(1, WORK_COOLDOWN_TIME, commands.BucketType.user)
@bot.command()
async def work(ctx):
    if str(ctx.message.author.id) in UsersDirectory:
        user = UsersDirectory[str(ctx.message.author.id)]
        newMoney = (WORK_MONEY_MULT * user['xp'])
        newXP = (1 * WORK_XP_MULT * newMoney)
        user.update({'funds': user['funds'] + newMoney})
        user.update({'xp': user['xp'] + newXP})

        await ctx.send(f'Worked! Gained {newMoney} Money and {newXP} XP!\nCurrent funds: {user["funds"]}\tCurrent XP: {user["xp"]}')

    else:
        raise NameError(f'User ({ctx.message.author.nick}) does not have an account!')


@bot.command(aliases=['open-account'])
async def _init_user(ctx):
    if str(ctx.message.author.id) in UsersDirectory:
        await ctx.send(f'{ctx.message.author.nick} already has an open account!')
    else:
        try:
            CreateUser(str(ctx.message.author.id), 0.00, 1, {})
        except Exception as e:
            print(e)
        await ctx.send(f'Account opened!')


@bot.command()
async def shutdown(ctx):
    if ctx.message.author.id == 120052885319974912:
        save()
        await bot.close()
    else:
        print("Unauthorized User attempted to shut down!")

load()
save()
bot.run(TOKEN)
