# Edensible.py
#
# Name:
# Date:
# Student Number: Mesuvag
#
# Simple ansible imitation.
# Further implementation can be made, I recommend yaml validation,
# e.g. check existence for required variables, task name length limit, host group really exists...
# Could be nicely done with an outer module.
# On bigger scale I think class for each module (with methods for each action) is good,
# but for this scale I chose functions =>
# better readability in my opinion (plus the topic of the hafifa chapter is functions)

import configparser  # For reading INI files (/etc/ansible/hosts file)
import yaml
import re
import paramiko  # YAY IT FINALLY WORKED, needed to upgrade pip

EDENSIBLE_ROOT_FOLDER = r'ENTER YOUR OWN PATH'
SSH_PORT = 22


def file(module, connection):
    """
    File related module.
    Function gets task module with its attributes as a parameter, then extracts needed variables, so in a way:
    Parameters:
        state: state of file, options:
                        touch (make sure exists)
                        directory (make sure directory in such path exists)
                        absent (delete)
        path: path of the object to act on
        module: The module defined in the playbook with its parameters
        connection: ssh client. used to run commands remotely
    returns (task result, message)
    task result possible values: ['OK','CHANGED','FAIL']
    """
    state = module["state"]
    path = module["path"]
    if state == 'touch':
        return run_command(connection, f'touch {path}')

    elif state == 'directory':
        # Check if directory already exists
        stdin, stdout, stderr = connection.exec_command(f'[ -d {path} ] && echo "EXIST" || echo "MISSING"')

        output = stdout.readlines()[0].rstrip()
        # Create directory if missing. return OK if exists
        if "MISSING" == output:
            return run_command(connection, f'mkdir {path}')
        elif "EXIST" == output:
            return 'OK', ''

    elif state == 'absent':
        # Check if file already missing
        stdin, stdout, stderr = connection.exec_command(f'[ -e {path} ] && echo "EXIST" || echo "MISSING"')

        output = stdout.readlines()[0].rstrip()
        if "MISSING" == output:
            return 'OK', ''
        elif "EXIST" == output:
            return run_command(connection, f'rm -rf {path}')

    else:
        return 'FAIL', 'Invalid state. valid values are [touch,directory,absent]'


def shell(module, connection):
    """
    Execute shell commands on remote host
    Function gets task module with its attributes as a parameter, then extracts needed variables, so in a way:
    Parameters:
        cmd: command to execute
        module: The module defined in the playbook with its parameters
        connection: ssh client. used to run commands remotely
    returns (task result, message)
    task result possible values: ['OK','CHANGED','FAIL']
    """
    cmd = module["cmd"]
    return run_command(connection, cmd)


def service(module, connection):
    """
    Service related module.
    Function gets task module with its attributes as a parameter, then extracts needed variables, so in a way:
    Parameters:
        desired_state: state of service, options:
                        started
                        stopped
                        enabled
                        disabled
        name: service name to act on
        module: The module defined in the playbook with its parameters
        connection: ssh client. used to run commands remotely
    returns (task result, message)
    task result possible values: ['OK','CHANGED','FAIL']
    """
    desired_state = module["state"]
    service_name = module["name"]
    pattern = '^(Created|Removed) symlink .*'

    stdin, stdout, stderr = connection.exec_command(f'systemctl is-active {service_name}')
    is_started = 'started' if stdout.readlines()[0].rstrip() == 'active' else 'stopped'

    stdin, stdout, stderr = connection.exec_command(f'systemctl is-enabled {service_name}')
    is_enabled = 'enabled' if stdout.readlines()[0].rstrip() == 'enabled' else 'disabled'

    if desired_state == 'started':
        if is_started == 'stopped':
            return run_command(connection, f'sudo systemctl start {service_name}')
        else:
            return 'OK', ''
    elif desired_state == 'stopped':
        if is_started == 'started':
            return run_command(connection, f'sudo systemctl stop {service_name}')
        else:
            return 'OK', ''
    # For some reason systemctl redirects its regular output to stderr. That means, successful enable/disable
    # has stderr of "Created/Removed"
    elif desired_state == 'enabled':
        if is_enabled == 'disabled':
            result, task_msg = run_command(connection, f'sudo systemctl enable {service_name}')
            if re.match(pattern, task_msg[0]):
                return 'CHANGED', ''
            else:
                return result, task_msg
        else:
            return 'OK', ''
    elif desired_state == 'disabled':
        if is_enabled == 'enabled':
            result, task_msg = run_command(connection, f'sudo systemctl disable {service_name}')
            if re.match(pattern, task_msg[0]):
                return 'CHANGED', ''
            else:
                return result, task_msg
        else:
            return 'OK', ''
    else:
        return 'FAIL', 'Invalid state. valid values are [started, stopped, enabled, disabled]'


def yum(module, connection):
    """
    Package manager module.
    Function gets task module with its attributes as a parameter, then extracts needed variables, so in a way:
    Parameters:
        action: what action to apply on the package name, options:
                        install
                        remove
        package_name: package name
        module: The module defined in the playbook with its parameters
        connection: ssh client. used to run commands remotely
    returns (task result, message)
    task result possible values: ['OK','CHANGED','FAIL']
    """
    action = module["action"]
    package_name = module["name"]

    # Find only "packagename.[extra]". DO NOT find "dependency-packagename.[extra]" or "packagename-dependency.[extra]"
    stdin, stdout, stderr = connection.exec_command(fr'yum list installed | grep -e "^{package_name}\."')
    is_installed = 'EXIST' if stdout.readlines() else 'MISSING'

    if action == 'install':
        if is_installed == 'MISSING':
            return run_command(connection, f'sudo yum install -y {package_name}')
        else:
            return 'OK', ''
    elif action == 'remove':
        if is_installed == 'EXIST':
            return run_command(connection, f'sudo yum remove -y {package_name}')
        else:
            return 'OK', ''
    else:
        return 'FAIL', 'Invalid action. valid values are [install, remove]'


def edensible_step_print(action, name, line_size=80):
    """
    Print in ansible format (action type, action name, and asterisks till the end).
    Parameters:
        action: the action type, such as PLAY, TASK...
        name: action name
        line_size: required to know how many asterisks to repeat
    returns nothing.
    """
    print(f'{action} {name} {"*"*(line_size-len(action)-len(name))}')


def get_valid_ssh(connection, hosts, username, password, port=22):
    """
    Try to connect to all hosts, return only successful connections
    Parameters:
        connection: ssh client
        hosts: list of hosts to try to connect to
        username: username to use for ssh connection
        password: password to use for ssh connection
        port: port to ssh to, defaults to 22
    returns list of successful connections, empty if none succeeded.
    """
    valid_connections = []
    for host in hosts:
        try:
            connection.connect(host, port, username, password)
            valid_connections.append(host)
        except:
            print(f'Connection to {host} failed')
    return valid_connections


def get_module_name(task, allowed_modules):
    """
    Function to get module name in task
    Parameters:
        task: ssh client
        allowed_modules: list of hosts to try to connect to
    returns module_name if found, False if 0 or 2 or more modules were given in the same task
    """
    module_name = False
    for attr in task:

        # Is the attribute the module name?
        if attr in allowed_modules:

            # module_name is already defined? means that two modules are given!
            if module_name:
                print('Only one module is allowed in a single task!')
                return False
            module_name = attr
    return module_name


def run_command(connection, cmd):
    """
    Execute commands on remote host
    Parameters:
        cmd: command to execute
        connection: ssh client. used to run commands remotely
    returns (task result, message)
    task result possible values: ['OK','CHANGED','FAIL']
    """
    stdin, stdout, stderr = connection.exec_command(f'{cmd}')
    errors = stderr.readlines()
    if errors:
        return 'FAIL', errors
    else:
        return 'CHANGED', ''


def main():
    # Modules dict must be defined after functions definitions
    MODULE_DICT = {
        "file": file,
        "shell": shell,
        "service": service,
        "yum": yum
    }

    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load playbook to python-convenient format.
    with open(f'{EDENSIBLE_ROOT_FOLDER}/main.yml', 'r') as play_file:
        playbooks = yaml.safe_load(play_file)

    # Loop on playbooks
    for playbook in playbooks:
        edensible_step_print('PLAY', f'[{playbook["name"]}]')
        results_recap = {}

        hosts_group = playbook["hosts"]
        # Get hosts addresses and connection-related variables from hosts file
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(f'{EDENSIBLE_ROOT_FOLDER}/hosts')

        hosts = [host for host in config[hosts_group]]
        edensible_user = config[f"{hosts_group}:vars"]["edensible_user"]
        edensible_pass = config[f"{hosts_group}:vars"]["edensible_password"]

        valid_ssh = get_valid_ssh(connection, hosts, edensible_user, edensible_pass)

        if valid_ssh:

            # Execute each task
            for task in playbook["tasks"]:
                edensible_step_print('TASK', f'[{task["name"]}]')

                module_name = get_module_name(task, MODULE_DICT)

                if module_name:

                    # Run only on valid connection hosts
                    for host in valid_ssh:

                            # Create connection
                            connection.connect(host, SSH_PORT, edensible_user, edensible_pass)
                            # Run appropriate function
                            result, task_msg = MODULE_DICT[module_name](task[module_name], connection)

                            if host not in results_recap:
                                results_recap[host] = {'FAILED': 0, 'CHANGED': 0, 'OK': 0}

                            if result == 'FAIL':
                                print(f'{result}: [{host}] => {task_msg}')
                                results_recap[host]['FAILED'] += 1
                                # Remove host from valid hosts. Don't run any more tasks on this host
                                valid_ssh.remove(host)
                            elif result == 'CHANGED':
                                print(f'{result}: [{host}]')
                                results_recap[host]['CHANGED'] += 1
                            else:
                                print(f'{result}: [{host}]')
                                results_recap[host]['OK'] += 1
                else:
                    # if module_name is empty, means no task attribute matched the valid modules dict
                    print('No valid module was given in the task, maybe you have a typo?')
        else:
            print('No valid hosts, continuing to next play')

        edensible_step_print('PLAY', 'RECAP')
        for host in results_recap:
            print(f'{host}', end=' ------------- ')
            for status_type in results_recap[host]:
                print(f'{status_type}={results_recap[host][status_type]}', end='   ')

        print('')


if __name__ == '__main__':
    main()
