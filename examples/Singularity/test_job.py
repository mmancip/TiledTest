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

TILEDVIZ_DIR=config['SITE']['TILEDVIZ_DIR']
TILESINGULARITYS_DIR=os.path.join(TILEDVIZ_DIR,"TVConnections/Singularity")
SPACE_DIR=config['SITE']['SPACE_DIR']
#NOVNC_URL=config['SITE']['NOVNC_URL']
GPU_FILE=config['SITE']['GPU_FILE']

SSH_FRONTEND=config['SITE']['SSH_FRONTEND']
SSH_LOGIN=config['SITE']['SSH_LOGIN']
SSH_IP=config['SITE']['SSH_IP']

SSL_PUBLIC=config['SITE']['SSL_PUBLIC']
SSL_PRIVATE=config['SITE']['SSL_PRIVATE']

config.read(CASE_config)

CASE=config['CASE']['CASE_NAME']
App="glxgears"

NUM_DOCKERS=int(config['CASE']['NUM_DOCKERS'])

CASE_DOCKER_PATH=config['CASE']['CASE_DOCKER_PATH']

OPTIONssh=config['CASE']['OPTIONssh']

SINGULARITY_NAME=config['CASE']['SINGULARITY_NAME']

OPTIONS=config['CASE']['OPTIONS'].replace("$","").replace('"','')
print("\nOPTIONS from CASE_CONFIG : "+OPTIONS)
OPTIONS=OPTIONS.replace("JOBPath",JOBPath)
OPTIONS=OPTIONS.replace('{','|{').replace('}','}|').split('|')
OPTIONS="".join(list(map( replaceconf,OPTIONS)))
print("OPTIONS after replacement : "+OPTIONS)


CreateTS='create TS='+TileSet+' Nb='+str(NUM_DOCKERS)

client.send_server(CreateTS)

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
COMMAND_GIT="git clone https://github.com/mmancip/TiledTest.git"
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
    send_file_server(client,TileSet,".", "list_hostsgpu", JOBPath)
    #send_file_server(client,TileSet,".", os.path.join(TILEDVIZ_DIR,"TVConnections/build_wss.py"), JOBPath)

except:
    print("Error sending files !")
    traceback.print_exc(file=sys.stdout)
    try:
        code.interact(banner="Try sending files by yourself :",local=dict(globals(), **locals()))
    except SystemExit:
        pass

# COMMAND_build="cp "+os.path.join(TILEDVIZ_DIR,"TVConnections/build_wss.py")+" "+JOBPath
# COMMAND_CP=LaunchTS+COMMAND_build
# client.send_server(COMMAND_CP)
# print("Out of cp build_wss : "+ str(client.get_OK()))


COMMAND_TiledTest=LaunchTS+COMMAND_GIT
client.send_server(COMMAND_TiledTest)
print("Out of git clone TiledTest : "+ str(client.get_OK()))

COMMAND_copy=LaunchTS+" cp -rp TiledTest/test_client "+\
               "TiledTest/build_nodes_file "+\
               "./"

client.send_server(COMMAND_copy)
print("Out of copy scripts from TiledTest : "+ str(client.get_OK()))

# Launch containers HERE
REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+SPACE_DIR+" "+SINGULARITY_NAME
TiledSet=list(range(NUM_DOCKERS))

print("\nREF_CAS : "+REF_CAS)

COMMANDStop=os.path.join(TILESINGULARITYS_DIR,"stop_singularitys")+" "+REF_CAS+" "+os.path.join(JOBPath,GPU_FILE)
print("\n"+COMMANDStop)
sys.stdout.flush()

# Launch singularitys
def Run_singularitys():
    COMMAND="bash -c \""+os.path.join(TILESINGULARITYS_DIR,"launch_singularitys")+" "+REF_CAS+" "+GPU_FILE+" "+SSH_FRONTEND+":"+SSH_IP+" "+TILEDVIZ_DIR+" "+TILESINGULARITYS_DIR+\
             " TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS+\
             " > "+os.path.join(JOBPath,"output_launch")+" 2>&1 \"" 
    logging.warning("\nCommand singularitys : "+COMMAND)
    client.send_server(LaunchTS+' '+COMMAND)
    state=client.get_OK()
    logging.warning("Out of launch singularity : "+ str(state))
    sys.stdout.flush()
    stateVM=(state == 0)
    return stateVM

try:
    stateVM=Run_singularitys()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()



try:
    if (stateVM):
        build_nodes_file()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()


time.sleep(2)
# Launch singularity tools
if (stateVM):
    all_resize("1920x1080")


try:
    if (stateVM):
        stateVM=launch_tunnel()
    sys.stdout.flush()
except:
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()
print("after launch tunnel servers %r" % (stateVM))

try:
    nodesf=open("nodes.json",'r')
    nodes=json.load(nodesf)
    nodesf.close()
except:
    print("nodes.json doesn't exists !")
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()

print("after read nodes.json %r" % (stateVM))

try:
    if (stateVM):
        stateVM=launch_vnc()
except:
    print("Problem when launch vnc !")
    stateVM=False
    traceback.print_exc(file=sys.stdout)
    kill_all_containers()

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
    COMMANDKill=' killall -9 Xvfb'
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

        
def kill_all_containers():
    stateVM=True
    client.send_server(ExecuteTS+' killall -9 Xvfb')
    state=client.get_OK()
    print("Out of killall command : "+ str(state))
    client.send_server(LaunchTS+" "+COMMANDStop)
    state=client.get_OK()
    print("Out of COMMANDStop : "+ str(state))
    stateVM=(state == 0)
    time.sleep(2)
    Remove_TileSet()
    return stateVM

        
#isActions=True
launch_actions_and_interact()

try:
    print("isActions: "+str(isActions))
except:
    print("isActions not defined.")

kill_all_containers()

sys.exit(0)

