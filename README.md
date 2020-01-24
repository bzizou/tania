## a simple script to automatically kill greedy processes

### Installation

Copy `tania.conf` and `tania_targets.json` to an appropriate location, for
example `/etc`, and customize those files. Put the `tania.py` into a location
for executable scripts, for example into `/usr/local/sbin`.

You can set up the `$TANIA_CONF_FILE` variable if you placed the config file
into another location than /etc.

### Usage

```
tania.py --help
Usage: tania [options]

Options:
  -h, --help     show this help message and exit
  -D, --do       Actualy do kill bad processes
  -v, --verbose  Be more verbose
  -m, --mail     Send an email to the familly of the deceased
```