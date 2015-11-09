#!/usr/bin/env python

import os
import logging
import argparse

from chatsimu import ChatLoader


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
    p.add_argument('-i', '--ip', action='store', default='127.0.0.1', help='Server IP address.')
    p.add_argument('-p', '--port', action='store', type=int, default=8888, help='Server Port.')
    p.add_argument('-b', '--probe_clients', action='store', type=int, default=0,
                   help='Number of additional clients in probe room (max 99).')
    p.add_argument('-r', '--rooms', action='store', default='room1',
                   help='Number of rooms (aside from the probe room).')
    p.add_argument('-c', '--clients', action='store', type=int, default=10, help='Number of clients per room.')
    p.add_argument('-n', '--connect_rate', action='store', type=float, default=10,
                   help='Connect rate (connections/sec).')
    p.add_argument('-s', '--send_rate', action='store', type=float, default=10, help='Send rate (messages/sec).')
    p.add_argument('-o', '--output_file', action='store', default='logsimulator.log', help='Name of log file.')
    return p

if __name__ == "__main__":
    PARSER = setup_cmd_parser()
    ARGS = PARSER.parse_args()
    log = set_up_logging(ARGS)
    log.info("START_LOADING - PID:%d" % (os.getpid(),))

    log.info("LOADING_PARAMS - IP:%s - PORT:%s - A_PROBE_CLIENTS:%s - ROOMS:%s - CLIENTS:%s - SEND_RATE:%s" %
             (ARGS.ip, ARGS.port,  ARGS.probe_clients, ARGS.rooms, ARGS.clients, ARGS.send_rate))

    cs = ChatLoader(ARGS.ip, ARGS.port, num_rooms=ARGS.rooms, ncprobe=ARGS.probe_clients,
                    num_clients_per_room=ARGS.clients,
                    connect_rate=ARGS.connect_rate, send_rate=ARGS.send_rate)
    cs.generate_rooms()
    cs.instantiate_clients()
    cs.start_all_clients()
    cs.connect_all_clients()
    cs.start_sending()
    raw_input("Press ENTER to finish...")
    cs.finish_clients()
