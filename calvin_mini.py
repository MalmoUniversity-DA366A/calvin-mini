from __future__ import print_function
import socket
import struct
import json
import select
import uuid
PORT = 1337

RT_ID = "calvin-miniscule"
TUNNEL_ID = None

ACTORS = {}



def actor_stdout(actor):
    infifo = actor['inports']['token']['fifo']
    if len(infifo) > 0:
        token = actor['inports']['token']['fifo'].pop(0)
        print("io.StandardOut<%s>: %s" % (actor['id'], token['data']))


def actor_counter(actor):
    import time
    actor['count'] += 1
    # This sleep allows other RT to catch up in case there is a congestion,
    # the reason is that we don't handle ACK and NACK messages properly at the
    # moment. We should. We're sorry. We cheat to have something to show.
    # Anyone caught using sleep() in the course will be given a FAIL-grade.
    time.sleep(0.5)
    actor['outports']['integer']['fifo'].append(actor['count'])


def actor_init(actor):
    actor['fire'] = ACTOR_TYPES[actor['type']]
    if actor['type'] == 'std.Counter':
        actor['count'] = 0


ACTOR_TYPES = \
    {
        'io.StandardOut': actor_stdout,
        'std.Counter': actor_counter,
    }


def gen_uuid(prefix=""):
    return prefix + str(uuid.uuid4())


def jprint(jstruct, prefix=""):
    print(prefix + ": ", json.dumps(jstruct, indent=2, default=str))


def start():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 1337))
    s.listen(5)
    return s


def accept(s):
    (conn, _) = s.accept()
    return conn


def recv_msg(conn):
    msg = conn.recv(2048)
    msg_len = struct.unpack_from("!I", msg)[0]
    msg = struct.unpack_from("!I%ds" % (msg_len, ), msg)[1]

    # jprint(json.loads(msg), prefix="RECV")
    msg = json.loads(msg)
    msg['conn'] = conn
    return msg


def handle_join(msg):
    reply = {}
    reply['cmd'] = 'JOIN_REPLY'
    reply['id'] = RT_ID
    reply['sid'] = msg['sid']
    reply['serializer'] = 'json'
    return reply


def create_actor(msg):
    global ACTORS
    # jprint(state)
    state = msg['state']
    actor = {}
    actor['type'] = state['actor_type']
    actor['name'] = state['actor_state']['name']
    actor['id'] = state['actor_state']['id']
    actor['inports'] = {}
    actor['outports'] = {}
    for portname in state['actor_state']['inports']:
        port_fifo = []
        port_id = state['actor_state']['inports'][portname]['id']
        port_peer = state['prev_connections']['inports'][port_id]
        actor['inports'][portname] = {'fifo': port_fifo, 'id': port_id, 'peer': port_peer}
    for portname in state['actor_state']['outports']:
        port_fifo = []
        port_id = state['actor_state']['outports'][portname]['id']
        port_peer = state['prev_connections']['outports'][port_id][0]
        actor['outports'][portname] = {'fifo': port_fifo, 'id': port_id, 'peer': port_peer}

    actor_init(actor)

    # bookkeeping
    actor['conn'] = msg['conn']
    actor['remote_rt'] = msg['from_rt_uuid']
    ACTORS[actor['id']] = actor

    # jprint(actor, prefix="NEW ACTOR")


def handle_actor_new(msg):
    create_actor(msg)
    reply = {}
    reply['cmd'] = 'REPLY'
    reply['msg_uuid'] = msg['msg_uuid']
    reply['value'] = 'ACK'
    reply['from_rt_uuid'] = RT_ID
    reply['to_rt_uuid'] = msg['from_rt_uuid']
    return reply


def handle_setup_tunnel(msg):
    global TUNNEL_ID
    request = {}
    request['msg_uuid'] = gen_uuid("MSG-")
    request['from_rt_uuid'] = RT_ID
    request['to_rt_uuid'] = msg['id']
    request['cmd'] = "TUNNEL_NEW"
    TUNNEL_ID = "fake-tunnel"
    request['tunnel_id'] = TUNNEL_ID
    request['policy'] = {}
    request['type'] = "token"
    return request


def pairwise(iterable):
    i = iter(iterable)
    return zip(i, i)


def handle_setup_ports(msg):
    state = msg['state']
    inports = state['prev_connections']['inports']
    outports = state['prev_connections']['outports']
    requests = []

    for port_id, dest in inports.items():
        for rt, peer_port_id in pairwise(dest):
            request = {}
            request['msg_uuid'] = gen_uuid("MSG-")
            request['from_rt_uuid'] = RT_ID
            request['to_rt_uuid'] = rt
            request['port_id'] = port_id
            request['peer_port_id'] = peer_port_id
            request['peer_actor_id'] = None
            request['peer_port_name'] = None
            request['peer_port_dir'] = None
            request['tunnel_id'] = TUNNEL_ID
            request['cmd'] = 'PORT_CONNECT'

            requests.append(request)

    for port_id, dests in outports.items():
        for rt, peer_port_id in dests:
            request = {}
            request['msg_uuid'] = gen_uuid("MSG-")
            request['from_rt_uuid'] = RT_ID
            request['to_rt_uuid'] = rt
            request['port_id'] = port_id
            request['peer_port_id'] = peer_port_id
            request['peer_actor_id'] = None
            request['peer_port_name'] = None
            request['peer_port_dir'] = None
            request['tunnel_id'] = TUNNEL_ID
            request['cmd'] = 'PORT_CONNECT'
            requests.append(request)

    return requests


def process(port_id, token):
    for actor_id, actor in ACTORS.items():
        for port_name, port in actor['inports'].items():
            if port['id'] == port_id:
                port['fifo'].append(token)


SEQUENCE_NBRS = {}

def handle_token(msg):
    reply = {}
    process(msg['peer_port_id'], msg['token'])
    reply['cmd'] = 'TOKEN_REPLY'
    reply['sequencenbr'] = msg['sequencenbr']
    reply['port_id'] = msg['port_id']
    reply['peer_port_id'] = msg['peer_port_id']
    reply['value'] = 'ACK'
    return reply


def send_tunnel(token, actor):
    msg = {}
    msg['to_rt_uuid'] = actor['remote_rt']
    msg['from_rt_uuid'] = RT_ID
    msg['cmd'] = "TUNNEL_DATA"
    msg['value'] = token
    msg['tunnel_id'] = TUNNEL_ID
    return msg


def send_token(data, actor, port_id, peer_port_id):
    global SEQUENCE_NBRS
    token = {}
    token['sequencenbr'] = SEQUENCE_NBRS.setdefault(port_id, 0)
    SEQUENCE_NBRS[port_id] += 1
    token['token'] = {'type': "Token", 'data': data}
    token['cmd'] = "TOKEN"
    token['port_id'] = port_id
    token['peer_port_id'] = peer_port_id[1]
    return [send_tunnel(token, actor)]


def handle_tunnel_data(msg):
    reply = {}
    reply['to_rt_uuid'] = msg['from_rt_uuid']
    reply['from_rt_uuid'] = msg['to_rt_uuid']
    reply['cmd'] = 'TUNNEL_DATA'
    reply['tunnel_id'] = TUNNEL_ID
    value = handle_msg(msg['value'])[0]
    reply['value'] = value
    return reply

def handle_msg(msg):
    if msg['cmd'] == 'JOIN_REQUEST':
        reply = [handle_join(msg)]
        reply += [handle_setup_tunnel(msg)]
        return reply
    if msg['cmd'] == 'ACTOR_NEW':
        reply = [handle_actor_new(msg)]
        reply += handle_setup_ports(msg)
        return reply
    if msg['cmd'] == 'TUNNEL_DATA':
        reply = [handle_tunnel_data(msg)]
        return reply
    if msg['cmd'] == 'TOKEN':
        reply = [handle_token(msg)]
        return reply
    if msg['cmd'] == 'TOKEN_REPLY':
        return [[]]
    if msg['cmd'] == 'REPLY':
        return []

    jprint(msg, prefix="UNKNOWN CMD")
    return None


def send_msg(conn, msg):
    # jprint(msg, prefix="SEND")
    msg = json.dumps(msg)
    data = struct.pack("!I%ds" % (len(msg), ), len(msg), msg)
    conn.sendall(data)


def loop():
    sock = start()

    messages_in = {}
    messages_out = {}

    incoming = [sock]
    outgoing = []

    while True:
        rread, rwrite, _ = select.select(incoming, outgoing, [])

        if sock in rread:
            conn = accept(sock)
            incoming += [conn]
            outgoing += [conn]
            rread.remove(sock)

        for conn in rread:
            msg = recv_msg(conn)
            messages_in.setdefault(conn, []).append(msg)

        for conn, messages in messages_in.items():
            if messages:
                reply = handle_msg(messages.pop(0))
                if reply:
                    messages_out.setdefault(conn, []).extend(reply)

        for actor_id, actor in ACTORS.items():
            actor['fire'](actor)

        for actor_id, actor in ACTORS.items():
            for port_name, port in actor['outports'].items():
                fifo = port['fifo']
                peer_port_id = port['peer']
                port_id = port['id']
                while fifo:
                    messages_out.setdefault(actor['conn'], []).extend(send_token(fifo.pop(0), actor, port_id, peer_port_id))

        for conn in rwrite:
            if messages_out.get(conn, False):
                send_msg(conn, messages_out[conn].pop(0))

    print("Exiting...")


if __name__ == '__main__':
    loop()
