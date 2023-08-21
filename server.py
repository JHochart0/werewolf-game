import socket
import sys
import threading
from time import sleep
import time as ti
import random

# import for every roles of the game
from Roles import role
from Roles import seer
from Roles import villager
from Roles import werewolf
from Roles import witch
from Roles import cupid
from Roles import hunter

# import shuffle for random
from random import shuffle


'''***************************************
***** Differents parameters for the game**
******************************************'''

# game has started or not
game_started = False

# used to know who is the admin, the first client to connect becomes the admin (None is the default value if noone is admin)
admin = None

# Amount of players for the game (there are 8 players minimum and 18 maximum)
nb_min_players = 8
nb_max_players = 18

# Timer for each role
time_debat = 60
time_cupid = 20
time_werewolf = 30
time_hunter = 20
time_witch = 20
time_seer = 20

# roles chosen for the game
has_hunter = True
has_cupid = True
has_seer = True
has_witch = True
nb_werewolf = 2

'''********************************************************
********Differents temporary variables for the game********
***********************************************************'''

# Used to know whose turn it is during the game (base value = "Villager")
turn = "Villager"


# List of roles of the game (we can access to client with the name given to the role)
roles = []

# List of players alive during the game
playersAlive = []

# List of players with numbers of vote on them
playersVoted = {}

# Used to know if we have a winner or not
winner = 0
'''*******************************************
********Variables used for TCP Connections****
**********************************************'''

# List of connected clients and their respective nickname
clients = []
nicknames = []

# IP of the server and ports for UDP and TCP
host = "0.0.0.0"
UDP_PORT = 1500
TCP_PORT = 1501

# Create a socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Sets REUSEADDR (as a socket option) to 1 on socket
udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given IP and port
s.bind((host, TCP_PORT))
udp_server_socket.bind((host, UDP_PORT))


'''*******************************************
*********************Game Part****************
**********************************************'''

# Function to give role randomly to players at the start of the game
def distribuer_role():
    global roles
    global nb_werewolf
    global has_hunter
    global has_cupid
    global has_seer
    global has_witch
    global nb_min_players
    global nb_max_players
    global clients
    global nicknames
    roles.clear()
    playersAlive.clear()
    role_a_distribuer = []
    nb_villager = 0
    if has_hunter:
        role_a_distribuer.append("hunter")
        nb_villager += 1
    if has_cupid:
        role_a_distribuer.append("cupid")
        nb_villager += 1
    if has_seer:
        role_a_distribuer.append("seer")
        nb_villager += 1
    if has_witch:
        role_a_distribuer.append("witch")
        nb_villager += 1
        
    nb_player = min(nb_max_players, len(clients))
    nb_villager = nb_player - nb_villager - nb_werewolf
    role_a_distribuer += ["werewolf" for i in range(nb_werewolf)]
    role_a_distribuer += ["villager" for i in range(nb_villager)]
    shuffle(role_a_distribuer)
    for i in range(len(role_a_distribuer)):
        role = role_a_distribuer[i]
        if role == "hunter":
            roles.append(hunter.Hunter(nicknames[i]))
        elif role == "cupid":
            roles.append(cupid.Cupid(nicknames[i]))
        elif role == "seer":
            roles.append(seer.Seer(nicknames[i]))
        elif role == "witch":
            roles.append(witch.Witch(nicknames[i]))
        elif role == "werewolf":
            roles.append(werewolf.Werewolf(nicknames[i]))
        else:
            roles.append(villager.Villager(nicknames[i]))
        target_message_client(clients[i], f"You are {str(role)}\n".encode("utf8"))
        playersAlive.append(nicknames[i])

#function to choose lovers from cupid
def chooseLovers(lover1, lover2):

    for i in range(len(roles)):
        if roles[i].name == lover1:
            roles[i].inLove = lover2
        elif roles[i].name == lover2:
            roles[i].inLove = lover1
        
    for role in roles:
        if role.strRole=="Cupid":
            role.arrowsSent=True
            break    

    lover1index = nicknames.index(lover1)
    lover2index = nicknames.index(lover2)
    lover1client = clients[lover1index]
    lover2client = clients[lover2index]
    ti.sleep(1)
    target_message_client(lover1client, f"<3 You fall in love with *{lover2}*. You need to be the last one alive with your lover from now !\n".encode("utf8"))
    target_message_client(lover1client, f"You can communicate to your lover in secret using the command !msgLover <message>.\n".encode("utf8"))
    target_message_client(lover2client, f"<3 You fall in love with *{lover1}*. You need to be the last one alive with your lover from now !\n".encode("utf8"))
    target_message_client(lover2client, f"You can communicate to your lover in secret using the command !msgLover <message>.\n".encode("utf8"))

# predict the role for the seer
def predict(targetName):
    for role in roles:
        if role.strRole=="Seer":
            role.personGuessed = targetName
        if targetName==role.name:
            targetRole=role.strRole

    ti.sleep(1)
    target_message_role(f"You predicted the role of *{targetName}*, he is a {targetRole} !\n".encode("utf8"), "Seer")

# shoot a player for the hunter
def shoot(targetName):
    for role in roles:
        if role.strRole=="Hunter":
            role.playerShot=targetName

    ti.sleep(1)
    target_message_role(f"You shoot at *{targetName}* before dying !\n".encode("utf8"), "Hunter")

# Check if a group of people won the game
def victory():
    global playersAlive
    nbAlive = len(playersAlive)
    nbWerewolves = 0

    for role in roles:
        if role.alive and role.strRole == "Werewolf":
            nbWerewolves += 1

    if nbAlive == 2:
        for role in roles:
            if role.name == playersAlive[0]:
                if role.inLove == playersAlive[1]:
                    return 1 # They lived happily ever after

    if nbWerewolves == nbAlive:
        return 2 # Werewolves eated well tonight
    elif nbWerewolves == 0:
        return 3 # Villagers are victorious 
    
    return 0 # Continue

# Game function used to play the game until the end
def game():
    global game_started
    global turn
    global winner
    global playersVoted
    while(True):
        if(game_started):
            broadcast_message(f"The game has started !\n".encode("utf8"))
            while(winner==0):
                ti.sleep(1)
                broadcast_message(f"The night is falling...\n".encode("utf8"))

                #*******Call Cupid********
                if(has_cupid):
                    for role in roles:
                        if role.strRole=="Cupid":
                            cupid=role
                            break
                    if cupid.alive:
                        if not cupid.arrowsSent:
                            turn="Cupid"

                            ti.sleep(1)
                            broadcast_message(f"Cupid is waking up...\n".encode("utf8"))
                            ti.sleep(1)
                            broadcast_message(f"Cupid is shooting his love arrows...\n".encode("utf8"))
                            ti.sleep(1)
                            target_message_role(f"You need to send your love arrows to two players using !sendArrows <IdPlayer1> <IdPlayer2> (check !playerAlive to see IDs).\n".encode("utf8"), "Cupid")
                            target_message_role(f"You have {time_cupid} seconds to choose !\n".encode("utf8"), "Cupid")
                            t1=ti.time()
                            t2=ti.time()
                            while( (t2-t1)<=time_cupid and not cupid.arrowsSent):
                                t2=ti.time()
                                indexCupid=roles.index(cupid)
                                cupid=roles[indexCupid]

                            if((t2-t1)>time_cupid):
                                turn=""
                                target_message_role(f"You ran out of time !\n".encode("utf8"), "Cupid")
                                random1 = random.randint(0, len(playersAlive)-1)
                                lover1=playersAlive[random1]
                                random2=random.randint(0, len(playersAlive)-1)
                                lover2=playersAlive[random2]
                                while(lover1==lover2):
                                    random2=random.randint(0, len(playersAlive)-1)
                                    lover2=playersAlive[random2]
                                chooseLovers(lover1, lover2)
                            i=0   
                            for role in roles:
                                if role.inLove!="":
                                    if i==0:
                                        lover1=role.inLove
                                        i+=1
                                    if i==1:
                                        lover2=role.inLove
                            ti.sleep(1)
                            target_message_role(f"Your arrows were sent to *{lover1}* and *{lover2}* !\n".encode("utf8"), "Cupid")

                #********Call Seer********
                if(has_seer):
                    for role in roles:
                        if role.strRole=="Seer":
                            seer=role
                            break
                    if seer.alive:
                        turn="Seer"

                        ti.sleep(1)
                        broadcast_message(f"The seer is waking up...\n".encode("utf8"))
                        ti.sleep(1)
                        broadcast_message(f"The seer will predict another player role...\n".encode("utf8"))
                        ti.sleep(1)
                        target_message_role(f"You need to predict a role of another player using !predict <IdPlayer> (check !playerAlive to see IDs).\n".encode("utf8"), "Seer")
                        target_message_role(f"You have {time_seer} seconds to choose !\n".encode("utf8"), "Seer")
                        t1=ti.time()
                        t2=ti.time()
                        while( (t2-t1)<=time_seer and seer.personGuessed==""):
                            t2=ti.time()
                            indexSeer=roles.index(seer)
                            seer=roles[indexSeer]

                        if((t2-t1)>time_seer):
                            turn=""
                            target_message_role(f"You ran out of time !\n".encode("utf8"), "Seer")
                            random1 = random.randint(0, len(playersAlive)-1)
                            predicted=playersAlive[random1]
                            while(predicted==seer.name):
                                random1 = random.randint(0, len(playersAlive)-1)
                                predicted=playersAlive[random1]
                            predict(predicted)
                    
                    for role in roles:
                        if role.strRole=="Seer":
                            role.personGuessed=""
                
                #********Call Werewolves********
                turn="Werewolf"
                ti.sleep(1)
                broadcast_message(f"The Werewolves are waking up...\n".encode("utf8"))
                ti.sleep(1)
                broadcast_message(f"The werewolves will choose their victim...\n".encode("utf8"))
                ti.sleep(1)
                target_message_role(f"You need to vote for the victim of the night using !vote <IdPlayer> (check !playerAlive to see IDs).\n".encode("utf8"), "Werewolf")
                target_message_role(f"You have {time_werewolf} seconds to debate and choose !\n".encode("utf8"), "Werewolf")

                t1=ti.time()
                t2=ti.time()
                while((t2-t1)<=time_werewolf):
                    t2=ti.time()

                if((t2-t1)>time_werewolf):
                    turn=""
                    target_message_role(f"Time over !\n".encode("utf8"), "Werewolf")
                    playersVoted={}
                    for player in playersAlive:
                        playersVoted[player]=0


                    for role in roles:
                        if role.strRole=="Werewolf":
                            if role.vote!="":
                                playersVoted[role.vote]+=1
                                role.vote=""
                    maxVote=max(playersVoted.values())
                    if maxVote>0:
                        playerAtMax=0
                        for player in playersVoted:
                            if playersVoted[player]==maxVote:
                                playerAtMax+=1
                                playerTarget=player

                        if playerAtMax==1:
                            for role in roles:
                                if role.strRole=="Werewolf":
                                    role.personEatten=playerTarget
                            ti.sleep(1)
                            target_message_role(f"The player *{playerTarget}* is the victim of the night !\n".encode("utf8"), "Werewolf")
                        else:
                            ti.sleep(1)
                            target_message_role(f"There is not an absolute majority in the votes, nobody will die tonight...\n".encode("utf8"), "Werewolf")
                    else:
                        ti.sleep(1)
                        target_message_role(f"Nobody has been voted tonight, nobody will die...\n".encode("utf8"), "Werewolf")

                #********Call Witch********   
                if(has_witch):
                    for role in roles:
                        if role.strRole=="Witch":
                            witch=role
                            break
                    if witch.alive:
                        turn="Witch"
                        ti.sleep(1)
                        broadcast_message(f"The witch is waking up...\n".encode("utf8"))
                        ti.sleep(1)
                        broadcast_message(f"The witch will play with her potions...\n".encode("utf8"))
                        ti.sleep(1)
                        if(witch.hasHealingPotion or witch.hasPoisonPotion):
                            if(witch.hasPoisonPotion):
                                ti.sleep(1)
                                target_message_role(f"You still have your poison Potion !\n".encode("utf8"), "Witch")
                                target_message_role(f"You can decide to use it on someone else by using !usePoisonPotion <idPlayer> (check !playerAlive to see IDs)\n".encode("utf8"), "Witch")
                            if(witch.hasHealingPotion):
                                ti.sleep(1)
                                target_message_role(f"You still have your healing Potion !\n".encode("utf8"), "Witch")
                                for role in roles:
                                    if role.strRole=="Werewolf":
                                        targetWerewolf=role.personEatten
                                ti.sleep(1)
                                if targetWerewolf=="":
                                    target_message_role(f"The werewolves didn't choose a victim tonight, you can keep your healing potion !\n".encode("utf8"), "Witch")
                                else:
                                    target_message_role(f"The victim from werewolves is *{targetWerewolf}* !\n".encode("utf8"), "Witch")
                                target_message_role(f"You can decide to save the victim with your healing potion by using !useHealingPotion.\n".encode("utf8"), "Witch")
                            ti.sleep(1)
                            target_message_role(f"You have {time_witch} seconds to choose !\n".encode("utf8"), "Witch")
                        else:
                            ti.sleep(1)
                            target_message_role(f"You already used all your potions.\n".encode("utf8"), "Witch")
                            ti.sleep(1)
                            target_message_role(f"Just wait {time_witch} seconds for the end of your turn.\n".encode("utf8"), "Witch")
                        t1=ti.time()
                        t2=ti.time()
                        while((t2-t1)<=time_witch):
                            t2=ti.time()

                        if((t2-t1)>time_witch):
                            turn=""
                            target_message_role(f"Time over !\n".encode("utf8"), "Witch")


                #*********DAY TIME********
                ti.sleep(1)
                broadcast_message(f"The sun is rising...\n".encode("utf8"))
                ti.sleep(1)
                broadcast_message(f"The entire village is waking up...\n".encode("utf8"))

                deadPlayers=[]
                killWerewolf=""
                killWitch=""
                for role in roles:
                    if role.strRole=="Werewolf":
                        killWerewolf=role.personEatten
                        role.personEatten=""

                for role in roles:
                    if role.strRole=="Witch":
                        if role.poisonedPlayer==killWerewolf:
                            killWitch=""
                        else:
                            killWitch=role.poisonedPlayer
                        role.poisonedPlayer=""
                            

                if killWerewolf!="":
                    deadPlayers.append(killWerewolf)
                if killWitch!="":
                    deadPlayers.append(killWitch)

                if len(deadPlayers)==0:
                    ti.sleep(1)
                    broadcast_message(f"Nobody is dead tonight !\n".encode("utf8"))
                else:
                    hunterDead=False
                    loverDead=False
                    #we detect who is dead during the night
                    for dead in deadPlayers:
                        for role in roles:
                            if role.name==dead:
                                roleDead=role.strRole
                                if roleDead=="Hunter":
                                    hunterDead=True
                                else:
                                    role.alive=False

                                if role.inLove!="":
                                    loverDead=True
                                    nameLover1=role.name
                                    if roleDead=="Hunter":
                                        hunterDead=True
                                    else:
                                        role.alive=False
                                print(dead)
                                print(playersAlive) 
                                playersAlive.remove(dead)
                                ti.sleep(1)
                                broadcast_message(f"*{dead}* is dead tonight ! He was a {roleDead} !\n".encode("utf8"))
                                break
                        
                    if loverDead:
                        for role in roles:
                            if role.name==nameLover1:
                                nameLover2=role.inLove
                                roleLover2=role.strRole


                        ti.sleep(1)
                        broadcast_message(f"*{nameLover1}* was in love with *{nameLover2}*. *{nameLover2}* dies from crying as well.\n".encode("utf8"))
                        

                        for role in roles:
                            if role.name==nameLover2:
                                playersAlive.remove(nameLover2)
                                nameLover2Role = role.strRole
                                broadcast_message(f"*{nameLover2}* was a {nameLover2Role}.\n".encode("utf8"))
                                if role.strRole=="Hunter":

                                    hunterDead=True
                                else:
                                    role.alive=False

                    #check if dead player was a hunter
                    if hunterDead:
                        ti.sleep(1)
                        broadcast_message(f"The hunter will shoot at someone before dying !\n".encode("utf8"))
                        turn="Hunter"
                        

                    if turn=="Hunter":
                        for role in roles:
                            if role.strRole=="Hunter":
                                hunter=role
                                break
                        ti.sleep(1)
                        target_message_role(f"You need to shoot at someone by using !shoot <idPlayer> (check !playerAlive to see IDs).\n".encode("utf8"), "Hunter")
                        ti.sleep(1)
                        target_message_role(f"You have {time_hunter} seconds to choose !\n".encode("utf8"), "Hunter")
                        t1=ti.time()
                        t2=ti.time()
                        while( (t2-t1)<=time_hunter and hunter.playerShot==""):
                            t2=ti.time()
                            indexHunter=roles.index(hunter)
                            hunter=roles[indexHunter]

                        if((t2-t1)>time_hunter):
                            turn=""
                            target_message_role(f"You ran out of time !\n".encode("utf8"), "Hunter")
                            random1 = random.randint(0, len(playersAlive)-1)
                            shot=playersAlive[random1]
                            while(shot==hunter.name):
                                random1 = random.randint(0, len(playersAlive)-1)
                                shot=playersAlive[random1]
                            shoot(shot)
                        indexHunter=roles.index(hunter)
                        hunter=roles[indexHunter]

                        rolePlayerShot = ""
                        for role in roles:
                            if role.name == hunter.playerShot:
                                rolePlayerShot = role.strRole

                        ti.sleep(1)
                        broadcast_message(f"The hunter shot at *{hunter.playerShot}*, he's dead !\n".encode("utf8"))
                        broadcast_message(f"*{hunter.playerShot}* was a {rolePlayerShot}\n".encode("utf8"))
                        rolePlayerShot
                        playersAlive.remove(hunter.playerShot)
                        
                        loverDie=""
                        for role in roles:
                            if hunter.playerShot==role.name:
                                if role.inLove!="":
                                    loverDie=role.inLove
                                    role.alive=False
                                else:
                                    role.alive=False
                                   
                                    
                        if loverDie!="":
                            for role in roles:
                                if role.name==loverDie:
                                    loverDieRole = role.strRole
                                    ti.sleep(1)
                                    broadcast_message(f"*{hunter.playerShot}* was in love with *{loverDie}*. *{loverDie}* dies from crying as well.\n".encode("utf8"))
                                    broadcast_message(f"*{loverDie}* was a {loverDieRole}\n".encode("utf8"))
                                    role.alive=False
                                    
                        for role in roles:
                            if role.strRole=="Hunter":
                                role.playerShot=""
                                role.alive=False
                       

                # Detect victory
                winner = victory()
                if winner == 1: # amour 2 werewolf #3 villa
                    broadcast_message(f"The lovers won this game!!\n".encode("utf8"))
                    game_started = False
                elif winner == 2:
                    broadcast_message(f"The werewolves won this game!!\n".encode("utf8"))
                    game_started = False
                elif winner == 3:
                    broadcast_message(f"The village won this game!!\n".encode("utf8"))
                    game_started = False

                if winner == 0:
                    turn="Villager"
                    ti.sleep(1)
                    broadcast_message(f"It's debate time !\n".encode("utf8"))
                    ti.sleep(1)
                    broadcast_message(f"You can vote to kill someone today by using !vote <idPlayer> (check !playerAlive to see IDs).\n".encode("utf8"))
                    ti.sleep(1)
                    broadcast_message(f"You have {time_debat} seconds to choose !\n".encode("utf8"))
                    t1=ti.time()
                    t2=ti.time()
                    while((t2-t1)<=time_debat):
                        t2=ti.time()

                    if((t2-t1)>time_debat):
                        turn=""
                        broadcast_message(f"Time over !\n".encode("utf8"))
                        playersVoted={}
                        for player in playersAlive:
                            playersVoted[player]=0

                        for role in roles:
                            if role.vote!="":
                                playersVoted[role.vote]+=1
                                role.vote=""
                        suspect=""
                        maxVote=max(playersVoted.values())
                        if maxVote>0:
                            playerAtMax=0
                            for player in playersVoted:
                                if playersVoted[player]==maxVote:
                                    playerAtMax+=1
                                    playerTarget=player

                            if playerAtMax==1:
                                suspect=playerTarget
                                ti.sleep(1)
                                broadcast_message(f"The player *{playerTarget}* is the designed suspect of the day, he gets executed in public !\n".encode("utf8"))
                            else:
                                ti.sleep(1)
                                broadcast_message(f"There is not an absolute majority in the votes, nobody will die today...\n".encode("utf8"))
                        else:
                            ti.sleep(1)
                            broadcast_message(f"Nobody has been voted today, nobody will die...\n".encode("utf8"))

                    #we manage to kill the suspect and do other things if he's a lover or a hunter
                    if suspect!="":
                        hunterDead=False
                        loverDead=False
                        for role in roles:
                            if role.name==suspect:
                                roleDead=role.strRole
                                if roleDead=="Hunter":
                                    hunterDead=True
                                else:
                                    role.alive=False
                                if role.inLove!="":
                                    loverDead=True
                                    nameLover1=role.name
                                    if roleDead=="Hunter":
                                        hunterDead=True
                                    else:
                                        role.alive=False
                                playersAlive.remove(suspect)
                                ti.sleep(1)
                                broadcast_message(f"*{suspect}* is dead today ! He was a {roleDead} !*\n".encode("utf8"))
                                break

                        if loverDead:
                            for role in roles:
                                if role.name==nameLover1:
                                    nameLover2=role.inLove

                            ti.sleep(1)
                            broadcast_message(f"*{nameLover1}* was in love with *{nameLover2}*. *{nameLover2}* dies from crying as well.\n".encode("utf8"))
                            for role in roles:
                                if role.name==nameLover2:
                                    playersAlive.remove(nameLover2)
                                    nameLover2Role = role.strRole
                                    broadcast_message(f"*{nameLover2}* was a {nameLover2Role}.\n".encode("utf8"))
                                    if role.strRole=="Hunter":
                                        hunterDead=True
                                    else:
                                        role.alive=False

                        if hunterDead:
                            ti.sleep(1)
                            broadcast_message(f"The hunter will shoot at someone before dying !\n".encode("utf8"))
                            turn="Hunter"

                        if turn=="Hunter":
                            for role in roles:
                                if role.strRole=="Hunter":
                                    hunter=role
                                    break
                            ti.sleep(1)
                            target_message_role(f"You need to shoot at someone by using !shoot <idPlayer> (check !playerAlive to see IDs).\n".encode("utf8"), "Hunter")
                            ti.sleep(1)
                            target_message_role(f"You have {time_hunter} seconds to choose !\n".encode("utf8"), "Hunter")
                            t1=ti.time()
                            t2=ti.time()
                            while( (t2-t1)<=time_hunter and hunter.playerShot==""):
                                t2=ti.time()
                                indexHunter=roles.index(hunter)
                                hunter=roles[indexHunter]

                            if((t2-t1)>time_hunter):
                                turn=""
                                target_message_role(f"You ran out of time !\n".encode("utf8"), "Hunter")
                                random1 = random.randint(0, len(playersAlive)-1)
                                shot=playersAlive[random1]
                                while(shot==hunter.name):
                                    random1 = random.randint(0, len(playersAlive)-1)
                                    shot=playersAlive[random1]
                                shoot(shot)
                            indexHunter=roles.index(hunter)
                            hunter=roles[indexHunter]

                            playerShotRole = ""
                            for role in roles:
                                if role.name == hunter.playerShot:
                                    playerShotRole = role.strRole

                            ti.sleep(1)
                            broadcast_message(f"The hunter shot at *{hunter.playerShot}*, he's dead !\n".encode("utf8"))
                            broadcast_message(f"*{hunter.playerShot}* was a {playerShotRole}\n".encode("utf8"))
                            playersAlive.remove(hunter.playerShot)

                            loverDie=""
                            for role in roles:
                                if hunter.playerShot==role.name:
                                    if role.inLove!="":
                                        loverDie=role.inLove
                                        role.alive=False
                                    else:
                                        role.alive=False
                                    
                                        
                            if loverDie!="":
                                for role in roles:
                                    if role.name==loverDie:
                                        playersAlive.remove(loverDie)
                                        loverDieRole = role.strRole
                                        ti.sleep(1)
                                        broadcast_message(f"*{hunter.playerShot}* was in love with *{loverDie}*. *{loverDie}* dies from crying as well.\n".encode("utf8"))
                                        broadcast_message(f"*{loverDie}* was a {loverDieRole}\n".encode("utf8"))
                                        role.alive=False

                                        
                            for role in roles:
                                if role.strRole=="Hunter":
                                    role.playerShot=""
                                    role.alive=False


                        winner = victory()
                        if winner == 1: # amour 2 werewolf #3 villa
                            broadcast_message(f"The lovers won this game!!\n".encode("utf8"))
                            game_started = False
                        elif winner == 2:
                            broadcast_message(f"The werewolves won this game!!\n".encode("utf8"))
                            game_started = False
                        elif winner == 3:
                            broadcast_message(f"The village won this game!!\n".encode("utf8"))
                            game_started = False
                        

'''********************************************
*******************TCP PART********************
***********************************************'''
# This makes the server listen to new connections
s.listen(1)
print(f"\nListening for connections on {host}:{UDP_PORT}...")
print(f"Listening for connections on {host}:{TCP_PORT}...\n")

# Send a message to a particular client (message must be encoded)
def target_message_client(client, message):
    client.send(message)


# Send a message to a particular role (message must be encoded and role a string of the role)
def target_message_role(message, roleTarget):
    if roleTarget=="Hunter":
        for role in roles:
            if role.strRole=="Hunter":
                nameClient = role.name
                indexName = nicknames.index(nameClient)
                client = clients[indexName]
                target_message_client(client, message)
    elif roleTarget=="Seer":
        for role in roles:
            if role.strRole=="Seer":
                nameClient = role.name
                indexName = nicknames.index(nameClient)
                client = clients[indexName]
                target_message_client(client, message)
    elif roleTarget=="Werewolf":
        for role in roles:
            if role.strRole=="Werewolf":
                nameClient = role.name
                indexName = nicknames.index(nameClient)
                client = clients[indexName]
                target_message_client(client, message)
    elif roleTarget=="Witch":
        for role in roles:
            if role.strRole=="Witch":
                nameClient = role.name
                indexName = nicknames.index(nameClient)
                client = clients[indexName]
                target_message_client(client, message)
    elif roleTarget=="Cupid":
        for role in roles:
            if role.strRole=="Cupid":
                nameClient = role.name
                indexName = nicknames.index(nameClient)
                client = clients[indexName]
                target_message_client(client, message)

# Send a message to every connected clients (message must be encoded)
def broadcast_message(message):
    for client in clients:
        client.send(message)


# Remove a client from the game
def remove_client(client, address):
    global admin
    # we check if the client was already connected to the chat or not,
    # if yes we remove him and alert others from disconnection
    if client in clients:
        index = clients.index(client)
        nickname = nicknames[index]

        for role in roles:
            if role.name==nickname:
                rolePlayer=role.strRole
                if nickname in playersAlive:
                    playersAlive.remove(nickname)
                    role.alive=False
                    broadcast_message(f"{nickname} has disconnected. He was a {rolePlayer}.\n".encode("utf8"))
        clients.remove(client)

        #management of the new admin if the admin leaves
        if len(clients)==0:
            admin = None
        elif len(clients)>0 and admin==client:
            admin=clients[0]
            nickNewAdmin=nicknames[1]
            print(f"{nickNewAdmin} becomes the new administrator of the game.")
            broadcast_message(f"{nickNewAdmin} becomes the new administrator of the game.\n".encode("utf8"))

        print(f"{nickname} left the chat !")
        broadcast_message(f"{nickname} left the chat !\n".encode("utf8"))
        nicknames.remove(nickname)
    print(f"Connection lost with a client: {str(address)}.")
    client.close()


# Handle the messages coming from the differents clients
def handle(client, address):
    global admin
    nicknameGiven = False
    while True:
        try:
            # asking for the name of the client
            if not nicknameGiven:
                target_message_client(client, "Please enter a username :\n".encode("utf8"))
                nickname = client.recv(1024).decode("utf8")
                if game_started:
                    target_message_client(client, "This game is already playing!\n".encode("utf8"))
                    client.close()
                elif len(clients) == nb_max_players:
                    target_message_client(client, "This game is full!\n".encode("utf8"))
                    client.close()
                else:
                    nicknames.append(nickname)
                    clients.append(client)

                    print(f"{nickname} joined the chat !")
                    target_message_client(client, "Connected to the server!\n".encode("utf8"))
                    broadcast_message(f"{nickname} joined the chat !\n".encode("utf8"))

                    if admin is None:
                        admin = client
                        target_message_client(client, "You are the administrator of the game !\n".encode("utf8"))
                    
                    nicknameGiven = True

            # name is given, asking for messages to chat
            else:
                message = client.recv(1024)
                containMessage = message.decode("utf8").split(": ")[1]
                indexClient = clients.index(client)
                nicknameClient = nicknames[indexClient]

                # We check if the message is a command or not
                # here it means it's a command
                if len(message) > 0 and containMessage.startswith("!"):
                    print("Command coming from", nicknameClient)
                    cmdhandler(containMessage[1:], client)
                # here it's just a simple message
                else:
                    msg=message.decode("utf8")
                    msg=msg+"\n"
                    message=msg.encode("utf8")

                    #manage the message during the started game
                    if game_started:
                        #we get the role of the current client
                        for role in roles:
                            if role.name==nicknameClient:
                                roleClient=role.strRole
                                roleC=role
                        #we check if the current client is alive or not
                        #if he's alive, we manage his message. Otherwise, we just deny him from talking
                        if roleC.alive:
                            # if the turn of the game is a certain role, we allow or not to talk with other people of the same role
                            if turn=="Werewolf":
                                if roleClient=="Werewolf":
                                    target_message_role(message, "Werewolf")
                                else:
                                    target_message_client(client, "You are sleeping, You can't talk to others !\n".encode("utf8"))
                            elif turn=="Seer":
                                if roleClient=="Seer":
                                    target_message_client(client, "You are the only seer of the game, you can't talk to anyone for the moment !\n".encode("utf8"))
                                else:
                                    target_message_client(client, "You are sleeping, You can't talk to others !\n".encode("utf8"))
                            elif turn=="Witch":
                                if roleClient=="Witch":
                                    target_message_client(client, "You are the only witch of the game, you can't talk to anyone for the moment !\n".encode("utf8"))
                                else:
                                    target_message_client(client, "You are sleeping, You can't talk to others !\n".encode("utf8"))
                            elif turn=="Cupid":
                                if roleClient=="Cupid":
                                    target_message_client(client, "You are the only cupid of the game, you can't talk to anyone for the moment !\n".encode("utf8"))
                                else:
                                    target_message_client(client, "You are sleeping, You can't talk to others !\n".encode("utf8"))
                            elif turn=="Hunter":
                                if roleClient=="Seer":
                                    target_message_client(client, "You are dying, you can't talk, you can only shoot at someone !\n".encode("utf8"))
                                else:
                                    target_message_client(client, "You are sleeping, You can't talk to others !\n".encode("utf8"))
                            elif turn=="Villager":
                                broadcast_message(message)
                            else:
                                target_message_client(client, "You are sleeping, You can't talk to others !\n".encode("utf8"))
                                
                        else:
                            target_message_client(client, "You are dead, deads don't talk !\n".encode("utf8"))
                    
                    # game isn't started, we can talk as we want
                    elif not game_started:
                        broadcast_message(message)
                

        #client has disconnected, we remove him
        except:
            remove_client(client, address)
            break


# TCP function used to listen connection from clients and connect them to the server
def tcp():
    global game_started
    global nb_max_players

    while True:
        client, address = s.accept()

        if game_started:
            target_message_client(client, "This game is already playing!\n".encode("utf8"))
            client.close()
        elif len(clients) == nb_max_players:
            target_message_client(client, "This game is full!\n".encode("utf8"))
            client.close()
        else:
            print(f"Connected with {str(address)}")


            thread = threading.Thread(
                target=handle,
                args=(
                    client,
                    address,
                ),
            )
            thread.start()


'''********************************************
*******************UDP PART********************
***********************************************'''

# UDP function used to give to clients the fact that we are a werewolf server
def udp():
    while True:
        receivedMessage = udp_server_socket.recvfrom(1024)

        if receivedMessage[0] == b"Werewolf?":
            print(f'Answer to {receivedMessage[1][0]}:{receivedMessage[1][1]} \n "I am a werewolf server"\n')
            udp_server_socket.sendto(b"I am a werewolf server", receivedMessage[1])


'''********************************************
*******************Command Handler*************
***********************************************'''

# function to handle the commands starting with a '!'
def cmdhandler(cmd, client):
    cmdarg = cmd.split(" ")
    global time_cupid
    global time_witch
    global time_seer
    global time_hunter
    global time_werewolf
    global time_debat
    global has_witch
    global has_cupid
    global has_seer
    global has_hunter
    global nb_werewolf
    global nb_max_players
    global nb_min_players
    global game_started
    global winner
    print(cmdarg[0])
    # Define if yes or no the host want a witch in his game
    if cmdarg[0] == "setwitch":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setwitch takes 1 parameter : 0 or 1\n".encode("utf8"))
            elif cmdarg[1] == "1":
                target_message_client(client, "You enabled witch in this game.\n".encode("utf8"))
                has_witch = True
            elif cmdarg[1] == "0":
                target_message_client(client, "You disabled witch in this game.\n".encode("utf8"))
                has_witch = False
            else:
                target_message_client(client, "setwitch takes 1 parameter : 0 or 1\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define if yes or no the host want a cupid in his game
    elif cmdarg[0] == "setcupid":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setcupid takes 1 parameter : 0 or 1\n".encode("utf8"))
            elif cmdarg[1] == "1":
                target_message_client(client, "You enabled cupid in this game.\n".encode("utf8"))
                has_cupid = True
            elif cmdarg[1] == "0":
                target_message_client(client, "You disabled cupid in this game.\n".encode("utf8"))
                has_cupid = False
            else:
                target_message_client(client, "setcupid takes 1 parameter : 0 or 1\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define if yes or no the host want a seer in his game
    elif cmdarg[0] == "setseer":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setseer takes 1 parameter : 0 or 1\n".encode("utf8"))
            elif cmdarg[1] == "1":
                target_message_client(client, "You enabled seer in this game.\n".encode("utf8"))
                has_seer = True
            elif cmdarg[1] == "0":
                target_message_client(client, "You disabled seer in this game.\n".encode("utf8"))
                has_seer = False
            else:
                target_message_client(client, "setseer takes 1 parameter : 0 or 1\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define if yes or no the host want a hunter in his game
    elif cmdarg[0] == "sethunter":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "sethunter takes 1 parameter : 0 or 1\n".encode("utf8"))
            elif cmdarg[1] == "1":
                target_message_client(client, "You enabled hunter in this game.\n".encode("utf8"))
                has_hunter = True
            elif cmdarg[1] == "0":
                target_message_client(client, "You disabled hunter in this game.\n".encode("utf8"))
                has_hunter = False
            else:
                target_message_client(client, "sethunter takes 1 parameter : 0 or 1\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how many werewolf the host want in his game
    elif cmdarg[0] == "setwerewolf":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setwerewolf takes 1 parameter : 1 to 3\n".encode("utf8"))
            elif cmdarg[1] in ["1", "2", "3"]:
                target_message_client(client, f"You will now have {cmdarg[1]} in this game.\n".encode("utf8"))
                nb_werewolf = int(cmdarg[1])
            else:
                target_message_client(client, "setwerewolf takes 1 parameter : 1 to 3\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how many players the host want in his game        
    elif cmdarg[0] == "setmaxplayer":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setmaxplayer takes 1 parameter : 8 to 18\n".encode("utf8"))
            elif cmdarg[1] in ["8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18"]:
                if nb_max_players < nb_min_players:
                    target_message_client(
                        client, "The number of minimum player is higher than the maximum player !\n".encode("utf8")
                    )
                nb_max_players = int(cmdarg[1])
            else:
                target_message_client(client, "setmaxplayer takes 1 parameter : 8 to 18\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how many players the host want before starting a game
    elif cmdarg[0] == "setminplayer":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setminplayer takes 1 parameter : 8 to 18\n".encode("utf8"))
            elif cmdarg[1] in ["8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18"]:
                if int(cmdarg[1]) > nb_max_players:
                    target_message_client(
                        client, "The number of minimum player is higher than the maxximum player !\n".encode("utf8")
                    )
                nb_min_players = int(cmdarg[1])
            else:
                target_message_client(client, "setminplayer takes 1 parameter : 8 to 18\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how much time the players will have to debate during the day
    elif cmdarg[0] == "setdebatetime":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setdebatetime take 1 parameter 20 to 300\n".encode("utf8"))
            elif cmdarg[1].isnumeric() and int(cmdarg[1]) >= 20 and int(cmdarg[1]) <= 300:
                target_message_client(client, f"This game will now have {cmdarg[1]} seconds to debate.\n".encode("utf8"))
                time_debat = int(cmdarg[1])
            else:
                target_message_client(client, "setdebatetime takes 1 parameter : 20 to 300\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how much time the werewolves have to choose their target
    elif cmdarg[0] == "setwerewolftime":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setwerewolftime takes 1 parameter : 20 to 300\n".encode("utf8"))
            elif cmdarg[1].isnumeric() and int(cmdarg[1]) >= 20 and int(cmdarg[1]) <= 300:
                target_message_client(client, f"Werewolves will now have {cmdarg[1]} seconds to choose their target.\n".encode("utf8"))
                time_werewolf = int(cmdarg[1])
            else:
                target_message_client(client, "setwerewolftime takes 1 parameter : 20 to 300\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how much time the seer has to choose a person to predict's role
    elif cmdarg[0] == "setseertime":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setseertime takes 1 parameter : 20 to 300\n".encode("utf8"))
            elif cmdarg[1].isnumeric() and int(cmdarg[1]) >= 20 and int(cmdarg[1]) <= 300:
                target_message_client(client, f"The seer will now have {cmdarg[1]} seconds to choose his target.\n".encode("utf8"))
                time_seer = int(cmdarg[1])
            else:
                target_message_client(client, "setseertime takes 1 parameter : 20 to 300\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how much time the witch has to choose if she want to use his potions
    elif cmdarg[0] == "setwitchtime":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setwitchtime takes 1 parameter : 20 to 300\n".encode("utf8"))
            elif cmdarg[1].isnumeric() and int(cmdarg[1]) >= 20 and int(cmdarg[1]) <= 300:
                target_message_client(client, f"The witch will now have {cmdarg[1]} seconds to choose what she want to do.\n".encode("utf8"))
                time_witch = int(cmdarg[1])
            else:
                target_message_client(client, "setwitchtime takes 1 parameter : 20 to 300\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how much time the cupid has to choose lovers
    elif cmdarg[0] == "setcupidtime":
        print(cmdarg)
        print(game_started)
        print(client)
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "setcupidtime take 1 parameter : 20 to 300\n".encode("utf8"))
            elif cmdarg[1].isnumeric() and int(cmdarg[1]) >= 20 and int(cmdarg[1]) <= 300:
                target_message_client(client, f"The cupid will now have {cmdarg[1]} seconds to send love arrows.\n".encode("utf8"))
                time_cupid = int(cmdarg[1])
            else:
                target_message_client(client, "setcupidtime takes 1 parameter : 20 to 300\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Define how much time the hunter has to choose which person he want to shoot
    elif cmdarg[0] == "sethuntertime":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(cmdarg) != 2:
                target_message_client(client, "sethuntertime takes 1 parameter : 20 to 300\n".encode("utf8"))
            elif cmdarg[1].isnumeric() and int(cmdarg[1]) >= 20 and int(cmdarg[1]) <= 300:
                target_message_client(client, f"The hunter will now have {cmdarg[1]} seconds to choose his target.\n".encode("utf8"))
                time_hunter = int(cmdarg[1])
            else:
                target_message_client(client, "sethuntertime takes 1 parameter : 20 to 300\n".encode("utf8"))
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Start the game if there is enough players
    elif cmdarg[0] == "start":
        if client==admin:
            if game_started:
                target_message_client(client, "The game has already started !\n".encode("utf8"))
            elif len(clients) < nb_min_players:
                target_message_client(client, "Not enough players to start the game !\n".encode("utf8"))
            else:
                winner=0
                game_started = True

                for p in clients:
                    target_message_client(p, "You started the game !\n".encode("utf8"))
                distribuer_role()

                
        else:
            target_message_client(client, "You are not allowed to use this command.\n".encode("utf8"))
    # Show the informations about the settings of the game
    elif cmdarg[0] == "info":
        target_message_client(
            client,
            "nb_min_players: {}\nnb_max_players: {}\ntime_debate: {}\ntime_werewolf: {}\
\ntime_seer: {}\ntime_witch: {}\ntime_cupid: {}\ntime_hunter: {}\nhas_cupid: {}\nhas_hunter: {}\nhas_witch: {}\nhas_seer: {}\nnumber of werewolf: {}\ngame started: {}\n".format(
                nb_min_players,
                nb_max_players,
                time_debat,
                time_werewolf,
                time_seer,
                time_witch,
                time_cupid,
                time_hunter,
                has_cupid,
                has_hunter,
                has_witch,
                has_seer,
                nb_werewolf,
                game_started,
            ).encode(
                "utf8"
            ),
        )
    # Show players alive
    elif cmdarg[0] == "playerAlive":
        if not game_started:
            target_message_client(
                client, "The game is not started, you cannot use this command for the moment.\n".encode("utf8")
            )

        else:
            message = ""
            for i in range(0, len(playersAlive)):
                message+=f"[{i}] {playersAlive[i]}\n"

            target_message_client(client, message.encode("utf8"))
    # Show all the commands avalaible
    elif cmdarg[0] == "help":
        adminListCmds = ["start", "setmaxplayer", "setminplayer", "setdebattime", "setwitch", "setwitchtime", "setseer", "setseertime", "setcupid", "setcupidtime", "sethunter", "sethuntertime", "setwerewolf", "setwerewolftime"]
        listCmds = ["help", "info"]
        listGameCmds = ["playerAlive", "vote", "sendArrows", "msgLover", "usePoisonPotion", "useHealingPotion", "predict", "vote", "shoot"]

        if client==admin:
            adminCmdsMessage = "Admin commands: "
            l = len(adminListCmds)
            for i in range(0, l):
                adminCmdsMessage += f"{adminListCmds[i]}"
                if i < l-1:
                    adminCmdsMessage += ", "
            
            adminCmdsMessage += "\n"
            target_message_client(client, adminCmdsMessage.encode("utf8"))

        baseCmdsMessage = "Base commands: "
        l = len(listCmds)
        for i in range(0, l):
            baseCmdsMessage += f"{listCmds[i]}"
            if i < l-1:
                baseCmdsMessage += ", "
        
        baseCmdsMessage += "\n"
        target_message_client(client, baseCmdsMessage.encode("utf8"))

        gameCmdsMessage = "In game commands: "
        l = len(listGameCmds)
        for i in range(0, l):
            gameCmdsMessage += f"{listGameCmds[i]}"
            if i < l-1:
                gameCmdsMessage += ", "
        
        gameCmdsMessage += "\n"
        target_message_client(client, gameCmdsMessage.encode("utf8"))
    # Send a message to his lover if you have one
    elif cmdarg[0] == "msgLover":
        if game_started:
            index = clients.index(client)
            clientName = nicknames[index]

            for role in roles:
                if role.name == clientName:
                    roleClient = role
                    break

            if roleClient.alive:
                index = clients.index(client)
                clientName = nicknames[index]
                    
                for role in roles:
                    if role.name == clientName:
                        roleClient = role
                        break

                if roleClient.inLove == "":
                        target_message_client(client, "You need to be a lover to use this command.\n".encode("utf8"))
                else:
                    if cmdarg[1] is not None:
                        index2 = nicknames.index(roleClient.inLove)
                        client2 = clients[index2]

                        target_message_client(client2, f"[<3] {clientName} : {cmdarg[1]}\n".encode("utf8"))
                        target_message_client(client, f"[<3] {clientName} : {cmdarg[1]}\n".encode("utf8"))
                    else:
                        target_message_client(client, "You need to enter a message !\n".encode("utf8"))
            else:
                target_message_client(client, "You're dead you can't do anything !\n".encode("utf8"))
        else:
            target_message_client(client, "The game is not currently started.\n".encode("utf8"))
    # Allows to choose which persons you want to make in love (If you are a Cupid and still have arrows)
    elif cmdarg[0] == "sendArrows":
        if game_started:
            index = clients.index(client)
            clientName = nicknames[index]

            for role in roles:
                if role.name == clientName:
                    roleClient = role
                    break

            if roleClient.strRole == "Cupid":
                if roleClient.alive:
                    if roleClient.arrowsSent:
                        target_message_client(client, "Your quiver is empty !\n".encode("utf8"))
                    else:
                        if turn == "Cupid":
                            if len(cmdarg) == 3:
                                cLen = len(playersAlive)-1
                                if (cmdarg[1].isnumeric() and cmdarg[2].isnumeric()):
                                    if (int(cmdarg[1]) >= 0 and int(cmdarg[1]) <= cLen) and (int(cmdarg[2]) >= 0 and int(cmdarg[2]) <= cLen):
                                        lover1 = playersAlive[int(cmdarg[1])]
                                        lover2 = playersAlive[int(cmdarg[2])]

                                        chooseLovers(lover1, lover2)    
                                    else:
                                        target_message_client(client, f"The chosen IDs needs to be between 0 and {cLen}.\n".encode("utf8"))
                                else:
                                    target_message_client(client, "The parameters needs to be IDs of players (!playerAlive).\n".encode("utf8"))  
                            else:
                                target_message_client(client, "You need 2 parameters for this command to work.\n".encode("utf8"))  
                        else:
                            target_message_client(client, "You can't use this action, it's not your turn !\n".encode("utf8"))
                else:
                    target_message_client(client, "You're dead you can't do anything !\n".encode("utf8"))
            else:
                target_message_client(client, "You are not cupid, you can't use this action.\n".encode("utf8"))
        else:
            target_message_client(client, "The game is not currently started.\n".encode("utf8"))
    # Allows you to choose if you want to save the life of the werewolf target (If you are a witch and still have healing potion)
    elif cmdarg[0] == "useHealingPotion":
        if game_started:
            index = clients.index(client)
            clientName = nicknames[index]

            for role in roles:
                if role.name == clientName:
                    roleClient = role
                    break
            if roleClient.strRole == "Witch":
                if roleClient.alive:
                    if turn == "Witch":
                        if not roleClient.hasHealingPotion:
                            target_message_client(client, "You already used your healing potion !\n".encode("utf8"))
                        else:
                            for role in roles:
                                if role.strRole=="Werewolf":
                                    personToSave=role.personEatten
                                    break

                            if personToSave=="":
                                target_message_client(client, "Don't waste your potion, you have nobody to save this night !\n".encode("utf8"))
                            else:
                                target_message_client(client, f"You're resurrecting *{personToSave}* !\n".encode("utf8"))
                                for role in roles:
                                    if role.strRole=="Werewolf":
                                        role.personEatten=""
                                roleClient.hasHealingPotion=False
                    else:
                        target_message_client(client, "You can't use this action, it's not your turn !\n".encode("utf8"))
                else:
                    target_message_client(client, "You're dead you can't do anything !\n".encode("utf8"))
            else:
                target_message_client(client, "You are not a witch, you can't use this action !\n".encode("utf8"))
        else:
            target_message_client(client, "The game is not currently started.\n".encode("utf8"))
    # Allows you to choose on which person you want to throw ur poison potion on someone (If you are a witch and still have poison potion)
    elif cmdarg[0] == "usePoisonPotion":
        if game_started:
            index = clients.index(client)
            clientName = nicknames[index]

            for role in roles:
                if role.name == clientName:
                    roleClient = role
                    break

            if roleClient.strRole == "Witch":
                if roleClient.alive:
                    if turn == "Witch":
                        if not roleClient.hasPoisonPotion:
                            target_message_client(client, "You already used your poison potion !\n".encode("utf8"))
                        else:
                            if len(cmdarg) == 2:
                                cLen = len(playersAlive)-1
                                if cmdarg[1].isnumeric():
                                    if int(cmdarg[1]) >= 0 and int(cmdarg[1]) <= cLen:
                                        targetName = playersAlive[int(cmdarg[1])]
                                                                           
                                        if targetName==roleClient.name:
                                            target_message_client(client, f"You can't use the poison potion on yourself !\n".encode("utf8"))
                                        else:
                                            target_message_client(client, f"You poisoned *{targetName}*, he will die at the start of the day !\n".encode("utf8"))
                                            roleClient.hasPoisonPotion = False
                                            roleClient.poisonedPlayer = targetName
                                    else:
                                        target_message_client(client, f"The chosen ID needs to be between 0 and {cLen}.\n".encode("utf8"))
                                else:
                                    target_message_client(client, "The parameter of this command needs to be an ID of a player (!playerAlive).\n".encode("utf8"))  
                            else:
                                target_message_client(client, "You need 1 parameter for this command to work.\n".encode("utf8"))  
                    else:
                        target_message_client(client, "You can't use this action, it's not your turn !\n".encode("utf8"))
                else:
                    target_message_client(client, "You're dead you can't do anything !\n".encode("utf8"))
            else:
                target_message_client(client, "You are not a witch, you can't use this action !\n".encode("utf8"))
        else:
            target_message_client(client, "The game is not currently started.\n".encode("utf8"))
    # Allows you to choose who to kill in the village during the day, in a democratical vote
    elif cmdarg[0] == "vote":
        if game_started:
            index = clients.index(client)
            clientName = nicknames[index]
            for role in roles:
                if role.name == clientName:
                    roleClient = role
                    break
            if roleClient.alive:
                #vote for the debate of the day
                if turn=="Villager":
                    if len(cmdarg) == 2:
                        cLen = len(playersAlive)-1
                        if cmdarg[1].isnumeric():
                            if int(cmdarg[1]) >= 0 and int(cmdarg[1]) <= cLen:
                                targetName = playersAlive[int(cmdarg[1])]

                                if targetName!=roleClient.vote:
                                    broadcast_message(f"*{roleClient.name}* voted for *{targetName}* !\n".encode("utf8"))
                                    roleClient.vote=targetName
                                else:
                                    target_message_client(client, f"Your vote is already on *{targetName}* !\n".encode("utf8"))
                            else:
                                target_message_client(client, f"The chosen ID needs to be between 0 and {cLen}.\n".encode("utf8"))
                        else:
                            target_message_client(client, "The parameter of this command needs to be an ID of a player (!playerAlive).\n".encode("utf8"))  

                    else:
                        target_message_client(client, "You need 1 parameter for this command to work.\n".encode("utf8"))

                #vote for werewolves
                elif turn=="Werewolf":
                    if roleClient.strRole=="Werewolf":
                        if len(cmdarg) == 2:
                            cLen = len(playersAlive)-1
                            if cmdarg[1].isnumeric():
                                if int(cmdarg[1]) >= 0 and int(cmdarg[1]) <= cLen:
                                    targetName = playersAlive[int(cmdarg[1])]

                                    if targetName!=roleClient.vote:
                                        msg=f"*{roleClient.name}* voted for *{targetName}* !\n".encode("utf8")
                                        target_message_role(msg, "Werewolf")
                                        roleClient.vote=targetName
                                    else:
                                        target_message_client(client, f"Your vote is already on *{targetName}* !\n".encode("utf8"))
                                else:
                                    target_message_client(client, f"The chosen ID needs to be between 0 and {cLen}.\n".encode("utf8"))
                            else:
                                target_message_client(client, "The parameter of this command needs to be an ID of a player (!playerAlive).\n".encode("utf8"))  
                        else:
                            target_message_client(client, "You need 1 parameter for this command to work.\n".encode("utf8"))
                    else:
                        target_message_client(client, "You are not a werewolf, you can't use this action !\n".encode("utf8"))
                else:
                    target_message_client(client, "You can't vote for the moment.\n".encode("utf8"))
            else:
               target_message_client(client, "You're dead you can't do anything !\n".encode("utf8"))
        else:
            target_message_client(client, "The game is not currently started.\n".encode("utf8"))
    # Allows you to choose who you want to predict the role (If you are a seer)
    elif cmdarg[0] == "predict":
        if game_started:
            index = clients.index(client)
            clientName = nicknames[index]
            for role in roles:
                if role.name == clientName:
                    roleClient = role
                    break
            if roleClient.strRole=="Seer":
                if roleClient.alive:
                    if turn == "Seer":
                        if roleClient.personGuessed=="":
                            if len(cmdarg) == 2:
                                cLen = len(playersAlive)-1
                                if cmdarg[1].isnumeric():
                                    if int(cmdarg[1]) >= 0 and int(cmdarg[1]) <= cLen:
                                        targetName = playersAlive[int(cmdarg[1])]
                                        if targetName==roleClient.name:
                                            target_message_client(client, f"You can't predict your own role !\n".encode("utf8"))
                                        else:
                                            predict(targetName)
                                    else:
                                        target_message_client(client, f"The chosen ID needs to be between 0 and {cLen}.\n".encode("utf8"))
                                else:
                                    target_message_client(client, "The parameter of this command needs to be an ID of a player (!playerAlive).\n".encode("utf8"))  
                            else:
                                target_message_client(client, "You need 1 parameter for this command to work.\n".encode("utf8"))
                        else:
                            target_message_client(client, "You already predicted tonight !\n".encode("utf8"))
                    else:
                        target_message_client(client, "You can't use this action, it's not your turn !\n".encode("utf8"))
                else:
                    target_message_client(client, "You're dead you can't do anything !\n".encode("utf8"))
            else:
                target_message_client(client, "You are not a seer, you can't use this action !\n".encode("utf8"))
        else:
            target_message_client(client, "The game is not currently started.\n".encode("utf8"))
    # Allows you to choose who you want to shoot down (If you are a dying hunter)
    elif cmdarg[0] == "shoot":
        if game_started:
            index = clients.index(client)
            clientName = nicknames[index]
            for role in roles:
                if role.name == clientName:
                    roleClient = role
                    break
            if roleClient.strRole=="Hunter":
                if roleClient.alive:
                    if turn == "Hunter":
                        if roleClient.playerShot=="":
                            if len(cmdarg) == 2:
                                cLen = len(playersAlive)-1
                                if cmdarg[1].isnumeric():
                                    if int(cmdarg[1]) >= 0 and int(cmdarg[1]) <= cLen:
                                        targetName = playersAlive[int(cmdarg[1])]
                                        if targetName==roleClient.name:
                                            target_message_client(client, f"You can't shoot at yourself !\n".encode("utf8"))
                                        else:
                                            shoot(targetName)
                                    else:
                                        target_message_client(client, f"The chosen ID need to be between 0 and {cLen}.\n".encode("utf8"))
                                else:
                                    target_message_client(client, "The parameter of this command needs to be an ID of a player (!playerAlive).\n".encode("utf8"))  
                            else:
                                target_message_client(client, "You need 1 parameter for this command to work.\n".encode("utf8"))
                        else:
                            target_message_client(client, "You already shot at someone !\n".encode("utf8"))
                    else:
                        target_message_client(client, "You can't use that action for the moment !\n".encode("utf8"))
                else:
                    target_message_client(client, "You're dead you can't do anything !\n".encode("utf8"))
            else:
                target_message_client(client, "You are not a hunter, you can't use this action !\n".encode("utf8"))
        else:
            target_message_client(client, "The game is not currently started.\n".encode("utf8"))
    else:
        target_message_client(client, "Unknown command. Type !help for existing commands.\n".encode("utf8"))



'''*******************************
***************Main Calls*********
**********************************'''

udp_thread = threading.Thread(target = udp, args = ())
udp_thread.daemon = True
udp_thread.start()

game_thread = threading.Thread(target = game, args = ())
game_thread.daemon=True
game_thread.start()

tcp_thread = threading.Thread(target = tcp, args = ())
tcp_thread.start()

