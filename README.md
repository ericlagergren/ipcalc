ipcalc
======
[![Build Status](https://travis-ci.org/EricLagerg/ipcalc.svg?branch=master)](https://travis-ci.org/EricLagerg/ipcalc)

<h2>This script is a subnetting calculator that mirrors *nix's ipcalc.</h2>

<p>This script allows you to perform IPv4 subnetting calculations.</p>


<h2>Usage:</h2>
```shell
# Optional
ln -s /usr/bin ipcalc.py

ipcalc [-n HOSTS | -p COLORS] [IPv4 address]/[mask] [submask OPTIONAL]
```

<h2>Example:</h2>
```shell
eric@crunchbang ~/sbdmn/ipcalc $ ipcalc -n 250 192.168.0.0
Address:   192.168.0.0
Netmask:   255.255.255.0 = 24
Wildcard:  0.0.0.255
3232235520
Class:     Class C (Private RFC1918)
-->
Network:   192.168.0.0/24
HostMin:   192.168.0.0
HostMax:   192.168.0.254
Broadcast: 192.168.0.255
Subnets:   256
Hosts/Net: 254

eric@crunchbang ~/sbdmn/ipcalc $ ipcalc 192.168.0.0/24
Address:   192.168.0.0
Netmask:   255.255.255.0 = 24
Wildcard:  0.0.0.255
3232235520
Class:     Class C (Private RFC1918)
-->
Network:   192.168.0.0/24
HostMin:   192.168.0.0
HostMax:   192.168.0.254
Broadcast: 192.168.0.255
Subnets:   256
Hosts/Net: 254
```

Or just add ``--help`` for more information.

- Written by: Eric Lagergren <ericscottlagergren@gmail.com>
- Licensed under the WTFPL <http://www.wtfpl.net/txt/copying/>