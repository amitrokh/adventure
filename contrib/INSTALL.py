#!/usr/bin/python
# Author: Anton Mitrokhin, MIPT-UMD 2014-2017


class bcolors:
    HEADER = '\033[95m'
    PLAIN = '\033[37m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def offset(str_, p_offset):
    for i in xrange(p_offset):
        str_ = '...' + str_
    return str_

def hdr(str_, p_offset=0):
    return offset(bcolors.HEADER + str_ + bcolors.ENDC, p_offset)

def wht(str_, p_offset=0):
    return offset(bcolors.PLAIN + str_ + bcolors.ENDC, p_offset)

def okb(str_, p_offset=0):
    return offset(bcolors.OKBLUE + str_ + bcolors.ENDC, p_offset)

def okg(str_, p_offset=0):
    return offset(bcolors.OKGREEN + str_ + bcolors.ENDC, p_offset)

def wrn(str_, p_offset=0):
    return offset(bcolors.WARNING + str_ + bcolors.ENDC, p_offset)

def err(str_, p_offset=0):
    return offset(bcolors.FAIL + str_ + bcolors.ENDC, p_offset)

def bld(str_, p_offset=0):
    return offset(bcolors.BOLD + str_ + bcolors.ENDC, p_offset)


import sys, os, subprocess, argparse
import getpass


# System related stuff
ROS_INSTALL_DIR = "/opt/ros/indigo"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LOCAL_BASH_FILE = ROOT_DIR + "/devel/setup.bash"
LAUNCHER_DIR = ROOT_DIR + "/contrib/launchers_gen/"
HOME_DIR = os.path.expanduser("~")
USERNAME = getpass.getuser()

# Startup related stuff
DEVS_TO_WAIT = ['/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AL00CIPJ-if00-port0', 
                '/dev/serial/by-id/usb-Yujin_Robot_iClebo_Kobuki_kobuki_A601D9PH-if00-port0']
WIFI_NAME = 'adventure-wifi'


# Append this line to autogenerated strings
GENERATOR_MARKER = ' # Generated by ADVENTURE-INSTALL-PY' 

DEPS = ["ros-indigo-ros-control", 
        "ros-indigo-rosserial",
        "ros-indigo-openni-launch",
        "ros-indigo-imu-filter-madgwick",
        "ros-indigo-realsense-camera",
        "ros-indigo-arbotix"]

try:
    CMAKE_PREFIX_PATH=os.environ["CMAKE_PREFIX_PATH"]
except:
    CMAKE_PREFIX_PATH=""

try:
    ROS_HOSTNAME=os.environ["ROS_HOSTNAME"]
except:
    ROS_HOSTNAME=""

try:
    ROS_MASTER_URI=os.environ["ROS_MASTER_URI"]
except:
    ROS_MASTER_URI=""

try:
    GAZEBO_MODEL_PATH=os.environ["GAZEBO_MODEL_PATH"]
except:
    GAZEBO_MODEL_PATH=""

try:
    ADVENTURE_SIMULATION=os.environ["ADVENTURE_SIMULATION"]
except:
    ADVENTURE_SIMULATION="false"

def print_info():
    print bld(wht("\nDEPLOY SCRIPT FOR ADVENTURE PROJECT"))
    print bld(wht("author: Anton Mitrokhin, 2014-2017"))
    print bld(wrn("Warning! "))+wht("This script assumes you had installed ROS Indigo to the ")+okb("'"+ROS_INSTALL_DIR+"'")
    print wht("")
    print wht("Workspace root directory: ")+okb(ROOT_DIR)
    print wht("Launcher bash scripts directory: ")+okb(LAUNCHER_DIR)
    print wht("")
    print wht("Compilation setup:")
    print hdr("CMAKE_PREFIX_PATH")+wht(": ")+okb(CMAKE_PREFIX_PATH)
    print wht("Network setup:")
    print hdr("ROS_HOSTNAME")+wht(": ")+okb(ROS_HOSTNAME)
    print hdr("ROS_MASTER_URI")+wht(": ")+okb(ROS_MASTER_URI)
    if (ROS_HOSTNAME == "" or ROS_MASTER_URI == ""):
        print err("Network setup is incomplete!")
        print wht("Set up ")+hdr("ROS_HOSTNAME")+wht(" and ")+hdr("ROS_MASTER_URI")+wht(" system variables")    
    print wht("")
    print wht("Other environment variables:")
    print hdr("GAZEBO_MODEL_PATH")+wht(": ")+okb(GAZEBO_MODEL_PATH)
    print hdr("ADVENTURE_SIMULATION")+wht(": ")+okb(ADVENTURE_SIMULATION)
    print wht("")

class BashFile(object):
    def __init__(self, path):
        self.path = path
        try:
            f = open(path, 'r')
            self.contents = f.readlines()
            f.close()
        except IOError:
            raise IOError("could not open file for read: " + path) 

    def __contains__(self, key):
        for line in self.contents:
            if self.line2simple(key) == self.line2simple(line):
                return True
        return False

    def __add__(self, line):
        if (line not in self):
            self.contents.append(line)
            self.writeout()
            print okg("[ADDED]: ") + wht(self.line2simple(line))
        else:
            print okg("[OK]: ") + wht(self.line2simple(line))
        return self

    def __iadd__(self, line):
        return self.__add__(line)

    def __radd__(self, line):
        if (line not in self):
            self.contents.insert(0, line)
            self.writeout()
            print okg("[ADDED]: ") + wht(self.line2simple(line))
        else:
            print okg("[OK]: ") + wht(self.line2simple(line))
        return self

    def writeout(self):
        try:
            f = open(self.path, 'w')
            f.writelines(self.contents)
        except IOError:
            raise IOError("could not open file for write: " + path)
        finally:
            f.close()
    
    def line2simple(self, line):
        '''
        Simplify the bash code line in terms of bash syntax
        (remove comments, trailing spaces, etc.)
        '''
        return line.partition('#')[0].strip(' \n')

    def regexpRemove(self, regexp):
        '''
        Remove lines which match given regular expression
        return the tuple containing removed lines
        '''
        import re
        removed = []
        for line in self.contents:
            if re.match(regexp, line):
                removed.append(line)
        for line in removed:
            self.contents.remove(line)
        self.writeout()
        return removed

bashrc = BashFile(HOME_DIR + '/.bashrc')

def ensure_dir(f):
    if not os.path.exists(f):
        print okg("Created directory: ") + okb(f)
        os.makedirs(f)

def exec_command(cmd_, silent=False):
    if not silent:
        print bld(okb("Executing bash commands:"))
        print hdr(cmd_+"...")
    try:
        result = subprocess.check_output(["bash", "-c", cmd_])
        if not silent:
            print wht(result)
   
    except subprocess.CalledProcessError as e:
        print bld(err("Error while executing '"+str(e.cmd)+
                      "': the return code is "+str(e.returncode)+": "+str(e.output)))
        print bld(wrn("If you want to return to this place restart the script."))
        return [1, ""]

    except:
        print bld(err("Something has went wrong! (" + str(sys.exc_info()) + ")")) 
        print bld(wrn("If you want to return to this place restart the script."))
        return [1, ""]
    return [0, result]

def query(str_):
    valid = {"y": True, "n": False}
    sys.stdout.write(str_)
    while True:
        clr_str = ""
        choice = raw_input().lower()
        if choice in valid:
            return valid[choice]
        else:
            if (choice == ''): choice = ' '
            sys.stdout.write('\033[1A'+'\033['+str(len(str_))+'C')
            for l in choice: clr_str = clr_str + " "
            sys.stdout.write(clr_str)
            sys.stdout.write('\033['+str(len(clr_str))+'D')

def cleanup():
    print bld(wht("Cleaning up..."))
    removed = bashrc.regexpRemove('.*' + GENERATOR_MARKER)
    
    if (len(removed) != 0):
        print wht("Removed ", 1)+err(str(len(removed)))+wht(" autogenerated lines from .bashrc")
    
    SHORTCUT_BASE_PATH = HOME_DIR + '/.local/share/applications/'
    if not os.path.exists(SHORTCUT_BASE_PATH):
        print wht("")
        return

    print wht("Removing shortcuts:", 1) 
    for name in os.listdir(SHORTCUT_BASE_PATH):
        if '_ad_gen.desktop' in name:
            os.remove(SHORTCUT_BASE_PATH + name)
            print wht("removed ", 2) + okb(name)
    print wht("")

def init_workspace():
    try:
        os.remove(ROOT_DIR + "/src/CMakeLists.txt")
    except:
        pass

    print "\nInitializing ROS workspace at " + ROOT_DIR + "/src";
    result = exec_command("source "+ ROS_INSTALL_DIR + "/setup.bash " +
                          "&& cd " + ROOT_DIR + "/src && catkin_init_workspace")

    if (result[0] != 0):
        print bld(err("Unable to execute catkin_init_workspace. Have you installed ROS?"))
        exit(1)

# Write 'format_str' to 'file_path' properly
def write_file_safely(file_path, format_str):
    try:
        bash_scipt_file = open(file_path, 'w+')
        bash_scipt_file.write(format_str)
        os.chmod(file_path, 0775)
        print okg("Written to ")+okb(file_path)
    except:
        print bld(err("Error creating "))+okb(file_path)
        print bld(err(sys.exc_info()))
        exit(1)

def write_file_safely_root(file_path, format_str):
    write_file_safely(HOME_DIR+"/.INSTALLPY_tmp", format_str)
    result = exec_command("sudo mv "+HOME_DIR+"/.INSTALLPY_tmp "+file_path)
    if (result[0] != 0):
        print bld(err("Aborting..."))
        try:
            os.remove(HOME_DIR+"/.INSTALLPY_tmp")
        except:
            print bld(err("Unable to remove "))+okb(file_path)
            print bld(err(sys.exc_info()))
            print bld(err("This is strange. You better remove it manually then..."))
        exit(1)
        

# Generates a shortcut. (Like alacarte utilite)
def add_shortcut(name, icon, command):
    if not os.path.isfile(icon):
        print bld(err("No such icon: ")) + okb(icon)
        exit(1)

    SHORTCUT_BASE_PATH = HOME_DIR + '/.local/share/applications/'
    ensure_dir(SHORTCUT_BASE_PATH)
    file_path = SHORTCUT_BASE_PATH + name + '_ad_gen.desktop'
    format_str = '#!/usr/bin/env xdg-open\n\n'\
                 '[Desktop Entry]\n'\
                 'Version=1.0\n'\
                 'Type=Application\n'\
                 'Terminal=true\n'\
                 'Name=' + name + '\n'\
                 'Icon=' + icon + '\n'\
                 'Exec=' + command
    write_file_safely(file_path, format_str)

def gen_bash_header(logfile=""):
    if (logfile == ""): logfile="/dev/tty"
    format_str = ("#!/bin/bash\n"+
    "LOGFILE="+logfile+"\n\n"+
    "echo \"============================\" > $LOGFILE\n"+
    "echo \"$(date)\" >> $LOGFILE\n"+
    "echo \"============================\" >> $LOGFILE\n"+
    "echo \"Startup from user '$(whoami)'\" >> $LOGFILE\n"+
    "echo \"\" >> $LOGFILE\n"+
    "source " + ROS_INSTALL_DIR + "/setup.bash &>> $LOGFILE\n"+
    "source " + LOCAL_BASH_FILE + " &>> $LOGFILE\n")
    if len(str(CMAKE_PREFIX_PATH)) != 0:
        format_str +='export CMAKE_PREFIX_PATH=' + str(CMAKE_PREFIX_PATH) + '\n'
    if len(str(ROS_HOSTNAME)) != 0:
        format_str +='export ROS_HOSTNAME=' + str(ROS_HOSTNAME) + '\n'
    if len(str(ROS_MASTER_URI)) != 0:
        format_str +='export ROS_MASTER_URI=' + str(ROS_MASTER_URI) + '\n'
    if len(str(GAZEBO_MODEL_PATH)) != 0:
        format_str +='export GAZEBO_MODEL_PATH=' + str(GAZEBO_MODEL_PATH) + '\n'
    if len(str(ADVENTURE_SIMULATION)) != 0:
        format_str +='export ADVENTURE_SIMULATION=' + str(ADVENTURE_SIMULATION) + '\n'
    return format_str

def gen_launcher(bash_name, launcher_name, icon_name, command):
    file_path = LAUNCHER_DIR + bash_name
    format_str = gen_bash_header()
    format_str += "\n" + command + " &>> $LOGFILE\n\nsleep 0.2"
    write_file_safely(file_path, format_str)
    add_shortcut(launcher_name, ROOT_DIR + '/contrib/icons/' + icon_name, file_path)

def setup_user_permissions():
    result = exec_command("groups " + USERNAME, True)
    if (result[0] == 0) and "dialout" not in result[1]:
        print hdr("Your user (")+bld(hdr(USERNAME))+hdr(") should "+
                  "be in a ")+err("'dialout'")+hdr(" group to be able "+
                  "to communicate with some sensor types.\n"+
                  "Do you wish to be added? (Requires superuser privileges)") 
        if (query("y/n?")):
            print wht("Adding user " + USERNAME + " to 'dialout'...")
            exec_command("sudo adduser " + USERNAME + " dialout")
        else:
            print wht("Skipping...")

def setup_dev_permissions():
    file_path = "/etc/udev/rules.d/85-inputdevice.rules"
    format_str = "SUBSYSTEM==\"input\", MODE=\"666\""
    write_file_safely_root(file_path, format_str)

def install_project_deps():
    print wht("Installing project dependencies:")
    cmd_ = "sudo apt-get install -y"
    for dep in DEPS:
        cmd_ += " " + dep
    exec_command(cmd_)

# This will generate scripts that will be launched on system startup
def create_startup_scripts():
    print wht("Creating system starup scripts requires root permissions. "+
              "Do you wish to continue?")
    if (not query("y/n?")):
        return
    user_launcher = ("#!/bin/bash\n"+
    "echo \"$(sudo -u "+USERNAME+" "+HOME_DIR+"/.user_startup.sh)\"\n")
    root_launcher = ("#!/bin/bash\n"+
    "echo \"$(sudo -u root "+HOME_DIR+"/.root_startup.sh)\"\n")
    write_file_safely_root("/etc/init.d/user_startup_launcher.sh", user_launcher)
    write_file_safely_root("/etc/init.d/root_startup_launcher.sh", root_launcher)

    result = exec_command("sudo update-rc.d user_startup_launcher.sh defaults")
    if (result[0] != 0): exit(1)
    result = exec_command("sudo update-rc.d root_startup_launcher.sh defaults")
    if (result[0] != 0): exit(1)
    
    user_format_str = gen_bash_header(HOME_DIR+"/.user_startup.log")
    user_format_str+= ("\nfor DRIVE_USB_FILE in " + " ".join(DEVS_TO_WAIT)+"; do\n"+
    "    echo \"Waiting until $DRIVE_USB_FILE appears in the system...\" >> $LOGFILE\n"+
    "    while [ ! -e $DRIVE_USB_FILE ]\n"+
    "    do\n"+
    "        sleep 0.2\n"+
    "    done\n"+
    "    echo \"...Found\" >> $LOGFILE\n"+
    "done\n"+
    "echo \"\" >> $LOGFILE\n"+
    "echo \"== Starting up the driver ==\" >> $LOGFILE\n"+
    "echo \"$(date)\" >> $LOGFILE\n"+
    "echo \"============================\" >> $LOGFILE\n"+
    "echo \"\" >> $LOGFILE\n"+
    "echo \"$(roslaunch adventure_bringup adventure.launch &>> $LOGFILE )\"\n")
    write_file_safely(HOME_DIR+"/.user_startup.sh", user_format_str)

    root_format_str = gen_bash_header(HOME_DIR+"/.root_startup.log")
    root_format_str+= ("\n\nLC_ALL=C\n"+
    "nmcli con up id '" + WIFI_NAME + "'\n"+
    "while [ \"$(nmcli -t -f WIFI,STATE nm)\" = 'enabled:disconnected' ]\n"+
    "do\n"+
    "    nmcli con up id '" + WIFI_NAME + "'\n"+
    "    sleep 5\n"+
    "done\n"
    "echo \"WiFi configuration finished...\" >> $LOGFILE\n")
    write_file_safely(HOME_DIR+"/.root_startup.sh", root_format_str)


# Handle command line args
parser = argparse.ArgumentParser(description='Deploy script for Adventure project.')
parser.add_argument('-c', dest='only_clear', action='store_const', const=True, default=False,
                    help='only clear up autogenerated scripts/config entries and exit')
parser.add_argument('-i', dest='only_info', action='store_const', const=True, default=False,
                    help='only print some useful system info and exit')
parser.add_argument('--deps', dest='install_deps', action='store_const', const=True, default=False,
                    help='install deps and exit')
parser.add_argument('--startup', dest='init_startup', action='store_const', const=True, default=False,
                    help='initialize startup scripts')
parser.add_argument('--perm', dest='setup_permissions', action='store_const', const=True, default=False,
                    help='This will change /dev/input permissions so that it would be possible to access it as non-root.'+
                    'Requres sudo. Will need to restart the system.')
args = parser.parse_args()
used_only_cli = False
if (args.only_clear):
    used_only_cli = True
    cleanup()

if (args.only_info):
    used_only_cli = True
    print_info()
 
if (args.install_deps):
    used_only_cli = True
    install_project_deps()

if (args.init_startup):
    used_only_cli = True
    create_startup_scripts()

if (args.setup_permissions):
    used_only_cli = True
    setup_dev_permissions()

if (used_only_cli): exit(0)

# Print out useful system information
print_info()

# Add myself to dialout and do other useful system stuff
setup_user_permissions()

# Install required packages
'''
install_project_deps()
'''
# Initialize catkin workspace
init_workspace() 

# Configure ~/.bashrc for ROS
bashrc = bashrc + ("source " + LOCAL_BASH_FILE + GENERATOR_MARKER + '\n')
bashrc = bashrc + ("source " + ROS_INSTALL_DIR + "/setup.bash" + GENERATOR_MARKER + '\n')
bashrc = bashrc + ("export PATH=" + LAUNCHER_DIR + ":$PATH" + GENERATOR_MARKER + '\n')

print wht("")

# Generate launchers
ensure_dir(LAUNCHER_DIR)

# gen_launcher('bashscriptname', 'launchername', 'iconname.png', 'roslaunch <package> <launchfile>.launch')
gen_launcher('adventure-rebuild',          'adventureRebuild',         'rosRebuild.png',   'cd ' + ROOT_DIR + '\n\n'\
                                                                                           'catkin_make\n\n'\
                                                                                           'source ' + LOCAL_BASH_FILE + '\n'\
                                                                                           'echo "Press any key to continue..."\nread')

gen_launcher('adventure-rebuild-eclipse',  'adventureRebuild4Eclipse', 'rosRebuild4Eclipse.png', 'cd ' + ROOT_DIR + '\n'\
                                                                                           'catkin_make --force-cmake -G"Eclipse CDT4 - Unix Makefiles" -DCMAKE_BUILD_TYPE=Debug'\
                                                                                           ' -DCMAKE_ECLIPSE_MAKE_ARGUMENTS=-j8\n'\
                                                                                           'source ' + LOCAL_BASH_FILE + '\n'\
                                                                                           'echo "Press any key to continue..."\nread')

gen_launcher('adventure-simulator',       'adventureSimulationEnv',    'rosSimulator.png',  'roslaunch adventure_gazebo adventure_world.launch')
gen_launcher('adventure-core-4-real',     'adventureCore4Real',        'rosRun4Real.png',   'roslaunch adventure_examples core.launch')

