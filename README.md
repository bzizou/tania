## A greedy processes killer

Tania is a python program designed to kill processes that should not be there 
on a server hosting many users sessions, like a computing cluster's frontend, 
generally because users forgot (or do not know how to) launch their program into a 
proper job. You can customize which processes should be monitored (targets) and 
which should be whitelisted (allies), based on their name, owner, cputime and 
memory size (rss).
Tania is designed to be run as a cron job and can send e-mails to the users having
their processes shot down. A warning threshold can be set-up before the actual kill 
to send a warning e-mail.

### Installation


Install tania:

```bash
git clone https://github.com/bzizou/tania
cd tania
pip install .
```

Copy `etc/tania.conf` and `etc/tania_targets.json` to an appropriate location, for
example `/etc`, and customize those files. 
You can set up the `$TANIA_CONF_FILE` variable if you placed the config file
into another location than /etc.

```bash
sudo cp etc/tania.conf /etc
sudo cp etc/tania_targets.json /etc
# Edit tania.conf and tania_targets.json
# WARNING: tania can kill system processes if not configured properly!
```

### Usage

```
~# tania --help
Usage: tania [options]

Options:
  -h, --help     show this help message and exit
  -D, --do       Actualy do kill bad processes
  -v, --verbose  Be more verbose
  -m, --mail     Send an email to the familly of the deceased
```

By default, tania does nothing and only prints the PID of the processes that should be killed:

```bash
~# tania               
Warning: 1827444 is in the viewfinder 
Warning: 210765 is in the viewfinder  
Warning: 3317806 is in the viewfinder 
```

You can print more informations, to know the reasons of the kills:

```bash
~# tania -v
We should kill 1670118 ( yes ) of bzizou with cputime 4 (limit  1 )
We should kill 1666340 ( stress-ng-vm [run] ) of bzizou with memory 212292 (limit  200000 )
```

To actually kill the processes, use `--do`:

```bash
~# tania --do
Shooting down process 1670118
```

The `--mail` option will send an e-mail to the owner of the killed process using the mail templates
from the config file.

Finally, Tania is meant to be run frequently from cron. Here's an example cron job configuration:

```
# cat /etc/cron.d/tania                                  
*/2 * * * * root /usr/local/bin/tania --do --mail |grep -v Warning
```

### Configuring targets

The `tania.conf` file is self-explanatory; just follow the comments.

The json targets file (`tania_targets.json` by default) contains 2 types of entries: 
*ally* or *target*. An ally is simply a process that should never be killed. 

Targets and allies are defined by a *cmd* and a *user* string. Those strings are
regular expressions.

Here's an ally example meaning that all Nextflow processes of the user Goldorak should never be killed:

```
{
    "type": "ally",
    "cmd": "^.*nextflow.*",
    "user": "goldorak"
},
```

Targets have *time_limit*, *time_limit_warn* and *rss_limit* definitions.
* time_limit: Max CPU time in seconds at which a process should be killed
* time_limit_warn: CPU time in seconds at which warning e-mail should be sent to the user
* rss_limit: Max memory limit that a process can use before being killed

Here's a default configuration to kill every processes that use more than 600s of cpu time with
a warning at 300s of cpu time, and maximum memory use of 1GB:

```
{
     "type": "target",
     "cmd": ".*",
     "user": ".*",
     "time_limit": 600,
     "time_limit_warn": 300,
     "rss_limit": 1000000
}
```

WARNING: You should generally keep all system processes as ally with such an entry:

```
{
    "type": "ally",
    "cmd": ".*",
    "user": "^root$|^postgres$|^apache2$|^avahi$|^messagebus$|^polkituser$|^systemd.*|^rtkit$|^openldap$|^oar$|^bind$|^nut$|^www-data$|^flexlm$|^ntp$|^statd$|^oident$|^nslcd$|^nscd$|^haldaemon$|^munge$|^dbus$|^rpc$|^_fluentd$|^calyptia-fluent$"
},
```

Add more users to the list if necessary.

### Why this name "Tania" ?

Check https://en.wikipedia.org/wiki/Tania_Chernova
