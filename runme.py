import requests
import json
import sys

hostctrl = "http://localhost:5001"
slaveaddr = "localhost"
slaveport = 1337


def setup_network():
    data = {"peers": ["calvinip://%s:%s" % (slaveaddr, slaveport)]}
    requests.post(hostctrl + "/peer_setup", data=json.dumps(data))


# Not used
def deploy_app():
    with open("calvin/scripts/test3.calvin", "r") as fp:
        script = fp.read()
    data = {"name": "testapp", "script": script}
    requests.post(hostctrl + "/deploy", data=json.dumps(data))


def actor_info(actor_id):
    return json.loads(requests.get(hostctrl + "/actor/" + actor_id).text)


def migrate(actor_sort):
    req = requests.get(hostctrl + "/actors")
    actors = json.loads(req.text)
    a_infos = {a: actor_info(a) for a in actors}
    if actor_sort == "sink":
        actor = [a for a in a_infos if a_infos[a]['type'] == "io.StandardOut"][0]
    else:
        actor = [a for a in a_infos if a_infos[a]['type'] == 'std.Counter'][0]
    data = {"peer_node_id": "calvin-miniscule"}
    requests.post(hostctrl + "/actor/" + actor + "/migrate", data=json.dumps(data))

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ["source", "sink"]:
        print("Usage: %s <source/sink>" % (sys.argv[0], ))
        sys.exit(0)

    setup_network()
    migrate(sys.argv[1])
