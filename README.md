# SourceMod Addon Manager 2 (SMAM2) #

SMAM2 is a package manager built specifically for SourceMod.

This was heavily inspired by [Phil25's SMAM](https://github.com/Phil25/SMAM). I thought the idea was great so I went ahead and rewrote it, improving on a few features and giving it some new features entirely.

There is currently not yet a "database" of plugins/extensions. For now, every addon is listed in the GitHub repo in a .json file. If you want to add your project/plugin/extension, just file a pull request.

# Features #

## Multiple Server Management ##

SMAM2 can support managing multiple servers. This is useful for scalable server hosts with multiple servers on a single machine. Addons can be installed to each server all at once, or servers can be explicitly selected for individual installations.

<details>
<summary><b>Example:</b></summary>

```sh
[scag@localhost ~]$ smam add /home/tf2/tf -ntf2
Successfully created server 1 (tf2) with path "/home/tf2/tf".

[scag@localhost ~]$ smam add /home/csgo/csgo
Successfully created server 2 () with path "/home/csgo/csgo".

[scag@localhost ~]$ smam add /home/l4d/l4d2 -nl4d
Successfully created server 2 (l4d) with path "/home/l4d/l4d2".
```
```sh
[scag@localhost ~]$ smam install sourcemod1-11 metamod1-12
Successfully installed addon sourcemod1-11 to server 1 (tf2).
Successfully installed addon sourcemod1-11 to server 2 ().
Successfully installed addon sourcemod1-11 to server 3 (l4d).

Successfully installed addon metamod1-12 to server 1 (tf2).
Successfully installed addon metamod1-12 to server 2 ().
Successfully installed addon metamod1-12 to server 3 (l4d).

[scag@localhost ~]$ smam install tf2items -stf2
Successfully installed addon tf2items to server 1 (tf2).

[scag@localhost ~]$ smam install steamworks -s2,3
Successfully installed addon steamworks to server 2 ().
Successfully installed addon steamworks to server 3 (l4d).

[scag@localhost ~]$ smam install dhooks -s1-2
Successfully installed addon dhooks to server 1 (tf2).
Successfully installed addon dhooks to server 2 ().

[scag@localhost ~]$ smam remove steamworks -sl4d
Successfully removed addon steamworks from server 3 (l4d).
```
</details>

## Scaled Server Deployment ##

SMAM2 can install several addons at once, *including* SourceMod and MetaMod. With a little elbow grease, you can create a script to automatically create and deploy a server with its own specified plugins.

Plugins also can have registered dependencies. VSH2 requires TF2Items, so it is automatically added to the installation queue.

`pluginlist.txt`
```
metamod1-12
sourcemod1-11
vsh2
```

`install.sh`
```sh
./build.sh
smam add /home/tf2hale/tf2hale/tf -n tf2hale
smam install -F pluginlist.txt
```

## Configuration ##

Setting up addons in the main database is easily configurable. Each subkey in the .json file can differentiate between Windows, Linux, and Mac (Darwin) configurations.

Config can exclude files, prepend to file paths to configure installation directories, and include required and optionally required dependencies.

Each server installation data is set up in the user's home data directory, `~/.local/share/smam/` for Unix and `C:\Users\<you>\AppData\Local\smam\` for Windows.

# Installation #

SMAM2 is OS independent and uses `pip` to install.

SMAM2 also requires the `appdirs` package i.e. `pip3 install appdirs`.

## Windows ##

After running steamcmd to install server files...

```sh
C:\Users\johnm> git clone https://github.com/Scags/SMAM2.git
C:\Users\johnm> cd SMAM2
C:\Users\johnm\SMAM2> pip install . # OR you can execute 'py setup.py install'
C:\Users\johnm\SMAM2> smam add C:\path\to\game\dir -n my_server_name	# This is the game directory that holds the 'addons' folder (e.g. tf/csgo/l4d2/css)
```

You're done. You should be able to setup and configure your server(s) from here on.

## Unix ##

After running steamcmd to install server files...

```sh
[scag@localhost ~]$ git clone https://github.com/Scags/SMAM2.git
[scag@localhost ~]$ cd SMAM2
```

You have 2 options from here.

If you run a single server or you have a single user running multiple servers, you would use:
```sh
[scag@localhost ~/SMAM2]$ pip3 install .
```
You may also need to add the local bin dir to PATH. This installs SMAM so that you won't need to escalate to manage a server, but if you are running servers under different users, SMAM will be confused if you try to run it under a different user than the one you installed with.

Otherwise, if you are running multiple servers on the same machine under different users, you may want to install to the /usr/bin directory as `sudo`. This would mean using:
```sh
[scag@localhost ~/SMAM2]$ sudo python3 setup.py install
```

From then on, you would have to run `smam` as root, but you would be able to harness SMAM's ability configure multiple servers at once.

# Commands #

Adding a server:
```
[scag@localhost ~]$ smam add -h
usage: smam add [-h] [-n NAME]

add a server to SMAM

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  name of the server being added

[scag@localhost ~]$ smam add path/to/serverdir
```

Dropping a server:

This does not remove any files
```
[scag@localhost ~]$ smam drop -h
usage: smam drop [-h]

drop server(s) from SMAM

optional arguments:
  -h, --help  show this help message and exit

[scag@localhost ~]$ smam drop 1
[scag@localhost ~]$ smam drop tf2hale
[scag@localhost ~]$ smam drop all
```

Installing an addon:
```
[scag@localhost ~]$ smam install -h
usage: smam [-h] [-s SERVERS] [-n] [-u] [-f] [-o] [-F FILE]

install a plugin/extension

optional arguments:
  -h, --help            show this help message and exit
  -s SERVERS, --servers SERVERS
                        server(s) to install to
  -n, --noconfig        ignore config files from installation
  -u, --upgrade         update addon to the latest version
  -f, --force           force installation regardless of preexisting files
  -o, --optional        install addon's optional packages
  -F FILE, --file FILE  read addons from a file

[scag@localhost ~]$ smam install tf2items
[scag@localhost ~]$ smam install -s 1 steamworks
[scag@localhost ~]$ smam install vsh2 -o
[scag@localhost ~]$ smam install sourcemod1-11 -nf -s 1-4
[scag@localhost ~]$ smam install -Fmyplugins.txt -s1,4
```

Removing an addon:
```
[scag@localhost ~]$ smam remove -h
usage: smam [-h] [-s SERVERS] [-k]

remove a plugin/extension

optional arguments:
  -h, --help            show this help message and exit
  -s SERVERS, --servers SERVERS
                        server(s) to remove from
  -k, --keep            do not remove addon files

[scag@localhost ~]$ smam remove left4downtown -k
[scag@localhost ~]$ smam remove steamtools steamworks
[scag@localhost ~]$ smam remove all 
```

List servers and their addons:
```
[scag@localhost ~]$ smam list -h
usage: smam [-h] [-a]

list server(s) and their addons

optional arguments:
  -h, --help  show this help message and exit
  -a, --all   list content paths

[scag@localhost ~]$ smam list -a
```

Search for an addon:
```
[scag@localhost ~]$ smam search -h
usage: smam [-h]

search for an addon

optional arguments:
  -h, --help  show this help message and exit

[scag@localhost ~]$ smam search tf2
[scag@localhost ~]$ smam search sourcemod
```

List info for an addon:
```
[scag@localhost ~]$ smam info -h
usage: smam [-h]

list information for an addon

optional arguments:
  -h, --help  show this help message and exit

[scag@localhost ~]$ smam info tf2items
```

# TODO

- Allow complete server deletion.
- Allow local addon database configurations
- Improve argparse's command structure
