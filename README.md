## A simple script to automatically kill greedy processes

Tania is a python script designed to kill processes that should not be there 
on a computing cluster's frontend, generally because users forgot (or do not 
know how to) launch their program into a proper job.
You can customize which processes should be monitored (targets) and which should
be whitelisted (allies), based on their name, owner, cputime and memory size (rss). 

### Installation


Install tania:

```bash
git clone https://github.com/bzizou/tania
cd tania
pip install .
```

Copy `tania.conf` and `tania_targets.json` to an appropriate location, for
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
tania --help
Usage: tania [options]

Options:
  -h, --help     show this help message and exit
  -D, --do       Actualy do kill bad processes
  -v, --verbose  Be more verbose
  -m, --mail     Send an email to the familly of the deceased
```

By default, tania does nothing and only prints the PID of the processes that should be killed:

```bash
root@f-dahu:~# tania               
Warning: 1827444 is in the viewfinder 
Warning: 210765 is in the viewfinder  
Warning: 3317806 is in the viewfinder 
```

You can print more informations, to know the reasons of the kills:

```bash
root@dahu:~# tania -v
We should kill 1670118 ( yes ) of bzizou with cputime 4 (limit  1 )
We should kill 1666340 ( stress-ng-vm [run] ) of bzizou with memory 212292 (limit  200000 )
```

To actually kill the processes, use `--do`:

```bash
root@dahu:~# tania --do
Shooting down process 1670118
```

The `--mail` option will send an e-mail to the owner of the killed process using the mail templates
from the config file.

Finally, Tania is meant to be run frequently from cron. Here's an example cron job configuration:

```
# cat /etc/cron.d/tania                                  
*/2 * * * * root tania --do --mail |grep -v Warning
```

