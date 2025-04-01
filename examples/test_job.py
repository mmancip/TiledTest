#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys,os,time
import code
import argparse
import re, datetime
import json

if (os.path.exists("config.tar")):
    os.system("tar xf config.tar")

SITE_config='./site_config.ini'
CASE_config="./case_config.ini"

actions_file=open("/home/myuser/actions.json",'r')
tiles_actions=json.load(actions_file)
#launch_actions()

config = configparser.ConfigParser()
config.optionxform = str

config.read(SITE_config)

TILEDOCKERS_path=config['SITE']['TILEDOCKER_DIR']
DOCKERSPACE_DIR=config['SITE']['DOCKERSPACE_DIR']
#NOVNC_URL=config['SITE']['NOVNC_URL']
GPU_FILE=config['SITE']['GPU_FILE']

SSH_FRONTEND=config['SITE']['SSH_FRONTEND']
SSH_LOGIN=config['SITE']['SSH_LOGIN']
SSH_IP=config['SITE']['SSH_IP']
init_IP=config['SITE']['init_IP']

config.read(CASE_config)

CASE=config['CASE']['CASE_NAME']
App="glxgears"

NUM_DOCKERS=int(config['CASE']['NUM_DOCKERS'])

CASE_DOCKER_PATH=config['CASE']['CASE_DOCKER_PATH']

network=config['CASE']['network']
nethost=config['CASE']['nethost']
domain=config['CASE']['domain']

OPTIONssh=config['CASE']['OPTIONssh']
# TODO NO NEED
SOCKETdomain=config['CASE']['SOCKETdomain']

DOCKER_NAME=config['CASE']['DOCKER_NAME']

OPTIONS=config['CASE']['OPTIONS'].replace("$","").replace('"','')
print("\nOPTIONS from CASE_CONFIG : "+OPTIONS)
OPTIONS=OPTIONS.replace("JOBPath",JOBPath)
OPTIONS=OPTIONS.replace('{','|{').replace('}','}|').split('|')
OPTIONS="".join(list(map( replaceconf,OPTIONS)))
print("OPTIONS after replacement : "+OPTIONS)


CreateTS='create TS='+TileSet+' Nb='+str(NUM_DOCKERS)

client.send_server(CreateTS)

COMMANDStop="echo 'JobID is not defined.'"

# Global commands
# Execute on each/a set of tiles
ExecuteTS='execute TS='+TileSet+" "
# Launch a command on the frontend
LaunchTS='launch TS='+TileSet+" "+JOBPath+' '

# Build TEST dir
# client.send_server(LaunchTS+" mkdir "+CASE)
# print("Out of mkdir %s : %s" % (CASE, str(client.get_OK())))
#CASEdir=os.path.join(JOBPath,CASE)
#LaunchTSC='launch TS='+TileSet+" "+CASEdir+' '

# get TiledTest package from Github
COMMAND_GIT="git clone -q https://github.com/mmancip/TiledTest.git"
print("command_git : "+COMMAND_GIT)
os.system(COMMAND_GIT)
# Untar Test package
# os.system("tar xfz TiledTest.tgz")

# command='launch TS='+TileSet+" "+TiledVizPath+" cp -p build_qr "+os.path.join(JOBPath,'..')
# print("cp build_qr : %s" % (command))
# client.send_server(command)
# print("Out of cp build_qr : %s" % (str(client.get_OK())))

# Send CASE and SITE files
try:
    client.send_server(LaunchTS+' chmod og-rxw '+JOBPath)
    print("Out of chmod JOBPath : "+ str(client.get_OK()))

    send_file_server(client,TileSet,".", CASE_config, JOBPath)
    CASE_config=os.path.join(JOBPath,CASE_config)
    send_file_server(client,TileSet,".", SITE_config, JOBPath)
    SITE_config=os.path.join(JOBPath,os.path.basename(SITE_config))
    send_file_server(client,TileSet,".", GPU_FILE, JOBPath)

except:
    print("Error sending files !")
    traceback.print_exc(file=sys.stdout)
    try:
        code.interact(banner="Try sending files by yourself :",local=dict(globals(), **locals()))
    except SystemExit:
        pass



COMMAND_TiledTest=LaunchTS+COMMAND_GIT
client.send_server(COMMAND_TiledTest)
print("Out of git clone TiledTest : "+ str(client.get_OK()))

COMMAND_copy=LaunchTS+" cp -rp TiledTest/test_client "+\
               "TiledTest/build_nodes_file "+\
               "./"

client.send_server(COMMAND_copy)
print("Out of copy scripts from TiledTest : "+ str(client.get_OK()))

# Launch containers HERE
REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+DOCKERSPACE_DIR+" "+DOCKER_NAME
TiledSet=list(range(NUM_DOCKERS))

print("\nREF_CAS : "+REF_CAS)

COMMANDStop=os.path.join(TILEDOCKERS_path,"stop_dockers")+" "+REF_CAS+" "+os.path.join(JOBPath,GPU_FILE)
print("\n"+COMMANDStop)
sys.stdout.flush()

try:
    stateVM=Run_dockers()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()


# Get password file with right number of lines (NUM_DOCKERS)
out_get=0
try:
    out_get=get_file_client(client,TileSet,JOBPath,"list_dockers_pass",".")
    logging.warning("out get list_dockers_pass : "+str(out_get))
except:
    pass
try:
    count=0
    while( int(out_get) <= 0):
        time.sleep(10)
        os.system('mv list_dockers_pass list_dockers_pass_')
        out_get=get_file_client(client,TileSet,JOBPath,"list_dockers_pass",".")
        logging.warning("out get list_dockers_pass : "+str(out_get))
        count=count+1
        if (count > 10):
            logging.error("Error create list_dockers_pass. Job stopped.")
            kill_all_containers()
            sys.exit(0)
except:
    pass

size=0
try:
    with open('list_dockers_pass') as f:
        size=len([0 for _ in f])
except:
    pass

while(size != NUM_DOCKERS):
    time.sleep(10)
    os.system('mv list_dockers_pass list_dockers_pass_')
    try:
        out_get=get_file_client(client,TileSet,JOBPath,"list_dockers_pass",".")
    except:
        pass
    try:
        with open('list_dockers_pass') as f:
            size=len([0 for _ in f])
    except:
        pass

logging.warning("list_dockers_pass OK %d %d" % (size,NUM_DOCKERS))


try:
    if (stateVM):
        build_nodes_file()
        
        while(os.path.getsize("nodes.json_init") < 50):
            time.sleep(5)
            logging.warning("nodes.json_init to small. Try another build.")
            build_nodes_file()
            if (os.path.getsize("nodes.json_init") < 50):
                logging.error("Something has gone wrong with build_nodes_file 2.")
                kill_all_containers()
            else:
                break

    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()
logging.warning("after build_nodes_json %r" % (stateVM))
#get_file_client(client,TileSet,JOBPath,"nodes.json",".")

try:
    if (stateVM):
        nodes_json_init()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()
logging.warning("after nodes_json_init %r" % (stateVM))

try:
    if (stateVM):
        stateVM=share_ssh_key()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()
logging.warning("after share ssh keys %r" % (stateVM))

time.sleep(2)
# Launch docker tools
if (stateVM):
    all_resize("1920x1080")

logging.warning("Before launch_tunnel.")

try:
    if (stateVM):
        stateVM=launch_tunnel()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    #kill_all_containers()
print("after launch tunnel servers %r" % (stateVM))

try:
    nodesf=open("nodes.json",'r')
    nodes=json.load(nodesf)
    nodesf.close()
except:
    print("nodes.json doesn't exists !")
    print("ls -la")
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    #kill_all_containers()

print("after read nodes.json %r" % (stateVM))

try:
    if (stateVM):
        stateVM=launch_vnc()
except:
    print("Problem when launch vnc !")
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    #kill_all_containers()

print("after launch vnc servers %r" % (stateVM))

def launch_one_client(script='test_client',tileNum=-1,tileId='001'):
    COMMAND=' '+os.path.join(CASE_DOCKER_PATH,script)
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    print("launch command on %s : %s" % (TilesStr,COMMAND))
    CommandTS=ExecuteTS+TilesStr+COMMAND
    client.send_server(CommandTS)        
    client.get_OK()

def launch_client_global(script='test_client'):
    COMMAND=' '+os.path.join(CASE_DOCKER_PATH,script)
    print("launch command on all tiles : %s" % (COMMAND))
    sys.stdout.flush()
    CommandTS=ExecuteTS+COMMAND
    client.send_server(CommandTS)

    client.get_OK()

try:
    if (stateVM):
        launch_client_global(script='test_client')
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)

def next_element(script='test_client',tileNum=-1,tileId='001'):
    COMMAND=' '+os.path.join(CASE_DOCKER_PATH,script)
    COMMANDKill=' killall -9 glxgears'
    if ( tileNum > -1 ):
        tileId=containerId(tileNum+1)
    else:
        tileNum=int(tileId)-1 
    TilesStr=' Tiles=('+tileId+') '
    print("%s Client command : %s" % (TilesStr,COMMAND))

    CommandTSK=ExecuteTS+TilesStr+COMMANDKill
    client.send_server(CommandTSK)
    client.get_OK()
    
    CommandTS=ExecuteTS+TilesStr+COMMAND
    client.send_server(CommandTS)
    client.get_OK()

    nodesf=open("nodes.json",'r')
    nodes=json.load(nodesf)
    nodesf.close()

    import socket
    hostname=socket.gethostname()

    nodes["nodes"][tileNum]["title"]=tileId+" "+hostname
    if ("variable" in nodes["nodes"][tileNum]):
        nodes["nodes"][tileNum]["variable"]="ID-"+tileId+"_"+hostname
    nodes["nodes"][tileNum]["comment"]="New comment for tile "+tileId
    # if ("usersNotes" in nodes["nodes"][tileNum]):
    #     nodes["nodes"][tileNum]["usersNotes"]=re.sub(r'file .*',"New Element host "+hostname,
    #                                                  nodes["nodes"][tileNum]["usersNotes"])
    nodes["nodes"][tileNum]["usersNotes"]="New Element host "+hostname
    nodes["nodes"][tileNum]["tags"]=[]
    nodes["nodes"][tileNum]["tags"].append(TileSet)
    nodes["nodes"][tileNum]["tags"].append("NewElement")

    nodesf=open("nodes.json",'w')
    nodesf.write(json.dumps(nodes))
    nodesf.close()        

    

def init_wmctrl():
    client.send_server(ExecuteTS+' wmctrl -l -G')
    print("Out of wmctrl : "+ str(client.get_OK()))

if (stateVM):
    init_wmctrl()
    
def remove_element(script='paraview_client',tileNum=-1,tileId='001'):
    COMMANDKill=' killall -9 Xvnc'
    if ( tileNum > -1 ):
        tileId=containerId(tileNum+1)
    else:
        tileNum=int(tileId)-1 
    TilesStr=' Tiles=('+tileId+') '
    print("%s VMD command : %s" % (TilesStr,COMMANDKill))

    CommandTSK=ExecuteTS+TilesStr+COMMANDKill
    client.send_server(CommandTSK)
    client.get_OK()

    nodesf=open("nodes.json",'r')
    nodes=json.load(nodesf)
    nodesf.close()

    del nodes["nodes"][tileNum]
    
    nodesf=open("nodes.json",'w')
    nodesf.write(json.dumps(nodes))
    nodesf.close()
        

try:
    if (stateVM):
        clear_vnc_all()
except:
    traceback.print_exc(file=sys.stdout)


def launch_changesize(RESOL="1920x1080",tileNum=-1,tileId='001'):
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    COMMAND=ExecuteTS+TilesStr+' xrandr --fb '+RESOL
    print("call server with : "+COMMAND)
    client.send_server(COMMAND)
    print("server answer is "+str(client.get_OK()))

def launch_smallsize(tileNum=-1,tileId='001'):
    print("Launch launch_changesize smallsize for tile "+str(tileNum))
    launch_changesize(tileNum=tileNum,RESOL="950x420")

def launch_bigsize(tileNum=-1,tileId='001'):
    print("Launch launch_changesize bigsize for tile "+str(tileNum))
    launch_changesize(tileNum=tileNum,RESOL="1920x1200")

def get_windows():
    client.send_server(ExecuteTS+' wmctrl -l -G')
    print("Out of wmctrl : "+ str(client.get_OK()))

if (stateVM):
    get_windows()
sys.stdout.flush()

def fullscreenApp_(windowname=App,tileNum=-1):
    fullscreenApp(windowname=App,tileNum=tileNum)
def move_glxgears(windowname="glxgears",tileNum=-1):
    movewindows(windowname=windowname,wmctrl_option="remove,fullscreen -e 0,+10,+20,400,400",tileNum=tileNum)

        
def toggle_fullscr():
    for i in range(NUM_DOCKERS):
        client.send_server(ExecuteTS+' Tiles=('+containerId(i+1)+') '+
                           '/opt/movewindows glxgears -b toggle,fullscreen')
        client.get_OK()

#isActions=True
launch_actions_and_interact()

try:
    print("isActions: "+str(isActions))
except:
    print("isActions not defined.")

kill_all_containers()

sys.exit(0)

