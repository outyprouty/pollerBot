# bot.py
import os

from discord.ext import commands
from dotenv import load_dotenv
import discord

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
WRITE_ID = int(os.getenv('WRITE_POLL'))
ANS_ID = int(os.getenv('ANS_POLL'))
ANS_ID = int(os.getenv('LOG_POLL'))

class Poll:

    reactions = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']
    cancelEmoji = '🇿'
    
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
    
    def getNumOptions(self):
        return len(self.options)

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
        if self.open:
            if emoji == Poll.cancelEmoji:
                self.cancelCtr += 1
                
                if self.cancelCtr >= 2:
                    self.open = False
                    return -2, "Poll Closed"
                return 0, "Success"
            if user in self.responded:
                return -1, "Already responded"
            try:
                voteIndex = Poll.reactions.index(emoji)
            except ValueError as err:
                return -1, "Wrong emoji Used!"
            self.results[voteIndex] += 1
            self.responded.append(user)
            return 0,'Success'
        else:
            return -2, "Poll Closed"
    
    def getResults(self):
        s = '-'*50
        s += "\n"
        s += "Results for poll ID #%d"%self.id
        s += "\n"
        if self.open:
            s += "Poll is still open!"
        else:
            s += "Poll is closed!"
        s += "\n"
        
        s += self.question 
        s += "\n"
        for i in range(len(self.options)):
            s += "%s  --  %s"%(self.options[i], self.results[i])
            s += "\n"
        s += '-'*50
        return s


helpStr = \
"""
Poller Polls! Offering Anonymous Polling
 Use:
    In pollcre8 channel: !newPoll "Question" "Opt1" "Opt2" ... "OptN"
        Support for N <= 10
        Ensure question and options are in quotes
    Instruct respondents to click a single emoji cooresponding to 
        the choice of the respondent. Responses are recorded back-side.
    Responses are visible to NO ONE but pollcre8 channel viewers.
    No usernames are associated with responses in persistent logs.
 Closing Poll:
    React with :regional_indicator_z: twice on poll.
    This will dump the results of this poll to the pollcre8 channel.
 Closing Bot:
    !endBot
    This will dump all poll results from this session to pollcre8 channel.
 Happy Polling!
"""     
polls = []
pollIDs = []
bot = commands.Bot(command_prefix='!')
writeChan = bot.get_channel(WRITE_ID)
ansChan = bot.get_channel(ANS_ID)
logChan = bot.get_channel(LOG_ID)

#Just to let logs know bot is ready
@bot.event
async def on_ready():
    print('Bot ready')

@bot.command(name='newPoll')
async def newPoll(ctx, *args):
    try:
        #If pollcre8 channel
        if ctx.channel.id == WRITE_ID:
            #Input checking
            if len(args) < 3:
                #Write help string to user in pollcre8
                await writeChan.send("Not enough arguments.\n" + helpStr)
                return
            #Create new Poll object 
            newPoll = Poll(args[0], args[1:])
            
            #Get number of poll options
            numOpts = newPoll.getNumOptions()
            
            #Define pollString aka Question and Answers string
            pollStr = newPoll.getPollString()

            #Write the poll to the channel
            msg  = await ansChan.send(pollStr)
           
            #Add the reactions to the poll! 
            for rea in Poll.reactions[:numOpts]:
                await msg.add_reaction(rea)

            #This sets the poll ID and opens the poll
            newPoll.setID(msg.id)

            #This is clerical -- keeping track of polls
            polls.append(newPoll)
            pollIDs.append(polls[-1].getID())
            
    except AttributeError as err:
        print(err)
        await bot.close()

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
        
        await writeChan.send(succ[1])
        if succ[0] == -2:
            await writeChan.send(tmpPoll.getResults())

@bot.command(name='rem')
async def remove(ctx):
    messages = await ctx.channel.history(limit=500).flatten()
    for m in messages:
        await m.delete()
    

@bot.command(name='endBot')
async def stop(ctx):
    if ctx.channel.id == WRITE_ID:
        print("Bot ended by user command.")
        print("Dumping all Poll results")
        for p in polls:
            print('-'*50)
            print(p.getResults())
            print('-'*50)
        await bot.close()

bot.run(TOKEN)
