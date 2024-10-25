#!/usr/bin/env python3
# Tania Chernova (a Russian-American) and her group went to Stalingrad by
# traveling through the sewer system to reach the Russian lines. After
# that, she joined Vasily Zaytsev's sniper school and became a sniper.
#
# Tania is a python script designed to kill processes that should not
# be there on a computing cluster's frontend, generally because users
# forgot (or do not know how to) launch their program into a proper job.
#
# TODO make stateful to kill a process if already identified and still runs
# despite a first term
# store pid, uid, timestamp, process, status in pickle and load on re-run

import json
import sys,os,time,re
import configparser
import subprocess
import re
from optparse import OptionParser
import smtplib
import hashlib
import pathlib
from os import path
from filelock import Timeout, FileLock

# Configuration file opening
config=configparser.ConfigParser()
DEFAULT_CONFIG_FILE="/etc/tania.conf"
try:
    if not os.path.isfile(os.environ['TANIA_CONF_FILE']):
        raise
except:
    if os.path.isfile(DEFAULT_CONFIG_FILE):
        config.read(DEFAULT_CONFIG_FILE)
    else:
        sys.stderr.write("Error: could not load configuration file!\n")
        sys.stderr.write("The configuration file is searched into "+DEFAULT_CONFIG_FILE+" or in the location given by the $TANIA_CONF_FILE environment variable\n")
        sys.exit(1)
else:
    config.read(os.environ['TANIA_CONF_FILE'])

# Get some variables from the configuration file
TARGETS_FILE=config.get('general','targets_file')
PS_CMD=config.get('general','ps_cmd',raw=True)
RSS_PS_CMD=config.get('general','rss_ps_cmd',raw=True)
TMPDIR=config.get('general','tmp_dir')+"/tania"

# Options parsing
parser = OptionParser()
parser.add_option("-D", "--do",
                  action="store_true", dest="do", default=False,
                  help="Actualy do kill bad processes")
parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="Be more verbose")
parser.add_option("-m", "--mail",
                  action="store_true", dest="send_mail", default=False,
                  help="Send an email to the familly of the deceased")
(options, args) = parser.parse_args()


def get_top_processes(cmd) :
    """
        Get the list of running processes as a list of dict (cputime)
    """
    run_string = cmd
    if cmd == "BUILT-IN":
      run_string = "ps -Ao 'pid,time,user:100,command:100000' --sort=-cputime |head -200"
    task = subprocess.Popen(run_string, shell=True, stdout=subprocess.PIPE)
    data = task.stdout.read()
    assert task.wait() == 0
    data = data.decode().split('\n')
    processes=[]
    if cmd == "BUILT-IN":
      for string in data:
        string=string.lstrip()
        p = re.split(r"[\s\t]+", string, 3)
        p = [x.strip(' ') for x in p]
        if len(p) == 4 and p[1] != "TIME":
          processes.append({
                'pid' : p[0],
                'cputime' : p[1],
                'user' : p[2],
                'cmd' : p[3]
          })
    else:
      for string in data:
        p = string.split(':::')
        p = [x.strip(' ') for x in p]
        if len(p) == 4 and p[2] != "TIME":
          processes.append({
                'cmd' : p[0],
                'pid' : p[1],
                'cputime' : p[2],
                'user' : p[3]
          })
    return processes

def get_hungry_processes(cmd) :
    """
        Get the list of running processes as a list of dict (rss)
    """
    run_string = cmd
    if cmd == "BUILT-IN":
      run_string = "ps -Ao 'pid,rss,user:100,command:100000' --sort=-rss |head -200"
    task = subprocess.Popen(run_string, shell=True, stdout=subprocess.PIPE)
    data = task.stdout.read()
    assert task.wait() == 0
    data = data.decode().split('\n')
    processes=[]
    for string in data:
      string=string.lstrip()
      p = re.split(r"[\s\t]+", string, 3)
      p = [x.strip(' ') for x in p]
      if len(p) == 4 and p[1] != "RSS":
        processes.append({
              'pid' : p[0],
              'rss' : int(p[1]),
              'user' : p[2],
              'cmd' : p[3]
        })
    return processes


def load_targets(targets_file) :
    """
       Load the target file
    """
    with open(targets_file) as json_file:
        return json.load(json_file)

def send_mail(mail_template,login,command,pid,value,limit) :
    """
        Send an email to the owner of the process
    """
    cmd = config.get('mail','get_email').replace("[login]",login)
    task = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dest = task.stdout.read().decode().strip('\n').strip(' ')
    dest_err = task.stderr.read().decode().strip('\n').strip(' ')
    assert task.wait() == 0
    mail = config.get('mail',mail_template)
    mail_from = config.get('mail','smtp_from')
    mail_cc = config.get('mail','smtp_cc')
    subject = config.get('mail','subject')
    mail = "Subject: "+subject+"\n\n"+mail
    mail = "From: "+mail_from+"\n"+mail
    if dest != "" :
        mail = "Cc: "+mail_cc+"\n"+mail
        mail = "To: "+dest+"\n"+mail
        dests = [dest] + [mail_cc]
    else:
        print("Could not get the e-mail address of",login, file=sys.stderr)
        if options.verbose :
            print("Cmd:",cmd, file=sys.stderr)
            print("Warning:",dest_err, file=sys.stderr)
        mail = "To: "+mail_cc+"\n"+mail
        dests = [mail_cc]
    mail = mail.replace("[pid]",str(pid))
    mail = mail.replace("[cputime]",str(value))
    mail = mail.replace("[rss]",str(value))
    mail = mail.replace("[command]",str(command))
    mail = mail.replace("[limit]",str(limit))
    server = smtplib.SMTP()
    server.connect(config.get('mail','smtp_server'))
    server.sendmail(mail_from, dests, mail)

# Main
def main():
  processes = get_top_processes(PS_CMD)
  rss_processes = get_hungry_processes(RSS_PS_CMD)
  all_processes = processes + rss_processes
  targets = load_targets(TARGETS_FILE)
  pathlib.Path(TMPDIR).mkdir(parents=True, exist_ok=True)
  
  lock = FileLock(TMPDIR+"/lock", timeout=10)
  
  try:
      with lock.acquire():
          for process in all_processes:
              p_pid=process['pid']
              p_cmd=process['cmd']
              p_user=process['user']
              if 'cputime' in process:
                p_time=process['cputime']
                p_rss=0
              else:
                p_rss=process['rss']
                p_time="0:0:0"
              for target in targets:
                  # Does the user match?
                  user=re.search(target['user'],p_user)
                  # Does the cmd match?
                  cmd=re.search(target['cmd'],p_cmd)
                  # Is it an ally?
                  if user and cmd and target['type']=='ally':
                      break
                  # Is it a target?
                  if target['type']=='target':
                      # Convert cputime into seconds
                      m=re.search("(.*)-(.*:.*:.*)",p_time)
                      if m :
                          cputime=86400*int(m.group(1))
                          cputime+=sum(x * int(t) for x, t in zip([3600, 60, 1], m.group(2).split(":")))
                      else :
                          cputime=sum(x * int(t) for x, t in zip([3600, 60, 1], p_time.split(":")))
                      if user and cmd :
          
                          # Compute a hash filename that will be used to keep track of already sent mail
                          file_hash=hashlib.md5((p_user+p_cmd+p_pid).encode()).hexdigest()
          
                          # Does the cpu time exceeds the warn limit?
                          if 'time_limit_warn' in target and cputime>=target['time_limit_warn'] and cputime<target['time_limit']:
                              if options.verbose :
                                  print('Process',p_pid, "(",p_cmd,") of",p_user,"used cputime",cputime, "(limit ",target['time_limit'],")")
                              else :
                                  print('Warning:',p_pid,"is in the viewfinder")
                              warn_file=TMPDIR+"/warn_"+file_hash
                              if options.do and options.send_mail and not path.exists(warn_file):
                                  send_mail('warn_mail',p_user,p_cmd,p_pid,cputime,target['time_limit'])
                                  pathlib.Path(warn_file).touch()
          
                          # Does the cpu time exceeds the limit?
                          if cputime>target['time_limit']:
                              if options.do :
                                  if options.verbose:
                                      print('Shooting down',p_pid, "(",p_cmd,") of",p_user,"with cputime",cputime, "(limit ",target['time_limit'],")")
                                  # Shoot down
                                  if not options.verbose : print('Shooting down process',p_pid)
                                  subprocess.run(["kill", p_pid])
                                  # Send e-mail
                                  kill_file=TMPDIR+"/kill_"+file_hash
                                  if options.send_mail and not path.exists(kill_file) :
                                      send_mail('kill_mail',p_user,p_cmd,p_pid,cputime,target['time_limit'])
                                      pathlib.Path(kill_file).touch()
                                      print()
                              else :
                                  if options.verbose :
                                      print('We should kill',p_pid, "(",p_cmd,") of",p_user,"with cputime",cputime, "(limit ",target['time_limit'],")")
                                  else :
                                      print('We should kill process',p_pid)
  
                          # Does the memory exceeds the limit?
                          if 'rss_limit' in target and p_rss>target['rss_limit']:
                              if options.do :
                                  if options.verbose:
                                      print('Shooting down',p_pid, "(",p_cmd,") of",p_user,"with memory",p_rss, "(limit ",target['rss_limit'],")")
                                  # Shoot down
                                  if not options.verbose : print('Shooting down process',p_pid)
                                  subprocess.run(["kill", p_pid])
                                  # Send e-mail
                                  kill_file=TMPDIR+"/kill_"+file_hash
                                  if options.send_mail and not path.exists(kill_file) :
                                      send_mail('rss_kill_mail',p_user,p_cmd,p_pid,p_rss,target['rss_limit'])
                                      pathlib.Path(kill_file).touch()
                                      print()
                              else :
                                  if options.verbose :
                                      print('We should kill',p_pid, "(",p_cmd,") of",p_user,"with memory",p_rss, "(limit ",target['rss_limit'],")")
                                  else :
                                      print('We should kill process',p_pid)
                          break
  except Timeout:
      print("Another instance of Tania currently holds the lock.")

if __name__ == '__main__':
        main()
