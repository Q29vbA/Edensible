# Edensible
Cute small ansible mimic, <br />
Part of hafifa. <br />
Named after hofefet Eden

## Overview

main.yml could be YAML or JSON format. <br />
As with YAML, comment using '#'. <br />

File tree is as below: <br />
EDENSIBLE_ROOT_FOLDER <br />
└─── main.yml <br />
└─── hosts

## Hosts file format
[host_group_name] <br />
IP/FQDN1 <br />
IP/FQDN2 <br />
... <br />
[another_host_group_name] <br />
IP/FQDN3 <br />
IP/FQDN4 <br />
... <br />
[host_group_name:vars] <br />
edensible_user={username-to-login-with} <br />
edensible_password={password-of-username} <br />
[another_host_group_name:vars] <br />
edensible_user={username-to-login-with} <br />
edensible_password={password-of-username} <br />


## Modules

### file
Parameters: <br />
	state: state of file, options: <br />
	  - touch (make sure exists) <br />
	  - directory (make sure directory in such path exists) <br />
	  - absent (delete) <br />
	path: path of the object to act on

### shell
Parameters: <br />
	cmd: command to execute

### service
Parameters: <br />
	state: state of service, options: <br />
	  - started <br />
	  - stopped <br />
	  - enabled <br />
	  - disabled <br />
	name: service name to act on

### yum
Parameters: <br />
	action: what action to apply on the package name, options: <br />
	  - install <br />
	  - remove <br />
	name: package name

