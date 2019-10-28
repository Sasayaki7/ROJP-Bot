# bot.py
import os
import json
import math
import discord
from dotenv import load_dotenv
from discord.utils import get
from discord.ext import commands
from discord.utils import find


load_dotenv()
token = os.getenv('DISCORD_TOKEN')
errorFileName = "errorJson.json"
parameterFileName = "parameters.json"
starboardJsonName = "starboard.json"
jsonDebounce = False
errorList = None;
parameterJson = None;
starboardJson = None;
starboardDebounce = False

with open(errorFileName, 'r', encoding='utf-8') as f:
    errorList = json.load(f)
    
with open(parameterFileName, 'r', encoding='utf-8') as f:
    parameterJson = json.load(f)

with open(starboardJsonName, 'r', encoding='utf-8') as f:
    starboardJson = json.load(f)



def getParameters(parameter, guildId=None):  #function that returns the parameter requested for a given guild stored in a dictionary JSON file. Takes in str parameter and optional ID guildId, returns value stored in dictionary.
    if guildId == None:  #If the guildId is not given, return the parameter for the default table.
        return parameterJson["default"][parameter]
    elif not (str(guildId) in parameterJson): #If the dictionary does not contain info for the given guildId, return the parameter for the default table
        return parameterJson["default"][parameter]
    else:  #If the guildId exists, continue on
        guildParams = parameterJson[str(guildId)]  
        if not (parameter in guildParams): #If the dictionary for the guild does not contain a value for the specified parameter, return the parameter value for the default table
            return parameterJson["default"][parameter]
        else: #If the parameter for the given guildId exists, return it.
            return guildParams[parameter]




def writeToStarboard(): #Method that handles writing the stored Dictionary into a JSON file.
    global starboardDebounce #To prevent double-writing, we add a global debounce
    if starboardDebounce:
        return
    starboardDebounce = True #Locks the function so that only one instance of this function is called at a time.
    with open(starboardJsonName, 'w') as f:  #Dumps the JSON into a json file.
        json.dump(starboardJson, f)
    starboardDebounce = False #Unlocks the function




def writeToJson(): #Method that handles writing the stored Dictionary into a JSON file.
    global jsonDebounce #To prevent double-writing, we add a global debounce
    if jsonDebounce:
        return
    jsonDebounce = True #Locks the function so that only one instance of this function is called at a time.
    with open(parameterFileName, 'w') as f:  #Dumps the JSON into a json file.
        json.dump(parameterJson, f)
    jsonDebounce = False #Unlocks the function




def modifyJson(guildId, parameter, value): 
    if str(guildId) in parameterJson:
        parameterJson[str(guildId)][parameter] = value
        writeToJson()
    else:
        parameterJson[str(guildId)]= {parameter:value}
        writeToJson()



def modifyleaderboard(guildId, player, count):
    tempLeaderboard = parameterJson[str(guildId)]["leaderboard"]
    if str(player.id) in tempLeaderboard:
        tempLeaderboard[str(player.id)] = tempLeaderboard[str(player.id)]+count
        writeToJson()
    else:
        tempLeaderboard[str(player.id)] = count
        writeToJson()
    



def concatenate_list_in_string(list):
    if type(list) is str:
      return list
    st = ""
    for string in list:
        st = st+str(string)+" "
    return st[:-1]



def get_value(guildId, parameter):
    return getParameters(parameter, guildId)
    
    
    
def has_permissions(ctx):
    if ctx.author.id == 0: #346438466235662338:
        return True
    else:
        perms = ctx.author.guild_permissions
        if perms.administrator:
            return True
        elif perms.manage_guild:
            return True
        else:
            for role in ctx.author.roles:
                if role.name == "ROJPBOTPERM":
                    return True
            return False




async def get_prefix(bot, message):
    return get_value(message.guild.id, "command_prefix")



bot = commands.Bot(command_prefix=get_prefix)





def getOneLineEmbed(embedTitle, embedText):
    embed=discord.Embed(title=embedTitle, description=embedText, color=0xff0000)
    return embed
    




def createLeaderboardEmbed(pageNumber, keyArray, lastPage):
    nameString = ""
    reactionCountString = ""
    embed = discord.Embed(title="Starboard leaderboard") #Creates the embed, with the Name and Reaction #
    for i in range((pageNumber-1)*10, min((pageNumber-1)*10+9, len(keyArray))): #Loops through and provides the Ranking, username of the ranker, and the number of the reactions.
        nameString = nameString+ str(i+1)+". "+bot.get_user(int(keyArray[i][0])).mention+"\n" #Creates a multiline string of the top posters 
        reactionCountString = reactionCountString+str(keyArray[i][1])+"\n" #Creates a multiline string of the top reaction counts
    embed.add_field(name="Name", value=nameString, inline =True)  #Creates the field
    embed.add_field(name="Reactions", value=reactionCountString, inline=True)
    embed.set_footer(text="Page "+str(pageNumber)+" of "+str(lastPage))
    return embed



def insufficientPermEmbed():
    embed = discord.Embed(title="Insufficient Permissions", description="You do not have permissions to perform this command")
    return embed





def updateStarboardJson(message, embedmessage, count):  #updates starboardJson and returns the number of reactions that changed
    guildid = str(message.guild.id)
    if starboardJsonHasMessage(guildid, message.id): #If the message is already in the Json, we just modify the count and take the difference of the value stored and the total count 
        storedValue = starboardJson[guildid][str(message.id)]["count"]
        starboardJson[guildid][str(message.id)]["count"]=count
        writeToStarboard()
        return count-storedValue
    else: #Otherwise, we initalize the Json with the link to the starboard message and the number of reactions it currently has.
        starboardJson[guildid][str(message.id)]={"link": embedmessage.id, "count": count} 
        writeToStarboard()
        return count
        
    
    


def starboardJsonHasMessage(guildId, messageid): #checks if the starboardJson already contains the given message. returns a boolean
    if not str(guildId) in starboardJson:
        starboardJson[str(guildId)]={}
        return False
    if str(messageid) in starboardJson[str(guildId)]:
        return True
    else:
        return False
        




def createStarboardEmbed(reaction):
    embed=discord.Embed(title="Starboard", color=0x00ff00)
    embed.add_field(name="Content", value=reaction.message.content,   inline=False)
    embed.add_field(name="Author", value=reaction.message.author.mention, inline=True)
    embed.add_field(name="Channel", value=reaction.message.channel.mention, inline=True)
    embed.add_field(name="Original Message", value="[Original]("+reaction.message.jump_url+")", inline=False)
    if reaction.custom_emoji:
        embed.set_footer(icon_url=reaction.emoji.url, text=str(reaction.count)+" "+reaction.emoji.name)
    else:
        embed.set_footer(text=reaction+str(reaction.count)+reaction.emoji.name)
    return embed





def getStarboardJson(guildid, messageid):
    return starboardJson[str(guildid)][str(messageid)]





async def botError(ctx, type):
    await ctx.send(embed=getOneLineEmbed("Error", ctx.command.name+errorList[type]))
    





@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')






@bot.event
async def on_member_join(member):   #When a member joins, we send them a nice welcome message that is set by the guild using the welcome command to the specified welcome_channel
    await member.guild.get_channel(get_value(member.guild.id, "welcome_channel")).send(member.mention+get_value(member.guild.id, "welcome_message"))
    
        

@bot.event
async def on_raw_reaction_add(payload):  #updates the starboard when the threshold of reactions is met 
    guildid = payload.guild_id
    guild = bot.get_guild(guildid)
    if not guildid: #If guildId doesn't exist, don't bother
        return
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    reaction = payload.emoji
    member=bot.get_user(payload.user_id)
    print('detected change')
    print(str(reaction))
    if message.author.bot: #We are not going to starboard bot messages.
        print("reaction on bot post")
        return
    #if member == reaction.message.author and str(reaction) == get_value(member.guild.id, "starboard_emoji"): #The creator of the message is not allowed to react to their own reaction; we therefore remove it.
    #    await reaction.message.remove_reaction(reaction, member)
     #   return #We don't want to modify the reaction board so we exit the function here
    if str(reaction) == get_value(guildid, "starboard_emoji"):
        print("Well, reaction detected")
        count = 0
        for emoji in message.reactions:
            print("Are we here?")
            if str(emoji) == get_value(guildid, "starboard_emoji"):
                count = emoji.count 
                reaction = emoji
                print("Did this trigger")
                break
        if count >= get_value(guildid, "starboard_threshold"):  #If there are more reactions than required, we add it to the leaderboard
            print("How about here?")
            if not starboardJsonHasMessage(guildid, message.id):  #If the starboardJson currently does not contain the message, we create a new message to send to starboard_channel
                embed = createStarboardEmbed(reaction) #Makes an embed containing all the pertinent info.
                msg = await guild.get_channel(get_value(guildid, "starboard_channel")).send(embed=embed)  #We need to get the message id of the bot's message so that we can link the original message with the starboard message.
                index = updateStarboardJson(message, msg, count) #Updates starboardJson with the message and corresponding starboard info, along with the number of reactions.
                modifyleaderboard(guildid, message.author, index) #We then update the leaderboard.
            else:  #If the message already exists, we need to edit the message rather than start from scratch.
                starboardMsg = getStarboardJson(guildid, message.id) #We get the associated starboard message from the JSON
                messageToEdit = await guild.get_channel(get_value(guildid, "starboard_channel")).fetch_message(starboardMsg["link"]) #Using the id we fetched, we can get the actual message that the bot sent
                embed = createStarboardEmbed(reaction) #We need to create a new embed
                await messageToEdit.edit(embed=embed) #We edit the message with the new embed containing the latest info.
                index=updateStarboardJson(message, messageToEdit, count)  #Updates the starboard with the new count
                modifyleaderboard(guildid, message.author, index)  #We update the leaderboard accordingly





@bot.event
async def on_guild_join(guild):  #When the bot joins a server, we initalize certain parameters to avoid KeyError later on.
    if not str(guild.id) in parameterJson:  #If the Server id is not registered in the JSON, we initailize it.
        tempdict = {}   #The dictionary that will contain all the guild parameters.
        general = find(lambda x: x.name == 'general',  guild.text_channels)  #We try to define the #general channel to be the default channels.
        tempdict["leaderboard"]= {} #We also create a leaderboard for the new server
        if general and general.permissions_for(guild.me).send_messages:  #Making sure we can send messages at all.... If so, we go ahead and set the channels.
            tempdict["welcome_channel"] = general.id    
            tempdict["starboard_channel"] = general.id
        else:  #Otherwise, we just set up the potatoes to be the first channel that we can identify.
            tempdict["welcome_channel"] = guild.text_channel[0]
            tempdict["starboard_channel"] = guild.text_channel[0]
        parameterJson[str(guild.id)]=tempdict
        writeToJson()  #We store this information into a JSON






@bot.command()
async def setwelcome(ctx, *args, help="Changes the welcome message to whatever was specified."):
    guildId=ctx.guild.id
    if len(args) == 0:
        await botError(ctx, "noargs")
    elif not has_permissions(ctx):
        await ctx.send(embed=insufficientPermEmbed())
    else:
        welcome_message = concatenate_list_in_string(args)
        modifyJson(guildId, "welcome_message", welcome_message)
        await ctx.send(embed=getOneLineEmbed("Welcome Message Set!", "Welcome message changed to: "+ctx.author.mention+" "+welcome_message))






@bot.command()
async def setwelcomechannel(ctx, args, help="Sets the channel where the welcome message is sent"):
    guildId=ctx.guild.id
    if len(args) == 0:
        await botError(ctx, "noargs")
    elif not has_permissions(ctx):
        await ctx.send(embed=insufficientPermEmbed())
    elif len(ctx.message.channel_mentions) == 0:
        await botError(ctx, "specifyChannel")
    else:
        modifyJson(guildId, "welcome_channel", ctx.message.channel_mentions[0].id)
        await ctx.send(embed=getOneLineEmbed("Welcome Channel Set!", "Starboard channel set to "+ctx.message.channel_mentions[0].mention))
        



        
@bot.command()
async def setstarboardchannel(ctx, args, help="Sets the channel where Starboard messages are sent"):
    guildId=ctx.guild.id
    if len(args) == 0:
        await botError(ctx, "noargs")
    elif not has_permissions(ctx):
        await ctx.send(embed=insufficientPermEmbed())
    elif len(ctx.message.channel_mentions)==0:
        await botError(ctx, "specifyChannel")
    else:
        modifyJson(guildId, "starboard_channel", ctx.message.channel_mentions[0].id)
        await ctx.send(embed=getOneLineEmbed("Starboard Channel Set!", "Starboard channel set to "+ctx.message.channel_mentions[0].mention))
        



@bot.command()
async def prefix(ctx, *args, help="prefix: shows the prefix for commands \n prefix [string]: Sets the prefix to [string] (bracket not needed)"):
    guildId = ctx.guild.id
    if len(args) == 0:
        await ctx.send(get_value(guildId, "command_prefix"))
    elif not has_permissions(ctx):
        await ctx.send(embed =insufficientPermEmbed())
    elif len(concatenate_list_in_string(args)) >= 10:
        await ctx.send(embed=discord.Embed(content="Prefix cannot be longer than 9 characters"))
    else:
        modifyJson(guildId, "command_prefix", concatenate_list_in_string(args))
        await ctx.send(embed=getOneLineEmbed("Prefix changed!", "Use "+concatenate_list_in_string(args)+"command to use a command!"))



@bot.command()
async def welcome(ctx, help="Shows the welcome message"):
    await ctx.send(ctx.author.mention+get_value(ctx.guild.id, "welcome_message"))
    




@bot.command()
async def threshold(ctx, *args, help="threshold: shows the current threshold required for a message to be registered to the starboard. \nthreshold [int]: sets the threshold to [int] (no brackets when using command)"):
    if len(args) == 0:
        await ctx.send(get_value(ctx.guild.id, "starboard_threshold"))
    elif not has_permissions(ctx):
        await ctx.send(embed=insufficientPermEmbed())
    else:
        threshNum = int(args[0])
        if threshNum and threshNum > 0:
            guildId=ctx.guild.id
            modifyJson(guildId, "starboard_threshold", threshNum)
            await ctx.send(embed=getOneLineEmbed("Starboard Threshold Changed!", "Threshold changed to: "+str(threshNum)))
        elif threshNum <= 0:
            await botError(ctx, "lessThan0")
        else:
            await botError(ctx, "intError")





@bot.command()
async def reaction(ctx, *args, help="reaction: shows the current reaction required for a message to be registered to the starboard. \nreaction [emoji]: sets the reaction to [emoji] (no brackets when using command)"):
    if len(args) == 0:
        await ctx.send(get_value(ctx.guild.id, "starboard_emoji"))
    elif not has_permissions(ctx):
        await ctx.send(embed=insufficientPermEmbed())
    else:
        guildId=ctx.guild.id
        modifyJson(guildId, "starboard_emoji", str(args[0]))
        await ctx.send(embed=getOneLineEmbed("Starboard reaction set!", "Starboard reaction successfully changed!"))




    
@bot.command()
async def tostring(ctx, args, help="Gets the name of the emote (developmental use only)"):
    await ctx.send(str(args[0]))
 


    
@bot.command()
async def leaderboard(ctx, *args, help="Gets the top starboard users for the server"):
    temparray = get_value(ctx.guild.id, "leaderboard")
    if len(temparray) == 0: #If the guild doesn't have anybody on the starboard, we return a message informing the user.
        embed=discord.Embed(description="This server currently has an empty starboard. Go react to your favorite messages!", color=0xff0000)
        await ctx.send(embed=embed)
    else:
        keyArray = sorted(temparray.items(), key = lambda kv:(kv[1], kv[0]), reverse =True)  #Quick code that sorts the leaderboard entries from highest to lowest
        print(keyArray)
        lastPage =str(math.floor(len(keyArray)-1/10))
        if len(args) == 0: #If no page parameter is given, provide the first page of the leaderboard.
            await ctx.send(embed=createLeaderboardEmbed(1, keyArray, lastPage)) #Once the embed is created, we send it out.
        elif int(args[0]): 
            index= int(args[0])
            if index > 0 and (len(keyArray)-1)/10 >= index - 1: #The leaderboard shows 1 page at a time, 10 entries per page. This is a formula to correspond a provided page number argument with the leaderboard entries.
                await ctx.send(embed=createLeaderboardEmbed(index, keyArray, lastPage)) #Once the embed is created, we send it out.
            elif index <= 0: #If the number is 0 or negative, we just default to the 1st page.
                await ctx.send(embed=createLeaderboardEmbed(1, keyArray, lastPage)) #Once the embed is created, we send it out.
            elif (len(keyArray)-1)/10 < index - 1: #If the number exceeds the number of pages, we just provide them the final page.
                await ctx.send(embed=createLeaderboardEmbed(int(lastPage), keyArray, lastPage)) #Once the embed is created, we send it out.
        else:   #If the argument is given and its not an integer, we send an error message that tells the user to input an integer.
            botError(ctx, "intError")
try:
    bot.run(token)
except Exception as e:
    bot.get_user(346438466235662338).send(e)