#!/usr/bin/env python

import os
import logging
import argparse
from multiprocessing import Pipe
import json
from time import sleep

import numpy as np

from chatsimu import ProbeClient


def set_up_logging(args):
    log_format = '%(created)f | %(message)s'
    logging.basicConfig(format=log_format)
    logger = logging.getLogger("simulator")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.output_file, mode='w')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('  %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

def setup_cmd_parser():
    p = argparse.ArgumentParser(description='Simulate rooms and clients for a simplechat_server.')
    p.add_argument('-m', '--messages', action='store', type=int, default=100, help='Number of messages to send.')
    p.add_argument('-s', '--send_rate', action='store', type=float, default=10, help='Send rate (messages/sec).')
    p.add_argument('-i', '--ip', action='store', default='127.0.0.1', help='Server IP address.')
    p.add_argument('-p', '--port', action='store', type=int, default=8888, help='Server Port.')
    p.add_argument('-o', '--output_file', action='store', default='logsimulator.log', help='Name of log file.')
    return p

def wait_respond(pipe, wc, rc=None):
    res = ""
    while res != wc:
        res = pipe.recv()
    if rc:
        pipe.send(rc)

def report(lines):
    data = np.array(lines)
    fr2 = np.percentile(data, 50, axis=0)  # report the MEDIAN
    np.set_printoptions(precision=6)
    r2 = fr2.tolist()
    print ', '.join([str(i) for i in r2])

def batch_summary(rep):
    snt = rep['msgs_sent']
    rcvd = rep['msgs_received']
    lst = rep['received_lst']
    da = []
    for tr, m in lst:
        m_obj = json.loads(m)
        ts = float(m_obj['sent_ts'])
        delta = tr - ts
        da.append(delta)

    rtts = np.array(da)
    rtt_mean = np.mean(rtts)  # round trip time, mean
    rtt_p99 = np.percentile(rtts, 99)
    rtt_p999 = np.percentile(rtts, 99.9)
    rtt_max = np.amax(rtts)
    return (rcvd, snt-rcvd, rtt_max, rtt_mean, rtt_p99, rtt_p999)


if __name__ == "__main__":
    NUM_BATCHES = 10
    PARSER = setup_cmd_parser()
    ARGS = PARSER.parse_args()
    log = set_up_logging(ARGS)
    log.info("START_PROBING - PID:%d" % (os.getpid(),))
    log.info("SIMU_PARAMS - IP:%s - PORT:%s - MSGS_TO_SEND: %s" % (ARGS.ip, ARGS.port,  ARGS.messages))
    pipe, b = Pipe()
    c = ProbeClient(b, ARGS.send_rate, ARGS.messages, ARGS.ip, ARGS.port)
    c.start()
    wait_respond(pipe, "running", "connect")
    wait_respond(pipe, "connected") # , "start_send_batch")
    print "PROBE CLIENT CONNECTED, now sending and receiving"
    batch_results = []
    for i in range(0, NUM_BATCHES):
        log.info("BATCH %d" % (i,))
        pipe.send("start_send_batch")
        wait_respond(pipe, "done_sending_batch", "report")
        rep = pipe.recv()   # block until we get the report
        batch_results.append(rep)
        sleep(1.2)  # pause
    pipe.send("finish")
    s = []
    for r in batch_results:
        s.append(batch_summary(r))
    report(s)
