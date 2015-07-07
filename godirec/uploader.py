import pysftp
import json
import os
import godirec

def test_uploader():
    with open(godirec.resource_filename(__name__, "conf.json")) as f:
        conf = json.load(f)
    host = conf['host']
    key_file = os.path.expanduser(conf['key_file'])
    user = conf['user']
    with pysftp.Connection(host, user, key_file) as sftp:
        filepath = conf['download']['from']
        localpath = conf['download']['to']
        sftp.get(filepath, localpath)

        filepath = conf['upload']['to']
        localpath = conf['upload']['from']
        sftp.put(localpath, filepath)
