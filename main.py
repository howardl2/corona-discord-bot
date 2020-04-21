import requests
import os
import datetime
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from discord import Game
from discord.ext import commands

from state_abr import states

# reverse map states
states_full = { v: k for k, v in states.items() }
CORONA_URL = "https://covidtracking.com/api"
STATE_EXTENSION = "/states/daily"
US_EXTENSION = "/us/daily"
IMG_DIR = "img/"

BOT_PREFIX = ("!!")

with open("token", "r") as readToken:
    TOKEN = readToken.read().strip()

client = commands.Bot(command_prefix=BOT_PREFIX, description="Answers how many cases of COVID-19 there are in the US")


@client.command(name="corona",
                brief="Tells you if you'll die",
                aliases=["coronavirus", "virus", "corona_virus", "covid", "covid-19"],
                pass_context=True)
async def corona_virus(ctx, *args):
    args = [a.upper() for a in args]
    if not args or "US" in args or "UNITED STATES" in args or "AMERICA" in args or (len(args) == 1 and ("PLOT" in args or "GRAPH" in args)):
        try:
            result = requests.get(CORONA_URL+US_EXTENSION).json()
        except Exception:
            await client.say("Couldn't get the Corona data =(")
            return

        try:
            res = result[0]["positive"]
            await client.say("There are {} positive cases in the US =(".format(res))
        except Exception as e:
            print(e)
            await client.say("Something went wrong =(")
        
        if "GRAPH" in args or "PLOT" in args:
            graph_stats(result, "united_states")
            await client.send_file(ctx.message.channel, IMG_DIR + "united_states.png")
            os.remove(IMG_DIR + "united_states.png")
        return

    state = args[0]
    st = ""
    if state.upper() in states:
        st = state.upper()
    elif state in states_full:
        st = states_full[state]
    else:
        await client.say("I don't recognize that =(")
        return

    # just query the api
    try:
        result = requests.get(CORONA_URL + STATE_EXTENSION + "?state=" + st).json()
    except Exception:
        await client.say("Couldn't get the Corona data =(")
        return
    
    if not len(result):
        await client.say("Couldn't get the Corona data =(")
        return

    loc = states[state] if state in states else state
    total = result[0]["positive"]
    await client.say("There are {} positive cases in {} =(".format(total, loc.upper()))
    if "GRAPH" in args or "PLOT" in args:
        graph_stats(result, loc)
        await client.send_file(ctx.message.channel, IMG_DIR + loc + ".png")
        os.remove(IMG_DIR + loc + ".png")


def graph_stats(data, location):
    '''
        Plot the data and return the graph itself
    '''
    d = sorted(data, key=lambda x: x["date"])
    for e in d:
        e["dateChecked"] = e["dateChecked"][:10]

    df = pd.json_normalize(d)

    # collect the moving average
    total_positive_avgs = gather_moving_avg(df["positive"])
    newcase_avgs = gather_moving_avg(df["positiveIncrease"])

    plt.plot(total_positive_avgs, newcase_avgs, color="blue", marker="o", linestyle="--")
    plt.xlabel("Total Positive")
    plt.ylabel("Positive Increase")
    plt.title("Logarithmic Covid Growth Rate")
    plt.grid(True)
    plt.xscale("log")
    plt.yscale("log")
    plt.savefig(IMG_DIR + location + ".png")
    plt.clf()

def gather_moving_avg(data):
    '''
        Given a list, return a smaller list of the grouped moving average specified by `days`
        Note: if the len(data) % days != 0, it will average whatever remains
    '''
    days = 7
    avgs = []
    queue = []
    for num in data:
        if len(queue) == days-1:
            # average
            val1, val2 = queue.pop(), queue.pop()
            avg = sum([val1, val2, num]) / days
            avgs.append(avg)
        else:
            queue.append(num)
    # average the remaining
    if queue:
        avgs.append(sum(queue) / len(queue))

    return avgs

@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")


async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)

client.loop.create_task(list_servers())
client.run(TOKEN)

# result = requests.get(CORONA_URL+US_EXTENSION).json()
# print(graph_stats(result, "united_states"))
