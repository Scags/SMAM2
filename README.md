# SourceMod Addon Manager 2 (SMAM2) #

SMAM2 is a package manager built specifically for SourceMod.

This was heavily inspired by [Phil25's SMAM](https://github.com/Phil25/SMAM). I thought the idea was great so I went ahead and rewrote it, improving on a few features and giving it some new features entirely.

There is currently not yet a "database" of plugins/extensions. For now, every addon is listed in the GitHub repo in a .json file. If you want to add your project/plugin/extension, just file a pull request.

### [Features](https://github.com/Scags/SMAM2#features-1)
### [Installation](https://github.com/Scags/SMAM2#installation-1)
### [Commands](https://github.com/Scags/SMAM2#commands-1)
### [Adding an Addon](https://github.com/Scags/SMAM2#adding-an-addon-1)
### [TODO](https://github.com/Scags/SMAM2#todo-1)

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

Each server's installation data is set up in the user's home data directory, `~/.local/share/smam/` for Unix and `C:\Users\<you>\AppData\Local\smam\` for Windows.

When installing an addon, the default behavior is pulling from the latest database file in the repo (addons.json). If you want to override this and use your own addons database. Open up the config directory and open `config.json` (which will only exist after running SMAM for the first time) and set "local" to true:
```json
{
    "local": false,
    "file_exclusions": [
        "*/.*",
        "*.md"
    ]
}
```
You can also change which files are ignored during installation with "file_exclusions". Default is hidden and Markdown files.

After doing so, SMAM will pull from a/the addons.json in the config directory. If this file does not exist upon running any SMAM command that requires the addons database, it will simply download the latest addons.json, write it to your config directory, and proceed to use that file until you run `smam update`.

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

Update the local addon database (only required if you've edited to config to use a local addon file)
```
[scag@localhost ~]$ smam update -h
usage: smam [-h]

Update addons.json to the latest version. Only useful if config key "local" is set to True

optional arguments:
  -h, --help  show this help message and exit
```

# Adding an Addon

Created a plugin? Add it! I encourage everyone to add their projects to this repo.

You can create subkeys for "linux", "windows", or "darwin" at any position in the config to differentiate between OSes. SMAM can figure it out for you. All entries are optional except for `url`.

Addon configuration is as follows:

- `author`
  - You!
- `description`
  - Description of your plugin/extension.
- `version`
  - Version of your addon.
- `url`
  - URL of the addon.
  - This can either be a string or a dict of prepended paths to prepend to the installation files. See `pathprepend`.
- `zipped`
  - If the URL leads to a file that is not a zipped folder or tarball, set to "false".
  - Already true by default.
- `exclude`
  - If necessary, add files/folders to ignore during installation.
  - Hidden and Markdown files are ignored globally.
- `required`
  - If your plugin requires a plugin or extension, you can add its name in an array/list.
  - The name is the same as the root addon node.
- `optional`
  - If your plugin has optional dependencies, you can list them in an array/list.
- `pathprepend`
  - Sometimes SMAM can't figure out where a files are supposed to go.
  - For example: if the URL points to a .smx, prepending "plugins/" to the file path would allow SMAM to follow addons/sourcemod/plugins and extract the plugin correctly.

<details><summary>Example addons:</summary>

```json
  "left4downtown":
	{
		"author": "Downtown1, ProdigySim",
		"description": "unlock maximum players slots ( up to 18*) in Left 4 Dead 1/2, also provide some new developer functionality",
		"version": "0.5.4.2",
		"zipped": false,
		"url":
		{
			"extensions/":
			{
				"linux": "https://forums.alliedmods.net/attachment.php?attachmentid=70562&d=1280077009",
				"darwin": "https://forums.alliedmods.net/attachment.php?attachmentid=70562&d=1280077009",
				"windows": "https://forums.alliedmods.net/attachment.php?attachmentid=70561&d=1280076998"
			},
			"scripting/include/": "https://forums.alliedmods.net/attachment.php?attachmentid=70564&d=1280077035",
			"gamedata/": "https://forums.alliedmods.net/attachment.php?attachmentid=70604&d=1280127112"
		}
	},
  "socket":
	{
		"author": "sfPlayer, JoinedSenses",
		"description": "provides networking functionality for SourceMod scripts",
		"version": "0.2",
		"zipped": false,
		"pathprepend": "extensions/",
		"url":
		{
			"windows": "https://github.com/JoinedSenses/sm-ext-socket/releases/download/v0.2/socket.ext.dll",
			"linux": "https://github.com/JoinedSenses/sm-ext-socket/releases/download/v0.2/socket.ext.so",
			"darwin": "https://github.com/JoinedSenses/sm-ext-socket/releases/download/v0.2/socket.ext.so"
		}
	},
  "vsh2":
	{
		"author": "Nergal",
		"description": "VSH2 is a rewrite of the original VSH, meant to combine the best of VSH and FF2.",
		"version": "2.12.0",
		"url": "https://github.com/VSH2-Devs/Vs-Saxton-Hale-2/archive/refs/heads/develop.zip",
		"exclude":
		[
			"*saxtonhale.smx",
			"*freak_fortress_2.smx"
		],
		"required":
		[
			"tf2items"
		]
	},
```
</details>

# TODO

- Allow complete server deletion.
- Improve argparse's command structure

~~Allow local addon database configurations~~ Implemented in V1.1
