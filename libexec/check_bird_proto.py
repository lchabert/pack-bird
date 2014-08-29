#!/usr/bin/env python

# Copyright (C) 2014:
# Chabert Loic, chabert.loic.74@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import os
import sys
import optparse
import re

try:
    import paramiko
except ImportError:
    print "ERROR : this plugin needs the python-paramiko module. Please install it"
    sys.exit(2)

# Ok try to load our directory to load the plugin utils.
my_dir = os.path.dirname(__file__)
sys.path.insert(0, my_dir)

try:
    import schecks
except ImportError:
    print "ERROR : this plugin needs the local schecks.py lib. Please install it"
    sys.exit(2)

VERSION = "1"

OK = 0
WARNING = 2
CRITICAL = 2
UNKNOWN = 3

def check_bgppeer(client, bgppeer):
    raw = r"""birdcl show protocols {0} | grep {0}""".format(bgppeer)
    stdin, stdout, stderr = client.exec_command(raw)
    try:
        try:
            line = [l for l in stderr][0]
            regexp = re.compile(r'Unable to connect to server control socket')
            if regexp.search(line) is not None:
                print "ERROR: Bird is not running."
                sys.exit(CRITICAL)
        except IndexError:
            pass 
        line = [l for l in stdout][0]
    except KeyError:
        print "UNKNOWN: bgppeer {0} not found.".format(bgppeer)
        sys.exit(UNKNOWN)

    regexp = re.compile(r'down')
    if regexp.search(line) is not None:
        print "ERROR: {0}'s BGP session is down.".format(bgppeer)
        sys.exit(CRITICAL)
    else:
        raw = r"""birdcl show route protocol {0} count""".format(bgppeer)
        stdin, stdout, stderr = client.exec_command(raw)
        line = [l for l in stdout][1]
        client.close()
        line = line.split(' ', 1)
        route_number = int(line[0])
        
        perfdata = 'imported_route={0};;;;'.format(route_number)
        if route_number > 1:
            print "OK: {0}'s BGP session is up. {1} route imported. | {2}".format(bgppeer, route_number, perfdata)
            sys.exit(OK)
        else:
            print "WARNING: {0}'s BGP session is up but {1} route imported. | {2}".format(bgppeer, route_number, perfdata)
            sys.exit(WARNING)


parser = optparse.OptionParser(
    "%prog [options]", version="%prog " + VERSION)
parser.add_option('-H', '--hostname',
                  dest="hostname", help='Hostname to connect to')
parser.add_option('-i', '--ssh-key',
                  dest="ssh_key_file", help='SSH key file to use. By default will take ~/.ssh/id_rsa.')
parser.add_option('-u', '--user',
                  dest="user", help='Remote user to use. By default shinken.')
parser.add_option('-p', '--port',
                  dest="port", help='SSH remote TCP port. By default 22')
parser.add_option('-P', '--passphrase',
                  dest="passphrase", help='SSH key passphrase. By default will use void')
parser.add_option('-T', '--transitaire', dest="bgppeer", help='BGP peer to check.')

if __name__ == '__main__':
    # Ok first job : parse args
    opts, args = parser.parse_args()
    if args:
        parser.error("Does not accept any argument.")

    hostname = opts.hostname
    if not hostname:
        print "Error : hostname parameter (-H) is mandatory."
        sys.exit(2)
    
    bgppeer = opts.bgppeer
    if not bgppeer:
        print "Error : BGP peer (protocol) parameter (-T) is mandatory."
        sys.exit(2)

    try:
        port = int(opts.port) or 22
    except:
        print "Error : port parameter (-p) must be an integer"

    ssh_key_file = opts.ssh_key_file or os.path.expanduser('~/.ssh/id_rsa')
    user = opts.user or 'shinken'
    passphrase = opts.passphrase or ''
    
    client = schecks.connect(hostname, ssh_key_file, passphrase, user, port)
    check_bgppeer(client, bgppeer)
