#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys,os,time
import code
import argparse
import re, datetime
import inspect
    
sys.path.append(os.path.realpath('/TiledViz/TVConnections/'))
from connect import sock

import json
# HPC Machine working directory
#In TVConnection :
# DATE=re.sub(r'\..*','',datetime.datetime.isoformat(datetime.datetime.now(),sep='_').replace(":","-"))
# TiledVizPath='/login/.tiledviz'
# JOBPath='/login/.tiledviz/TEST_'+DATE

# CASE_NAME in case_config:
#CASE="UREE"
#In TVConnection : TileSet="TEST"
SITE_config='./site_config.ini'
CASE_config="./case_config.ini"


if __name__ == '__main__':
    #def job(globals,locals)
    actions_file=open("/home/myuser/actions.json",'r')
    tiles_actions=json.load(actions_file)

    config = configparser.ConfigParser()
    config.optionxform = str

    config.read(SITE_config)

    TILEDOCKERS_path=config['SITE']['TILEDOCKER_DIR']
    DOCKERSPACE_DIR=config['SITE']['DOCKERSPACE_DIR']
    #NOVNC_URL=config['SITE']['NOVNC_URL']
    GPU_FILE=config['SITE']['GPU_FILE']

    HTTP_FRONTEND=config['SITE']['HTTP_FRONTEND']
    HTTP_LOGIN=config['SITE']['HTTP_LOGIN']
    HTTP_IP=config['SITE']['HTTP_IP']
    init_IP=config['SITE']['init_IP']

    config.read(CASE_config)

    CASE=config['CASE']['CASE_NAME']
    NUM_DOCKERS=int(config['CASE']['NUM_DOCKERS'])

    network=config['CASE']['network']
    nethost=config['CASE']['nethost']
    domain=config['CASE']['domain']

    OPTIONssh=config['CASE']['OPTIONssh']
    SOCKETdomain=config['CASE']['SOCKETdomain']

    DOCKER_NAME=config['CASE']['DOCKER_NAME']

    OPTIONS=config['CASE']['OPTIONS'].replace("$","").replace('"','')
    print("\nOPTIONS from CASE_CONFIG : "+OPTIONS)
    def replaceconf(x):
        if (re.search('}',x)):
            varname=x.replace("{","").replace("}","")
            return config['CASE'][varname]
        else:
            return x
    OPTIONS=OPTIONS.replace("JOBPath",JOBPath)
    OPTIONS=OPTIONS.replace('{','|{').replace('}','}|').split('|')
    #print("OPTIONS before replacement : "+str(OPTIONS))

    OPTIONS="".join(list(map( replaceconf,OPTIONS)))
    print("OPTIONS after replacement : "+OPTIONS)
    

    CreateTS='create TS='+TileSet+' Nb='+str(NUM_DOCKERS)

    client.send_server(CreateTS)

    # Build TEST dir
    client.send_server('launch TS='+TileSet+" "+JOBPath+" mkdir "+CASE)
    print("Out of mkdir %s : %s" % (CASE, str(client.get_OK())))
    CASEdir=os.path.join(JOBPath,CASE)

    # get TiledTest package from Github
    os.system("git clone https://github.com/mmancip/TiledTest.git")
    # Untar Test package
    # os.system("tar xfz TiledTest.tgz")
    
    # command='launch TS='+TileSet+" "+TiledVizPath+" cp -p build_qr "+os.path.join(JOBPath,'..')
    # print("cp build_qr : %s" % (command))
    # client.send_server(command)
    # print("Out of cp build_qr : %s" % (str(client.get_OK())))

    # Send CASE and SITE files
    try:
        send_file_server(client,TileSet,"TiledTest","test_client",JOBPath)
        send_file_server(client,TileSet,"TiledTest", "build_nodes_file", JOBPath)

        send_file_server(client,TileSet,".", CASE_config, CASEdir)
        CASE_config=os.path.join(CASEdir,CASE_config)
        send_file_server(client,TileSet,".", SITE_config, JOBPath)
        SITE_config=os.path.join(JOBPath,os.path.basename(SITE_config))
        send_file_server(client,TileSet,".", "list_hostsgpu", CASEdir)
    except:
        print("Error sending files !")
        traceback.print_exc(file=sys.stdout)
        try:
            code.interact(banner="Try sending files by yourself :",local=dict(globals(), **locals()))
        except SystemExit:
            pass

    # Launch containers HERE
    REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+DOCKERSPACE_DIR+" "+DOCKER_NAME

    print("\nREF_CAS : "+REF_CAS)

    COMMANDStop=os.path.join(TILEDOCKERS_path,"stop_dockers")+" "+REF_CAS+" "+os.path.join(CASEdir,GPU_FILE)
    print("\n"+COMMANDStop)

    # Launch dockers
    # TileServer is given by TileServer.py to all containers of the tileset.
    COMMAND=os.path.join(TILEDOCKERS_path,"launch_dockers")+" "+REF_CAS+" "+GPU_FILE+" "+HTTP_FRONTEND+":"+HTTP_IP+\
             " "+network+" "+nethost+" "+domain+" "+init_IP+" TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS

    print("\nCommand dockers : "+COMMAND)
    
    client.send_server('launch TS='+TileSet+" "+CASEdir+' '+COMMAND)
    #code.interact(local=locals())
    print("Out of launch dockers : "+ str(client.get_OK()))

    # Build nodes.json file from new dockers list
    COMMAND='launch TS='+TileSet+" "+CASEdir+' ../build_nodes_file '+CASE_config+' '+SITE_config+' '+TileSet
    print("\nCommand dockers : "+COMMAND)

    client.send_server(COMMAND)
    print("Out of build_nodes_file : "+ str(client.get_OK()))
    
    get_file_client(client,TileSet,CASEdir,"nodes.json",".")

    time.sleep(2)
    # Launch docker tools
    def launch_tunnel():
        client.send_server('execute TS='+TileSet+' /opt/tunnel_ssh '+SOCKETdomain+' '+HTTP_FRONTEND+' '+HTTP_LOGIN)
        print("Out of tunnel_ssh : "+ str(client.get_OK()))
    launch_tunnel()

    def launch_vnc():
        client.send_server('execute TS='+TileSet+' /opt/vnccommand')
        print("Out of vnccommand : "+ str(client.get_OK()))
    launch_vnc()

    def launch_resize(RESOL="1440x900"):
        client.send_server('execute TS='+TileSet+' xrandr --fb '+RESOL)
        print("Out of xrandr : "+ str(client.get_OK()))
    launch_resize()

    def launch_changesize(RESOL="1920x1080",tileNum=-1,tileId='001'):
        if ( tileNum > -1 ):
            TilesStr=' Tiles=('+containerId(tileNum+1)+') '
        else:
            TilesStr=' Tiles=('+tileId+') '
        COMMAND='execute TS='+TileSet+TilesStr+' xrandr --fb '+RESOL
        print("call server with : "+COMMAND)
        client.send_server(COMMAND)
        print("server answer is "+str(client.get_OK()))
    
    def launch_smallsize(tileNum=-1,tileId='001'):
        print("Launch launch_changesize smallsize for tile "+str(tileNum))
        launch_changesize(tileNum=timeNum,RESOL="950x420")

    def launch_bigsize(tileNum=-1,tileId='001'):
        print("Launch launch_changesize bigsize for tile "+str(tileNum))
        launch_changesize(tileNum=tileNum,RESOL="1920x1200")

    # # Use a metadata tab to exchange element source
    # for i in range(NUM_DOCKERS):
    #     line=taglist.readline().split(' ')
    #     file_name=(line[1].split('='))[1].replace('"','')
    #     COMMAND=' Tiles=('+containerId(i+1)+') '+os.path.join(/home/myuser/CASE,'test_client')
    #     #+' '+' '+file_name
    #     print("%d TEST command : %s" % (i,COMMAND))
    #     CommandTS='execute TS='+TileSet+COMMAND
    #     client.send_server(CommandTS)
    #     client.get_OK()

    def launch_client_global(script='test_client'):
        COMMAND=' '+os.path.join("/home/myuser/CASE",script)
        print("launch command on all tiles : %s" % (COMMAND))
        CommandTS='execute TS='+TileSet+COMMAND
        client.send_server(CommandTS)
    
        client.get_OK()

    launch_client_global(script='test_client')
    
    def launch_one_client(script='test_client',tileNum=-1,tileId='001'):
        COMMAND=' '+os.path.join("/home/myuser/CASE",script)
        if ( tileNum > -1 ):
            TilesStr=' Tiles=('+containerId(tileNum+1)+') '
        else:
            TilesStr=' Tiles=('+tileId+') '
        print("launch command on %s : %s" % (TilesStr,COMMAND))
        CommandTS='execute TS='+TileSet+TilesStr+COMMAND
        client.send_server(CommandTS)        
        client.get_OK()

    
    def get_windows():
        client.send_server('execute TS='+TileSet+' wmctrl -l -G')
        print("Out of wmctrl : "+ str(client.get_OK()))
    get_windows()

    def fullscreenApp(windowname="glxgears",tileNum=-1):
        movewindows(windowname="glxgears",wmctrl_option='toggle,fullscreen',tileNum=tileNum)

    def movewindows(windowname="glxgears",wmctrl_option='toggle,fullscreen',tileNum=-1,tileId='001'):
        #remove,maximized_vert,maximized_horz
        #toggle,above
        #movewindows(windowname='glxgears',wmctrl_option="toggle,fullscreen",tileNum=2)
        if ( tileNum > -1 ):
            TilesStr=' Tiles=('+containerId(tileNum+1)+') '
        else:
            TilesStr=' Tiles=('+tileId+') '
        client.send_server('execute TS='+TileSet+TilesStr+'/opt/movewindows '+windowname+' -b '+wmctrl_option)
        client.get_OK()

    def toggle_fullscr():
        for i in range(NUM_DOCKERS):
            client.send_server('execute TS='+TileSet+' Tiles=('+containerId(i+1)+') '+
                               '/opt/movewindows OpenGL -b toggle,fullscreen')
            client.get_OK()
    
    def kill_all_containers():
        client.send_server('execute TS='+TileSet+' killall Xvnc')
        print("Out of killall command : "+ str(client.get_OK()))
        client.send_server('launch TS='+TileSet+" "+JOBPath+" "+COMMANDStop)
        client.close()

    # Launch Server for commands from FlaskDock
    print("GetActions=ClientAction("+str(connectionId)+",globals=dict(globals()),locals=dict(**locals()))")
    sys.stdout.flush()

    try:
        GetActions=ClientAction(connectionId,globals=dict(globals()),locals=dict(**locals()))
        outHandler.flush()
    except:
        traceback.print_exc(file=sys.stdout)
        code.interact(banner="Error ClientAction :",local=dict(globals(), **locals()))

    print("Actions \n",str(tiles_actions))
    sys.stdout.flush()
    try:
        code.interact(banner="Interactive console to use actions directly :",local=dict(globals(), **locals()))
    except SystemExit:
        pass

    kill_all_containers()

    sys.exit(0)


