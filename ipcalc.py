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

prog = 'ipcalc'
usage = '{0} [-n NUMHOST | -s SUBMASK] [IPv4 address/mask]'.format(prog)
description = ('Subnetting Calculator\n=====================\nTakes both an '
               'IPv4 address and either a submask in CIDR notation,\n'
               'quad-dotted notation, or an arbitary number of hosts.'
               '\n\nReturns a bunch of cool shit.')
epilogue = (
    'example:\n\tipcalc 192.168.0.1/24\n\tipcalc 192.168.0.1 24\n\t'
    'ipcalc -n 192.168.0.1 250\n\tipcalc -s 192.168.0.1 255.255.0.0')

parser = argparse.ArgumentParser(usage=usage,
                                 description=description,
                                 epilog=epilogue,
                                 formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument(
    'ip',
    metavar='IPv4 address/mask',
    type=str,
    help='CIDR notation of IPv4 address\n192.168.0.1/24')
group = parser.add_mutually_exclusive_group(required=False)
group.add_argument(
    '-c',
    '--cidr',
    metavar='CIDR num',
    type=int,
    help='CIDR number\n24, 32, 16, etc.')
group.add_argument('-n', '--numhost', type=int, help='integer number of hosts')
group.add_argument('-s', '--submask', type=str, help='quad-dotted submask')
parser.add_argument('--version', action='version', version='%(prog)s 1.0')

args = parser.parse_args()

# Set initial values

ip_input = args.ip.split('/')[0]
hosts_input = args.numhost
submask_input = args.submask

try:
    cidr_input = args.ip.split('/')[1]
except IndexError:
    cidr_input = args.cidr


MAX_BIT_INT = 32
MAX_BIT_HEX = 0xFF
MAX_BIT_BIN = 255

big_int = struct.Struct('!I')

# Check to see if the IP address or submask are bad

try:
    IP_32_BIT = big_int.unpack(socket.inet_aton(ip_input))[0]
except socket.error:
    quit('Invalid IPv4 address entered.')

try:
    SM_32_BIT = big_int.unpack(socket.inet_aton(submask_input))[0]
except socket.error:
    quit('Invalid submask entered.')
except TypeError:
    pass


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
    uint32_t = big_int.unpack(socket.inet_aton(submask))[0]

    # http://books.google.com/books?id=iBNKMspIlqEC&pg=PA66#v=onepage&q&f=false
    uint32_t = uint32_t - ((uint32_t >> 1) & 0x55555555)
    uint32_t = (uint32_t & 0x33333333) + ((uint32_t >> 2) & 0x33333333)
    uint32_t = (uint32_t + (uint32_t >> 4)) & 0x0F0F0F0F
    uint32_t = uint32_t + (uint32_t >> 8)
    uint32_t = uint32_t + (uint32_t >> 16)
    return uint32_t & 0x0000003F


def set_base(cidr, hosts, submask):
    """
    Returns the 'base' which is an int which is <= 32 and >= 0
    Represents number of 'set' bits.

    See: Hamming weight

    """
    if None is not cidr:
        try:
            base = int(cidr)
        except ValueError:
            quit('Don\'t include a / unless it\'s immediately followed '
                 'by a valid CIDR prefix')
        return base
    elif None is not hosts:
        base = int(set_bits_from_host(hosts))
        return base
    elif None is not submask:
        base = int(set_bits_from_submask(submask))
        return base


def submask_from_set_bits(base):
    """
    Returns a subnetwork mask from the base

    """
    try:
        mask = ~0 << (32 - base)
    except ValueError:
        quit('CIDR prefix too large.\nMust be <= 32, >= 0.')
    return '{0}.{1}.{2}.{3}'.format(
        mask >> 24 & MAX_BIT_BIN,
        mask >> 16 & MAX_BIT_BIN,
        mask >> 8 & MAX_BIT_BIN,
        mask & MAX_BIT_BIN)

# Set our base to perform calculations
base = set_base(cidr_input, hosts_input, submask_input)

# Try setting submask round two
# Probably could order this better but it's 2 AM and I'm tired
try:
    SM_32_BIT = big_int.unpack(
        socket.inet_aton(
            submask_from_set_bits(base)))[0]
except socket.error:
    quit('Invalid IPv4 address entered.')


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
    bn = ip | (~sm)
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
    pass


def ip_class(ip):
    """
    Returns class of IPv4 address

    """
    ip = big_int.unpack(socket.inet_aton(ip))[0]

    if 0xC0000000 == ip & 0xC0000000:
        return 'Class C'
    elif 0x80000000 == ip & 0x80000000:
        return 'Class B'
    elif 0 == ip & 0x80000000:
        return 'Class A'
    else:
        return False


# Set values we'll be modifying
submask = submask_from_set_bits(base)
network_address = network_addr(SM_32_BIT, IP_32_BIT)
broadcast_address = broadcast_addr(SM_32_BIT, IP_32_BIT)

network_min = '{0}{1}'.format(
    network_address[:-1], int(network_address[-1]) + 1)
network_max = '{0}{1}'.format(
    broadcast_address[:-1], int(broadcast_address[-1]) - 1)

print 'Address:   {0}'.format(ip_input)
print 'Netmask:   {0} = {1}'.format(submask_from_set_bits(base), base)
print 'Wildcard:  {0}'.format(wildcard(base))
print '=============================='
print 'Network:   {0}/{1}'.format(network_address, base)
print 'HostMin:   {0}'.format(network_min)
print 'HostMax:   {0}'.format(network_max)
print 'Broadcast: {0}'.format(broadcast_address)
print 'Subnets:   {0}'.format(subnets(base))
print 'Hosts/Net: {0}\t\t\t{1}'.format(max_hosts(base), ip_class(ip_input))
