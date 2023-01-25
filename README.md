# Edensible
Cute small ansible mimic,
Part of hafifa.
Named after hofefet Eden

## Overview

main.yml could be YAML or JSON format.
As with YAML, comment using '#'.

File tree is as below:
EDENSIBLE_ROOT_FOLDER
└─── main.yml
└─── hosts

## Hosts file format
[host_group_name]
IP/FQDN1
IP/FQDN2
...
[another_host_group_name]
IP/FQDN3
IP/FQDN4
...
[host_group_name:vars]
edensible_user={username-to-login-with}
edensible_password={password-of-username}
[another_host_group_name:vars]
edensible_user={username-to-login-with}
edensible_password={password-of-username}


## Modules

### file
Parameters:
	state: state of file, options:
	  - touch (make sure exists)
	  - directory (make sure directory in such path exists)
	  - absent (delete)
	path: path of the object to act on

### shell
Parameters:
	cmd: command to execute

### service
Parameters:
	state: state of service, options:
	  - started
	  - stopped
	  - enabled
	  - disabled
	name: service name to act on

### yum
Parameters:
	action: what action to apply on the package name, options:
	  - install
	  - remove
	name: package name

