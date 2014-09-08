ipcalc
======

<h2>This script is a subnetting calculator that mirrors *nix's ipcalc.</h2>

<p>Originally it was all cool with some super awesome bit shifting but
even though I actually got it to work I decided to drop that in favor
of the C modules socket and struct because it's faster or something.</p>

<p>I miss my bit shifting :(</p>

<h2>Usage:</h2>
```shell
./ipcalc.py [-s | -n] IPv4 address/CIDR prefix
```

Or just add ``--help`` for more information.

- Written by: Eric Lagergren <ericscottlagergren@gmail.com>
- Licensed under the WTFPL <http://www.wtfpl.net/txt/copying/>