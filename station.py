import os, sys, win32, time, json, random, time, datetime
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import _thread
from threading import Timer
import atexit
import uuid
import pickle


app = Flask(__name__)
CORS(app)
plugins = {}

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

history = []

tokens = {

}


letters = sum([
        [chr(s) for s in range(ord('a'), ord('z')+1)],
        [chr(s) for s in range(ord('A'), ord('Z')+1)],
        [chr(s) for s in range(ord('0'), ord('9')+1)],
        [
            '_','-','$','%','.']
        ], [])

motd = "PyChat Developers & Testers"


def saveAll():
    with open('tokens.pickle', 'wb') as f:
        pickle.dump(tokens, f)
    with open('history.pickle', 'wb') as f:
        pickle.dump(history, f)

atexit.register(saveAll)

def loadAll():
    global tokens, history
    if os.path.exists('tokens.pickle'):
        with open('tokens.pickle', 'rb') as f:
            tokens = pickle.load(f)
    if os.path.exists('history.pickle'):
        with open('history.pickle', 'rb') as f:
            history = pickle.load(f)

loadAll()


def execAdmin(com):
    global tokens, history
    comm = com.split()
    if comm[0] == 'op':
        if len(comm) > 1:
            if comm[1] in [tokens[token]['uname'] for token in tokens.keys()]:
                token = [token for token in tokens.keys() if tokens[token]['uname'] == comm[1]][0]
                tokens[token]['isAdmin'] = True
    if comm[0] == 'deop':
        if len(comm) > 1:
            if comm[1] in [tokens[token]['uname'] for token in tokens.keys()]:
                token = [token for token in tokens.keys() if tokens[token]['uname'] == comm[1]][0]
                tokens[token]['isAdmin'] = False
    if comm[0] == 'kick':
        if len(comm) > 1:
            if comm[1] in [tokens[token]['uname'] for token in tokens.keys()]:
                token = [token for token in tokens.keys() if tokens[token]['uname'] == comm[1]][0]
                del tokens[token]
    if comm[0] == 'test':
        history.append({'id':len(history), 'message': 'Testing! The user provided this event is admin.', 'uname': '[SERVER]'})
    if comm[0] == 'wipe':
        if len(comm) > 1:
            if comm[1] == 'tokens':
                history.append({'id':len(history), 'message': 'WARNING!!! YOUR ACCOUNT WILL BE DELETED IN 10 SECS', 'uname': '[DIE]'})
                time.sleep(10)
                tokens = {}
            if comm[1] == 'history':
                del history[:]
                for user in [tokens[token] for token in tokens.keys()]:
                    user['lastupdate'] = -1
                history.append({'id':len(history), 'message': 'WIPE! All messages was deleted from server, use your local copies', 'uname': '[WIPE]'})


@app.route('/reg/<string:uname>:<string:key>')
def reg(uname, key):
    global tokens, history
    # User exists
    if uname in [tokens[token]['uname'] for token in tokens.keys()]:
        if True in [True for token in tokens.keys() if tokens[token]['key'] == key and tokens[token]['uname'] == uname]:
            token = [token for token in tokens.keys() if tokens[token]['key'] == key and tokens[token]['uname'] == uname][0]

            new_token = str(uuid.uuid4())
            tokens[new_token] = tokens[token].copy()
            tokens[new_token]["lastactivity"] = int(time.time())
            tokens[new_token]["online"] = True

            #tokens.pop(token, None)
            if token in tokens:
                del tokens[token]

            history.append({'id':len(history), 'message': '%s returned to chat!' % uname, 'uname': '[SERVER]'})
            return Response('{"status": "ok", "response": {"uname": "%s", "key": "%s", "token": "%s", "motd": "%s"}}' % (uname, key, new_token, motd), mimetype='application/json')
        else:
            return Response('{"status": "fail", "code": "401", "desc": "nickname already registered, use correct pass"}', mimetype='application/json')
    # New user
    if len(uname) > 2 and len(key) > 2 and len(uname) <= 10:
        for s in list(uname):
            if not s in letters:
                return Response('{"status": "fail", "code": "306", "desc": "uname is required to be defined only in [A-Za-z0-9\_\-\.]"}', mimetype='application/json')
        new_token = str(uuid.uuid4())
        tokens[new_token] = {'uname': uname, 'key': key, 'lastupdate': len(history)-1, "lastactivity": int(time.time()), "online": True}
        if len(tokens.keys()) == 1:
            tokens[new_token].update({'isAdmin': True})


        history.append({'id':len(history), 'message': '%s joined chat!' % uname, 'uname': '[SERVER]'})
        return Response('{"status": "ok", "response": {"uname": "%s", "key": "%s", "token": "%s", "motd": "%s"}}' % (uname, key, new_token, motd), mimetype='application/json')
    else:
        return Response('{"status": "fail", "code": "302", "desc": "uname or key isn\'t correct key = (len > 2), uname = (10 >= len > 2) "}', mimetype='application/json')

@app.route('/send', methods=['POST'])
def send():
    global tokens, history
    ## if data is encrypted - decrypt it There
    ## There
    data = json.loads(request.data)
    if 'message' in data.keys() and 'token' in data.keys():
        uname = ''
        try:
            uname = tokens[data['token']]['uname']
        except KeyError:
            return Response('{"status": "fail", "code": "402", "desc": "no valid token presented"}', mimetype='application/json')

        token = data['token']
        tokens[token]['lastactivity'] = int(time.time())
        if tokens[token]['online'] == False:
            history.append({'id':len(history), 'message': '%s returned to chat!' % uname, 'uname': '[SERVER]'})
            tokens[token]['online'] = True

        # send if was offline, then came online

        if 'isAdmin' in tokens[token].keys() and tokens[token]['isAdmin'] == True and data['message'][:1] == '/':
            adm_r = execAdmin(data['message'][1:])
            return Response(json.dumps({'status': 'ok', 'response': {'type':'admin'}}), mimetype='application/json')

        raw_msg = {'id':len(history), 'message': data['message'], 'uname': uname}

        if 'direct' in data.keys():
            raw_msg['direct'] = data['direct']

        history.append(raw_msg)
        return Response(json.dumps({'status': 'ok', 'response': {}}), mimetype='application/json')
    else:
        return Response('{"status": "fail", "code": "501", "desc": "forbidden, because you don\'t provided [message, token]"}', mimetype='application/json')

@app.route('/updates', methods=['GET'])
@app.route('/send', methods=['GET'])
def err_usePost():
    return Response('{"status": "fail", "code": "500", "desc": "use POST request instead of GET"}', mimetype='application/json')

@app.route('/updates', methods=['POST'])
def updates():
    global tokens, history
    ## if data is encrypted - decrypt it There
    ## There
    data = json.loads(request.data)
    if 'token' in data.keys():
        uname = ''
        try:
            uname = tokens[data['token']]['uname']
        except KeyError:
            return Response('{"status": "fail", "code": "402", "desc": "no valid token presented"}', mimetype='application/json')
        # ok!
        #lbd = sorted(players, key=lambda k: k['ts'], reverse=True)
        token = data['token']
        tokens[token]['lastactivity'] = int(time.time())
        if tokens[token]['online'] == False:
            history.append({'id':len(history), 'message': '%s returned to chat!' % uname, 'uname': '[SERVER]'})
            tokens[token]['online'] = True

        count = 0
        start = time.time()
        doResp = True
        while count == 0:
            end = time.time()
            if (end - start) > 22.0:
                break

            # Renew this func. When token is renewed, you need to get new tokens
            try:
                msg_list = [message for message in history if message['id'] > tokens[data['token']]['lastupdate']]
            except KeyError:
                return Response('{"status": "fail", "code": "502", "desc": "your token expired"}', mimetype='application/json')


            count = len(msg_list)
            time.sleep(0.5)

        _ts = -1
        if len(msg_list) > 0:
            _ts = msg_list[-1]['id']

        if _ts > -1:
            tokens[data['token']]['lastupdate'] = _ts

        response = json.dumps({'status': 'ok', 'total': len(msg_list), 'response': msg_list})
        return Response(response, mimetype='application/json')
    else:
        return Response('{"status": "fail", "code": "501", "desc": "forbidden, because you don\'t provided [key, token]"}', mimetype='application/json')


@app.route('/online', methods=['POST'])
def online_list():
    global tokens, history
    data = json.loads(request.data)
    if 'token' in data.keys():
        uname = ''
        try:
            uname = tokens[data['token']]['uname']
        except KeyError:
            return Response('{"status": "fail", "code": "402", "desc": "no valid token presented"}', mimetype='application/json')
        # ok!
        #lbd = sorted(players, key=lambda k: k['ts'], reverse=True)
        token = data['token']
        tokens[token]['lastactivity'] = int(time.time())
        if tokens[token]['online'] == False:
            history.append({'id':len(history), 'message': '%s returned to chat!' % uname, 'uname': '[SERVER]'})
            tokens[token]['online'] = True

        fri_list = [{"uname": user['uname'], "online": user['online']} for user in [tokens[token] for token in tokens.keys() if not token == data['token']]]
        fri_list = sorted(fri_list, key=lambda k: k['online'], reverse=True)

        response = json.dumps({'status': 'ok', 'total': len(fri_list),'response': fri_list})
        return Response(response, mimetype='application/json')
    else:
        return Response('{"status": "fail", "code": "501", "desc": "forbidden, because you don\'t provided [token]"}', mimetype='application/json')



@app.route('/messages')
def msglist():
    return Response(json.dumps(history), mimetype='application/json')

@app.route('/tokens')
def toklist():
    return Response(json.dumps(tokens), mimetype='application/json')


def gupd():
    global tokens, history
    while True:
        for token in tokens.keys():
            if token in tokens:
                if tokens[token]['online'] == True and (time.time() - tokens[token]['lastactivity']) > 30:
                    tokens[token]['online'] = False
                    history.append({'id':len(history),
                        'message': '%s left the chat. (%s sec ago)' %
                        (tokens[token]['uname'], int(time.time() - tokens[token]['lastactivity'])),
                        'uname': '[SERVER]'})
            else:
                break
        time.sleep(10)


if __name__ == '__main__':

    _thread.start_new_thread(gupd, ())
    app.run('0.0.0.0', port=12000, debug=False, threaded=True)
