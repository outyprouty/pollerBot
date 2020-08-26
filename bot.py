# bot.py
import os

from discord.ext import commands
from dotenv import load_dotenv
import discord

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
WRITE_ID = int(os.getenv('WRITE_POLL'))
ANS_ID = int(os.getenv('ANS_POLL'))

class Poll:

    reactions = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']
    
    def __init__(self, question, options):
        self.cancelCtr = 0

        #This should be a string question in "
        self.question = question

        #This should be a string in "
        self.options = options

        #This is auto-generated list of results, one per option tuple
        self.results = [0]*len(options)

        #This is status of poll, true - open, false - closed
        self.open = False

        #List of users who have responded already
        self.responded = []

    def setID(self, msgID):
        self.id = msgID
        self.open = True

    def getID(self):
        return self.id

    def getPollString(self):
        s = ""
        s += self.question
        s += "\n"
        s += '-'*50
        s += "\n"
        for i in range(len(self.options)):
            s += "%s -- %s"%(Poll.reactions[i], self.options[i])
            s += "\n"
        s += '-'*50
        return s

    def addVote(self, emoji, user):
        if emoji == cancelEmoji:
            self.cancelCtr ++
        if self.open:
            if user in self.responded:
                return -1, "Already responded"
            try:
                voteIndex = Poll.reactions.index(emoji)
            except ValueError as err:
                print(err)
                return -1, "Wrong emoji Used!"
            self.results[voteIndex] += 1
            self.responded.append(user)
            return 0
        else:
            return -1, "Poll Closed"
    
    def getResults(self):
        s = "Results for poll ID #%d"%self.id
        s += "\n"
        s += self.question 
        s += "\n"
        for i in range(len(self.options)):
            s += "%s  --  %s"%(self.options[i], self.results[i])
            s += "\n"
        s += '-'*50
        return s
        
polls = []
pollIDs = []
bot = commands.Bot(command_prefix='!')

@bot.command(name='n')
async def newPoll(ctx, *args):
    try:
        if ctx.channel.id == WRITE_ID:
            if len(args) < 3:
                await ctx.send("Not enough arguments.")
                return
            numOpts = len(args) - 1
            newPoll = Poll(args[0], args[1:])
            pollStr = newPoll.getPollString()

            pollChan = bot.get_channel(ANS_ID)
            msg  = await pollChan.send(pollStr)
            
            for rea in Poll.reactions[:numOpts]:
                await msg.add_reaction(rea)

            #This sets the poll ID and opens the poll
            newPoll.setID(msg.id)

            polls.append(newPoll)
            pollIDs.append(polls[-1].getID())
            
    except AttributeError as err:
        print(err)
        await bot.close()

@bot.event
async def on_ready():
    print('Bot ready')

@bot.event
async def on_reaction_add(reaction, user):
    userName = user.name
    ID = reaction.message.id
    try:
        tmpPoll = polls[pollIDs.index(ID)]
    except ValueError as err:
        return
 
    if userName != 'poller':
        #Get reaction
        emoji = reaction.emoji
        #Remove reaction
        await reaction.remove(user)

        #Tally vote
        succ = tmpPoll.addVote(emoji, userName)
        
        if succ == 0:
            print('Vote on poll %d!'%ID)
            print(tmpPoll.getResults())
        else:
            print(succ[1])

@bot.command(name='stop')
async def stop(ctx):
    if ctx.channel.id == WRITE_ID:
        await bot.close()

bot.run(TOKEN)
