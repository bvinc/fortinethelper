#!/usr/bin/env python3
import os, sys, time
import re
import pexpect
import subprocess
import configparser

# Create a file named fortinethelper.ini that looks like:
#
# [VPN]
# Path: ./forticlientsslvpn/64bit/forticlientsslvpn_cli
# Server: vpn.mycompany.com:443
# User: myusername
# Pass: mypassword

CONFIG_FILE = "fortinethelper.ini"

def find_gateway_ip():
	output = subprocess.check_output(["route", "-n"]).decode("utf-8")
	m = re.search(r"0.0.0.0\s+(10\.[0-9]+\.[0-9]+\.[0-9]+).*ppp", output)
	ip = m.group(1)
	return ip

if os.geteuid() != 0:
	print("Must run as root")
	sys.exit(1)

# Read the config file
config = configparser.ConfigParser()
config.read(CONFIG_FILE)
path = config.get("VPN", "Path")
server = config.get("VPN", "Server")
user = config.get("VPN", "User")
passw = config.get("VPN", "Pass")

# Launch the forticlient ssl vpn cli
vpn = pexpect.spawn('%s --server %s --vpnuser %s' % (path, server, user) )
vpn.expect("Password for VPN:")
vpn.sendline(passw)
print("Sent pass")
vpn.expect('connect to this server?')
vpn.sendline('Y')
print("Sent Y")
vpn.expect('Connected')
print("Connected")
vpn.expect('Tunnel running')
print("Tunnel running.  Sleeping 10 seconds...")
time.sleep(10)

# Undo forticlient changes to the resolv.conf file
print("Removing fortigate added nameservers from resolv.conf")
os.system('''cp /etc/resolv.conf /etc/resolv.conf.fortisucks''')
os.system('''egrep -v 'nameserver[[:space:]]*10\.' /etc/resolv.conf > /etc/resolv.conf.fortifix''')
os.rename("/etc/resolv.conf.fortifix", "/etc/resolv.conf")

# Remove the default route, only route specific ip ranges
print("Removing default route")
ip = find_gateway_ip()
print("Found gateway ip: %s" % ip)
subprocess.check_call(["route", "add", "-net", "10.0.0.0/8", "gw", ip])
subprocess.check_call(["route", "del", "-net", "0.0.0.0", "gw", ip])

os.system('route -n')

vpn.interact()
