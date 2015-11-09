#!/usr/bin/env python

import pxssh
import pexpect
import time
import sys
from os.path import isdir
from os import mkdir


# pantest_vs:  vs=variable server. This version of pantest takes the first argument of the params line
# (old, new) as the server.

STATS_INTERVAL = 1  # seconds
HEADER="server_type, adtl_probe_clients, num_adtl_rooms, clients_per_room, snd_rate, sent_msgs, lost_msgs, RTT_max, RTT_mean, RTT_99, RTT_999, max_sprocess_cpu"

def get_test_params(fn):
    # adtl_probe_clients, num_adtl_rooms, clients_per_room, snd_rate
    f = open(fn,'r')
    lines = f.readlines()
    f.close()
    data = []
    for line in lines:
        di = line.split(',')
        st = "" if di[0].lower() != 'old' else '_old'
        di[0] = '0'
        di = [int(e.strip()) for e in di]
        di[0] = st
        data.append(di)
    return data

def start_session(server,username):
    so = pxssh.pxssh()  # simplechat server
    so.force_password = False
    so.login(server, username, original_prompt='$', login_timeout=600)
    return so

if len(sys.argv) != 6:
    print "Usage: %s <server_ip> <username> <path> <params_file> <out_file>" % (sys.argv[0],)
    print "Do NOT use a trailing slash in the path!"
    sys.exit()

SERVER = sys.argv[1]
USERNAME = sys.argv[2]
SCRIPTS_PATH = sys.argv[3]
test_params = get_test_params(sys.argv[4])
fout = open(sys.argv[5], 'w')
fout.write(HEADER + '\n')

# instantiate shell objects, and do log in. We're using ssh keys for passwordless login.
scs = start_session(SERVER,USERNAME)  # simplechat server session
psc = start_session(SERVER,USERNAME)  # pidstat command session
lc = start_session(SERVER,USERNAME)   # loader command session

if not isdir('cpuloads'):
    mkdir('cpuloads')

tn = 0
for param_set in test_params:

    server_type = param_set[0]  # server type, new or old.
    apc = param_set[1]  # adtl_probe_clients
    ar = param_set[2]   # num_adtl_rooms
    cpr = param_set[3]  # clients_per_room
    sr = param_set[4]   # snd_rate
    print "RUNNING TEST %d. Server type _%s_. Param set is %s" %(tn, server_type, repr(param_set))

    # start the server
    print "STARTING CHATSERVER..."
    scs.sendline("%s/simplechat_server%s.py -i='0.0.0.0' -c2" % (SCRIPTS_PATH,server_type,))
    scs.expect('PID:(\d+)', timeout=600)
    scs_pid = scs.match.group(1)  # we have the pid of the server
    print "CHATSERVER STARTED with pid %s" % (scs_pid,)

    # start logging server load with pidstat
    print "STARTING PIDSTAT..."
    psc.sendline('pidstat -h -p %s %s' % (scs_pid,STATS_INTERVAL))
    psc.expect('Time',timeout=600)
    start_time = time.time()
    print "PIDSTAT STARTED"
    # start the load

    load_required = not (0 == apc == ar == cpr)
    if load_required:
        print "STARTING loader: -b%d -r%d -c%d -s%d" % (apc, ar, cpr, sr)
        lc.sendline('%s/loader.py -b%d -r%d -c%d -s%d' % (SCRIPTS_PATH,apc, ar, cpr, sr))
        lc.expect('Press ENTER to finish', timeout=600)
    print "LOADER STARTED"

    # run the probe until it finishes
    print "RUNNING probe"
    result = pexpect.run("./probe.py -i=server_d -m100 -s%d" % (sr,), timeout=10e6)

    if load_required:
        print "STOPPING loader"
        lc.sendline('\n')  # send RETURN to   the loader, so it finishes
        lc.sendcontrol('c')
    end_time = time.time()
    secs = int(end_time - start_time) / STATS_INTERVAL

    print "GETTING AND STOPPING pidstats"
    pidstats = []
    for i in range(0, secs+4):  # read as many "python" as seconds. Don't do readlines, because of the headers and blanks that pidstat prints
        psc.expect('python', timeout=120)
        pidstats.append(psc.before)
    psc.sendcontrol('c')

    print "STOPPING server"
    scs.sendcontrol('c')

    # process result and pidstats to get data.
    rtt_line = result.strip().split('\n')[-1]
    pidstats = [e for e in pidstats if not "#" in e]  # filter out comments
    cpu_loads = []
    pf = open( "cpuloads/%d_%d_%d_%d_a.pidstat" % (apc, ar, cpr, sr), 'w')
    for pd in pidstats:
        pf.write(str(pd))
    pf.close()
    for i in pidstats:
        cl = i.strip('\r\n').strip()
        try:
            cl2 = cl.split()[-2]
            cpu_loads.append(cl2)
        except IndexError:
            print "Index error in CPU Load line: %s" %(cl,)
    pf = open( "cpuloads/%d_%d_%d_%d_b.pidstat" % (apc, ar, cpr, sr), 'w')
    for cl in cpu_loads:
        pf.write(str(cl)+'\n')
    pf.close()
    max_cpu_load = max(cpu_loads)
    out_line = ', '.join([str(e) for e in param_set]) + ", " + rtt_line + ", " + max_cpu_load
    fout.write(out_line+'\n')
    print "Killing all python processes, just in case... \n"
    psc.sendline('killall python')
    psc.prompt()
    print out_line
    tn += 1
    print

fout.close()
print "CLOSING remote sessions."

psc.logout()
lc.logout()
scs.logout()
psc.terminate()
lc.terminate()
scs.terminate()
