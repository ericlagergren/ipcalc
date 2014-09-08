#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script is a subnetting calculator that mirrors *nix's ipcalc.

Originally it was all cool with some super awesome bit shifting but
even though I actually got it to work I decided to drop that in favor
of the C modules socket and struct because it's faster or something.

I miss my bit shifting :(

Written by: Eric Lagergren <ericscottlagergren@gmail.com>
Licensed under the WTFPL <http://www.wtfpl.net/txt/copying/>

"""

import argparse
import math
import socket
import struct

def parse_args():

    prog = 'ipcalc'
    usage = '{0} [-n NUMHOST | -s SUBMASK] [IPv4 address/mask]'.format(prog)
    description = ('Subnetting Calculator'
                   '\n=====================\n'
                   'Takes both an IPv4 address and either a submask in CIDR '
                   'notation,\nquad-dotted notation, or an arbitary number of '
                   'hosts.\n\nAddress range, host values, submasks, etc.')
    epilogue = (
        'example:\n'
        '\tipcalc 192.168.0.1/24\n'
        '\tipcalc 192.168.0.1 24\n'
        '\tipcalc -n 192.168.0.1 250')

    parser = argparse.ArgumentParser(usage=usage,
                                     description=description,
                                     epilog=epilogue,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        'ip',
        metavar='IPv4 address/mask',
        type=str,
        help='CIDR notation of IPv4 address\n192.168.0.1/24')
    parser.add_argument(
        'prefix',
        metavar='CIDR prefix',
        type=str,
        help='CIDR prefix OR submask\n24, 16, etc. OR 255.255.0.0, etc.',
        const=None,
        nargs='?')
    parser.add_argument(
        '-n',
        '--hosts',
        type=int,
        help='Integer number of hosts')
    parser.add_argument(
        '-p',
        '--plain',
        '--no-colors',
        action='store_true',
        help='Turn colors off')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    return args

def main(*args):

    args = args[0]

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    if args.plain:
        HEADER = OKGREEN = OKBLUE = WARNING = FAIL = ENDC = '\033[0m'

    MAX_BIT_INT = 32
    MAX_BIT_HEX = 0xFF
    MAX_BIT_BIN = 255
    THIRTY_TWO_BITS = 4294967295

    big_int = struct.Struct('!I')


    def set_base(prefix, hosts):
        """
        Returns the 'base' which is an int which is <= 32 and >= 0
        Represents number of 'set' bits.

        See: https://www.google.com/search?q=hamming+weight

        """
        if hosts:
            base = int(set_bits_from_host(hosts))
            return base
        elif prefix:
            try:
                base = int(prefix)
            except ValueError:
                base = set_bits_from_submask(prefix)
            return base


    def set_bits_from_host(num_hosts):
        """
        Returns base from number of desired hosts
        See set_base()

        """
        if 0 is not num_hosts:
            num_hosts = MAX_BIT_INT - int(math.ceil(math.log(num_hosts, 2)))
        return num_hosts


    def set_bits_from_submask(submask):
        """
        Returns base from subnetwork mask
        See set_base()

        """
        # [23:47] <runciter>: struct.unpack('!I', socket.inet_aton(ip))
        # from user 'runciter' in #python on freenode IRC
        try:
            uint32_t = big_int.unpack(socket.inet_aton(submask))[0]
        except socket.error:
            quit('{0}Invalid subnet mask entered.'.format(FAIL))

        # http://books.google.com/books?id=iBNKMspIlqEC&pg=PA66#v=onepage&q&f=false
        uint32_t -= (uint32_t >> 1) & 0x55555555
        uint32_t = (uint32_t & 0x33333333) + ((uint32_t >> 2) & 0x33333333)
        uint32_t += (uint32_t >> 4) & 0x0F0F0F0F
        uint32_t += uint32_t >> 8
        uint32_t += uint32_t >> 16
        return uint32_t & 0x0000003F


    def submask_from_set_bits(base):
        """
        Returns a subnetwork mask from the base

        """
        try:
            mask = ~0 << (32 - base)
        except ValueError:
            quit(
                '{0}CIDR prefix too large.\n{1}Must be <= 32, >= 0.'.format(
                    FAIL,
                    WARNING))
        return '{0}.{1}.{2}.{3}'.format(
            mask >> 24 & MAX_BIT_BIN,
            mask >> 16 & MAX_BIT_BIN,
            mask >> 8 & MAX_BIT_BIN,
            mask & MAX_BIT_BIN)


    def wildcard(base):
        """
        Returns Cisco wildcard address.
        Same as inverse of subnetwork mask

        """
        mask = ~(~0 << (32 - base))
        return '{0}.{1}.{2}.{3}'.format(
            mask >> 24 & MAX_BIT_BIN,
            mask >> 16 & MAX_BIT_BIN,
            mask >> 8 & MAX_BIT_BIN,
            mask & MAX_BIT_BIN)


    def max_hosts(base):
        """
        Calculates max number of hosts network can support

        """
        base = base or 0
        if base >= 2:
            base = 2 ** (MAX_BIT_INT - base)
        return base - 2


    def broadcast_addr(sm, ip):
        """
        Returns broadcast address of network

        """
        bn = ip | (~sm & THIRTY_TWO_BITS)
        # To Do: Get this gross thing to work with struct and socket
        return ".".join(map(lambda n: str(bn >> n & MAX_BIT_HEX), [24, 16, 8, 0]))


    def network_addr(sm, ip):
        """
        Returns network address of network

        """
        bn = ip & sm
        return socket.inet_ntoa(big_int.pack(bn))


    def subnets(base):
        """
        Returns maximum number of available subnets

        """
        mod_base = base % 8
        return 2 ** mod_base if mod_base else 2 ** 8


    def display_bits():
        """
        Prints visualization of on/off bits

        """
        """
        try:
            b_int = bin(integer)[2:]
            return '.'.join(b_int[i:i+8] for i in xrange(0, len(b_int), 8))
        except TypeError:
            return big_int.unpack(socket.inet_aton(integer))

        """
        pass


    def ip_class(ip):
        """
        Returns class of IPv4 address

        """

        if 0xC0000000 == ip & 0xC0000000:
            return 'Class C'
        elif 0x80000000 == ip & 0x80000000:
            return 'Class B'
        elif 0 == ip & 0x80000000:
            return 'Class A'
        else:
            return False

    # Set initial values

    ip_input = args.ip.split('/')[0]
    hosts_input = args.hosts

    try:
        prefix_input = args.ip.split('/')[1]
    except IndexError:
        prefix_input = args.prefix

    # Set base for calculations
    base = set_base(prefix_input, hosts_input)

    try:
        IP_32_BIT = big_int.unpack(socket.inet_aton(ip_input))[0]
    except socket.error:
        quit('{0}Invalid IPv4 address entered.'.format(FAIL))

    SM_32_BIT = big_int.unpack(socket.inet_aton(submask_from_set_bits(base)))[0]

    # Set values we'll be modifying
    submask = submask_from_set_bits(base)
    network_address = network_addr(SM_32_BIT, IP_32_BIT)
    broadcast_address = broadcast_addr(SM_32_BIT, IP_32_BIT)

    network_min = network_addr(SM_32_BIT + 1, IP_32_BIT)
    network_max = '{0}{1}'.format(
        broadcast_address[:-1], int(broadcast_address[-1]) - 1)

    print 'Address:   {0}{1}{2}'.format(HEADER, ip_input, ENDC)
    print 'Netmask:   {0}{1} = {2}{3}'.format(HEADER, submask_from_set_bits(base), base, ENDC)
    print 'Wildcard:  {0}{1}{2}'.format(HEADER, wildcard(base), ENDC)
    print 'Class:     {0}{1}{2}'.format(HEADER, ip_class(IP_32_BIT), ENDC)
    print '{0}-->{1}'.format(OKGREEN, ENDC)
    print 'Network:   {0}{1}/{2}{3}'.format(OKBLUE, network_address, base, ENDC)
    print 'HostMin:   {0}{1}{2}'.format(OKBLUE, network_min, ENDC)
    print 'HostMax:   {0}{1}{2}'.format(OKBLUE, network_max, ENDC)
    print 'Broadcast: {0}{1}{2}'.format(OKBLUE, broadcast_address, ENDC)
    print 'Subnets:   {0}{1}{2}'.format(OKBLUE, subnets(base), ENDC)
    print 'Hosts/Net: {0}{1}{2}'.format(OKBLUE, max_hosts(base), ENDC)

if __name__ == '__main__':
    args = parse_args()
    main(args)
