#/u/GoldenSights
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import os
import sys
import sqlite3

'''USER CONFIGURATION'''
APP_ID = ""
APP_SECRET = ""
APP_URI = ""
APP_REFRESH = ""
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = ""
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBRESTRICT = ["GoldTesting", "test"]
#This is the subreddit where the bot is allowed to post.
#If a user inputs a permalink that does not lead to this subreddit, the post will fail.
#To allow any, delete everything between the brackets.
COMHEADER = "This is at the top of the comment\n\n"
#Comment Header. If you place _username_ anywhere in this line, it will be replaced by the name of the person who requested the comment.
COMFOOTER = "\n\nThis is at the bottom of the comment"
#Comment Footer. If you place _username_ anywhere in this line, it will be replaced by the name of the person who requested the comment.
PMHEADER = "This is at the top of the return PM\n\n"
#PM Header
PMFOOTER = "\n\nThis is at the bottom of the return PM"
#PM Footer
PMSUCCESS = "Your comment has successfully been created: [Here](_permalink_)"
#This will be sent to the user when his post succeeds
#_permalink_ will be replaced by the successful comment's permalink. You may move this around as you please.
PMFAILURE = "Your comment has been rejected for the following reason(s):\n\n"
#This will be sent to the user when his post fails. Error messages will be displayed
PMTITLE = "Anonymisc"
#This is the title of the message that will be returned to the user

ERRBANNED = "- You have been banned from using this service"
#If an admin has placed this user on the banlist, return this error
ERRFETCH = "- Failed to fetch comment object given that permalink. You should use the permalink exactly as it appears when you cut / copy from your address bar. The last 7 characters are the comments id number."
#If praw fails in fetching the object from ID, return this error
ERRNOPERMA = "- The first line of your PM must be a permalink to a comment."
#If the first line does not contain any visible permalink, return this error
ERRFORMATTING = "- Your message does not follow the proper format"
#If line formatting is wrong or lines are missing, return this error
ERRSUBREST = "- The bot will not go to that subreddit"
#If the bot is sent to an unapproved subreddit, return this error
ERRWHITELIST = "- The bot is currently running in whitelist mode. You have not been added to the whitelist"
#If WHITEMODE is set to True and the user is not on the whitelist, return this error
ERRTWICE = "- That comment has already been replied to through this service. The bot does not allow multiple replies at this time"
#If ALLOWTWICE is False and a second user tries to make a reply, return this error

WHITEMODE = False
#If set to True, the bot will only allow users who are registered in the whitelist.
#Members can be added to the whitelist by an admin or by entering a proper password
#Use True or False (With Capitals! No quotation marks!)

BANCOMMAND = "banuser"
UNBANCOMMAND = "unbanuser"
BANLISTCOMMAND = "banlist?"
#The ADMIN may use these commands to ban / unban a username
#BANLISTCOMMAND will return a PM with the names of all banned and whitelisted users.
WHITECOMMAND = "whitelist"
UNWHITECOMMAND = "unwhitelist"
#The ADMIN may use these commands to add / remove from the whitelist

BANPM = True
WHITEPM = True
#Do you want to PM the user when the ADMIN bans or whitelists him?
#Use True or False (With Capitals! No quotation marks!)

WHITEPASS = "addmetothelist"
#If the user's PM contains this string anywhere in the body, he will be added to the whitelist.

FIELDPERM = ["Permalink:", "Comment Permalink:", "Comment Link:", "Perma:"]
FIELDTEXT = ["Link Text:", "Hyperlink Text:", "Text:"]
FIELDURL = ["Link URL:", "Hyperlink URL:", "URL:"]
#These are the three fields the user needs to fill.

ALLOWTWICE = True
#Is it okay for multiple people to reply to the same comment?
#If this is False, only one person will be able to create a reply to a permalink
#Use True or False (With Capitals! No quotation marks!)

DISTINGUISHCOMMENT = False
#If your bot is going to be operating in a sub where it is a moderator, you may choose to distinguish the comment
#Use True or False (With Capitals! No quotation marks!)
WAIT = 15
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
ADMIN = ["GoldenSights"]
#This is the owner(s) of the bot. Only ADMINS can manage user bans.
'''All done!'''





try:
    import bot 
    USERAGENT = bot.getaT()
except ImportError:
    pass

WAITS = str(WAIT)


sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded old comments')
cur.execute('CREATE TABLE IF NOT EXISTS banned(name TEXT)')
print('Loaded blacklist')
cur.execute('CREATE TABLE IF NOT EXISTS white(name TEXT)')
print('Loaded whitelist')

sql.commit()


r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def scanPM():
    banlist = []
    whitelist = ADMIN[:]
    cur.execute('SELECT * FROM banned')
    fetched = cur.fetchall()
    for m in fetched:
        banlist.append(m[0])
    cur.execute('SELECT * FROM white')
    fetched = cur.fetchall()
    for m in fetched:
        whitelist.append(m[0])
    print(str(len(banlist)) + ' banned users. ' + str(len(whitelist)) + ' whitelisted.\n')
    print('Searhing Inbox.')
    pms = r.get_unread(unset_has_mail=True, update_user=True)
    for pm in pms:
        failresult = []
        failoverride = False
        cobj = None
        ltext = ''
        lurl = ''
        final = None
        print(pm.id + ', ', end='')
        try:
            author = pm.author.name.lower()
            print(author)
            bodysplit = pm.body.lower().split('\n\n')
            line = bodysplit[0]
            if any(author == admin.lower() for admin in ADMIN):
                if UNBANCOMMAND.lower() in line:
                    user = line.split()[-1]
                    print('\t[   ] ADMIN has unbanned ' + user)
                    cur.execute('DELETE FROM banned WHERE name=?', [user])
                    failoverride =  True
                    if BANPM == True:
                        r.send_message(user, PMTITLE, 'You have been unbanned from using this service.', captcha = None)
                elif BANCOMMAND.lower() in line:
                    user = line.split()[-1]
                    print('\t[   ] ADMIN has banned ' + user)
                    cur.execute('INSERT INTO banned VALUES(?)', [user])
                    failoverride =  True
                    if BANPM == True:
                        r.send_message(user, PMTITLE, 'You have been banned from using this service.', captcha = None)
                elif UNWHITECOMMAND.lower() in line:
                    user = line.split()[-1]
                    print('\t[   ] ADMIN has unwhitelisted ' + user)
                    cur.execute('DELETE FROM white WHERE name=?', [user])
                    failoverride =  True
                    if WHITEPM == True:
                        r.send_message(user, PMTITLE, 'You have been removed from the whitelist.', captcha = None)
                elif WHITECOMMAND.lower() in line:
                    user = line.split()[-1]
                    print('\t[   ] ADMIN has whitelisted ' + user)
                    cur.execute('INSERT INTO white VALUES(?)', [user])
                    failoverride =  True
                    if WHITEPM == True:
                        r.send_message(user, PMTITLE, 'You have been added to the whitelist.', captcha = None)
                elif BANLISTCOMMAND.lower() in line:
                    print('\t[   ] ADMIN has requested the banlist')
                    failoverride = True
                    r.send_message(author, PMTITLE, 'Banned Users:\n\n' + '\n\n'.join(banlist) + '\n\n_____\n\nWhitelisted Users:\n\n' + '\n\n'.join(whitelist), captcha=None)
            if WHITEPASS.lower() in pm.body.lower():
                print('\t[   ] ' + author + ' has whitelisted himself using the password')
                cur.execute('INSERT INTO white VALUES(?)', [author])
                failoverride = True
                r.send_message(author, PMTITLE, 'You have been added to the whitelist.', captcha = None)
                whitelist.append(author)

            if not any(author == user.lower() for user in banlist):
                if WHITEMODE == False or author in whitelist:
                    if any(field.lower() in pm.body.lower() for field in FIELDPERM):
                        for bline in bodysplit:
                            if any(field.lower() in bline for field in FIELDPERM):
                                bindex = bodysplit.index(bline)
                                for word in bline.split():
                                    if 'www.reddit.com/r/' in word:
                                        link = word
                                        if '/' == link[-8]:
                                            link = link[-7:]
                                        elif '/' == link[-1] and '/' == link[-9]:
                                            link = link[-8:-1]
                                        print('\t[   ] ' + link)
                                try:
                                    cobj = r.get_info(thing_id='t1_' + link)
                                    if ALLOWTWICE == False and not any(author == admin.lower() for admin in ADMIN):
                                        cur.execute('SELECT * FROM oldposts WHERE id=?', [cobj.id])
                                        if cur.fetchone():
                                            print('\t[ERR] This comment has already been replied to')
                                            failresult.append(ERRTWICE)
                                    print('\t[   ] Found comment object')
                                    if SUBRESTRICT == [] or any(cobj.subreddit.display_name.lower() == sub.lower() for sub in SUBRESTRICT):
                                        print('\t[   ] Passed sub restriction')
                                        try:
                                            if any(field.lower() in bodysplit[bindex+1] for field in FIELDTEXT):
                                                ltext = bodysplit[bindex+1]
                                                for field in FIELDTEXT:
                                                    ltext = ltext.replace(field.lower(), '')
                                                ltext = ltext.replace('[', '')
                                                ltext = ltext.replace(']', '')
                                                print('\t[   ] Found Link Text')
                                            if any(field.lower() in bodysplit[bindex+2] for field in FIELDURL):
                                                lurl = bodysplit[bindex+2]
                                                for field in FIELDURL:
                                                    lurl = lurl.replace(field.lower(), '')
                                                lurl = lurl.replace('(', '')
                                                lurl = lurl.replace(')', '')
                                                lurl.replace(' ','')
                                                if lurl[:4] == 'www.':
                                                    lurl = 'http://' + lurl
                                                print('\t[   ] Found Link URL')
                                        except:
                                            print('\t[ERR] Formatting issue')
                                            failresult.append(ERRFORMATTING)
                                    if SUBRESTRICT != [] and not any(cobj.subreddit.display_name.lower() == sub.lower() for sub in SUBRESTRICT):
                                        print('\t[ERR] Bad subreddit')
                                        failresult.append(ERRSUBREST)

                                    elif ltext == '' or lurl == '':
                                        print('\t[ERR] Formatting issue')
                                        failresult.append(ERRFORMATTING)
                                except:
                                    print('\t[ERR] Fetching comment object failed')
                                    failresult.append(ERRFETCH)
                    else:
                        print('\t[ERR] Formatting issue')
                        failresult.append(ERRFORMATTING)
                else:
                    print('\t[ERR] User not in whitelist')
                    failresult.append(ERRWHITELIST)
            else:
                print('\t[ERR] Banned user')
                failresult.append(ERRBANNED)

            if failoverride == True:
                print('\t[   ] Error Override. Will not send messages.')
                pass
            elif len(failresult) == 0:
                print('\t[   ] Creating comment')
                reply = cobj.reply(COMHEADER.replace('_username_', author) + '\n\n[' + ltext + '](' + lurl + ')\n\n' + COMFOOTER.replace('_username_', author))
                if ALLOWTWICE == False:
                    cur.execute('INSERT INTO oldposts VALUES(?)', [cobj.id])
                if DISTINGUISHCOMMENT == True:
                    try:
                        reply.distinguish()
                    except:
                        print('\t[ERR] Distinguish failed')
                print('\t[   ] Created ' + reply.id)
                print('\t[   ] Sending success message.')
                final = PMHEADER + PMSUCCESS.replace('_permalink_',reply.permalink) + PMFOOTER
                r.send_message(author, PMTITLE, final, captcha=None)
            else:
                print('\t[   ] Sending failure message')
                final = PMHEADER + PMFAILURE + '\n\n'.join(failresult) + PMFOOTER
                r.send_message(author, PMTITLE, final, captcha=None)
        except AttributeError:
            print()
            print('\t[ERR] Author unavailable.')

        pm.mark_as_read()
        sql.commit()


while True:
    try:
        scanPM()
    except Exception as e:
        print('ERROR: ' + str(e))
    print('Running again in ' + WAITS + ' seconds \n_________\n')
    sql.commit()
    time.sleep(WAIT)
