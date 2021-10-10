import argparse
import os
import appdirs
import sys
import json
import requests

import smam.helpers as helpers


class Server(object):
	def __init__(self, **kwargs):
		self.path = kwargs["path"]
		self.index = kwargs.get("index", 0)
		self.addons = kwargs.get("addons", {})
		self._name = kwargs.get("name", None)

	@staticmethod
	def fromconf(index, node):
		return Server(index=index, name=node["name"], path=node["path"], addons=node["addons"])

	def owns(self, addon):
		return addon in self.addons

	@property
	def name(self):
		return self._name or ""

	def remove_addon(self, addonstr):
		# Folders go last
		removefiles = self.addons[addonstr]["content"]
		removefolders = []
		for u in range(len(removefiles)-1, -1, -1):
			if removefiles[u][-1] == "/":
				removefolders.append(removefiles.pop(u))

		removefolders.sort(key=lambda x: len(x), reverse=True)
		removables = removefiles + removefolders
		for path in removables:
			if not os.path.exists(path):
				print(
					f"{helpers.colors.WARNING}Addon \"{addonstr}\" {'file' if path[-1] != '' else 'folder'} \"{path}\" does not exist in server #{self.index} ({self.name}). Skipping...{helpers.colors.ENDC}")
			else:
				if os.path.isdir(path):
					if len(os.listdir(path)) == 0 and not path.endswith("addons/"):
						os.rmdir(path)
					else:
						print(
							f"{helpers.colors.WARNING}Addon \"{addonstr}\" folder \"{path}\" from server #{self.index} ({self.name}) is not empty. Skipping...{helpers.colors.ENDC}")
						continue
				else:
					os.remove(path)
				print(
					f"{helpers.colors.OKCYAN}Removing addon \"{addonstr}\" {'file' if path[-1] != '' else 'folder'} \"{path}\" from server #{self.index} ({self.name}).{helpers.colors.ENDC}")


class Addon(object):
	def __init__(self, name, node):
		self.name = name
		self.url = helpers.osnode(node["url"])

		self.author = node.get("author", "")
		self.version = helpers.osnode(node.get("version", ""))
		self.description = node.get("description", "")
		self.zipped = node.get("zipped", True)
		self.pathprepend = node.get("pathprepend", "")
		self.exclude = helpers.osnode(node.get("exclude", []))
		self.required = helpers.osnode(node.get("required", []))
		self.optional = helpers.osnode(node.get("optional", []))


class SMAM(object):
	def __init__(self):
		p = argparse.ArgumentParser(
			prog="smam", description="SourceMod Addon Manager")
		p.add_argument("command", help="command to execute")

		# Multilevel commands are weird
		args = p.parse_args(sys.argv[1:2])
		if not hasattr(self, args.command):
			print("Unrecognized command")
			p.print_help()
			return

		getattr(self, args.command)()

	def _servers(self):
		os.makedirs(appdirs.user_data_dir("smam"), exist_ok=True)

		if not os.path.exists(os.path.join(appdirs.user_data_dir("smam"), "servers.json")):
			servers = open(os.path.join(
				appdirs.user_data_dir("smam"), "servers.json"), "w")
			servers.write("{}")
			servers.close()

		servers = open(os.path.join(
			appdirs.user_data_dir("smam"), "servers.json"), "r")

		serverdict = json.load(servers)
		servers.close()
		return [Server.fromconf(int(k), v) for k, v in serverdict.items()]

	def _addons(self):
		content = requests.get("https://brewcrew.tf/smam/addons.json").content
		if content is None:
			print(f"{helpers.colors.FAIL}Failed to download addon information.{helpers.colors.ENDC}")
			exit(1)

		j = json.loads(content)
		return {name: Addon(name, node) for name, node in j.items()}

	def _write_serverinfo(self, serverlist):
		j = {}
		for server in serverlist:
			j[str(server.index)] = {
				"name": server.name,
				"path": server.path,
				"addons": server.addons
			}

		with open(os.path.join(appdirs.user_data_dir("smam"), "servers.json"), "w") as f:
			json.dump(j, f, indent=4)

	def install(self):
		p = argparse.ArgumentParser(description="install a plugin/extension")
		p.add_argument("-s", "--servers", help="server(s) to install to",
		               type=str, dest="servers")
		p.add_argument("-n", "--noconfig", help="ignore config files from installation",
		               action="store_true", dest="noconfig")
		p.add_argument("-u", "--upgrade", help="update addon to the latest version",
		               action="store_true", dest="upgrade")
		p.add_argument("-f", "--force", help="force installation regardless of preexisting files",
		               action="store_true", dest="force")
		p.add_argument("-o", "--optional", help="install addon's optional packages",
		               action="store_true", dest="optional")
		p.add_argument("-F", "--file", help="read addons from a file",
		               type=argparse.FileType('r'), dest="file")
		args, candidates = p.parse_known_args(sys.argv[2:])

		servers = self._servers()
		if not len(servers):
			print(
				f"{helpers.colors.WARNING}No known servers exist. Add them with \"smam add [path/to/gamedir]\".{helpers.colors.ENDC}")
			return

		isbyname = False
		if getattr(args, "servers", False):
			# If picking servers by name
			for char in args.servers:
				if char not in "1234567890-,":
					isbyname = True
					break
			if not isbyname:
				indices = helpers.convert(args.servers)
				serverinstalls = [s for s in servers if s.index in indices]
			else:
				names = p.servers.split(",")
				serverinstalls = [s for s in servers if s.name in names]
		else:
			# If they didn't pass an explicit server, install to all of them
			serverinstalls = servers

		addons = self._addons()

		if args.file is not None:
			candidates.extend(args.file.read().split("\n"))

		# ._.
		for s in candidates:
			if not len(s):
				continue

			if s not in addons.keys():
				print(
					f"{helpers.colors.WARNING}Installation candidate {s} does not exist and will be skipped.{helpers.colors.ENDC}")
			elif addons[s].url is None:
				print(
					f"{helpers.colors.WARNING}Installation candidate {s} is not supported for this OS and will be skipped.{helpers.colors.ENDC}")

		installs = [addon for key, addon in addons.items() if key in candidates]

		if not len(installs):
			print(f"{helpers.colors.FAIL}Failed to satisfy any installation candidate.{helpers.colors.ENDC}")
			return

		# Requirements handling
		i = 0
		while i < len(installs):
			helpers.addpackages(installs[i], installs[i].required, installs, addons)
			if args.optional:
				helpers.addpackages(installs[i], installs[i].optional, installs, addons)
			i += 1

		for addon in installs:
			print(f"Collecting {addon.name}")
			filedict = helpers.collect(addon)

			for i in range(len(serverinstalls)):
				if serverinstalls[i].owns(addon.name) and not (args.upgrade or args.force):
					print(
						f"{helpers.colors.WARNING}Server #{serverinstalls[i].index} ({serverinstalls[i].name}) already has addon {addon.name} installed. Skipping...{helpers.colors.ENDC}")
					continue

				writepaths, pathfails = helpers.discern_writepaths(
					serverinstalls[i].path, filedict, addon.pathprepend)
				# This server now owns this addon
				serverinstalls[i].addons[addon.name] = {
					"url": addon.url,
					"content": [p for p, _ in writepaths]
				}

				written = 0
				failures = 0
				for path, bts in writepaths:
					if args.noconfig and ("configs/" in path or "cfg/" in path):
						continue

					# Is a folder
					if path[-1] == "/":
						os.makedirs(path, exist_ok=True)
					else:
						if os.path.exists(path) and not (args.upgrade or args.force):
							print(
								f"{helpers.colors.WARNING}File \"{path}\" already exists in server #{serverinstalls[i].index} ({serverinstalls[i].name}). Skipping...{helpers.colors.ENDC}")
							failures += 1
						else:
							with open(path, "wb") as f:
								f.write(bts)
								print(
									f"{helpers.colors.OKCYAN}Extracting \"{path}\" to server #{serverinstalls[i].index} ({serverinstalls[i].name}).{helpers.colors.ENDC}")
								written += 1

				if written:
					print(
						f"{helpers.colors.OKCYAN}Successfully installed addon {addon.name} to server #{serverinstalls[i].index} ({serverinstalls[i].name}).{helpers.colors.ENDC}")
				if pathfails:
					s = "" if pathfails == 1 else "s"
					print(
						f"{helpers.colors.WARNING}Could not configure path{s} for {pathfails} archive file{s}/folder{s}. Most likely unnecessary and unneeded.{helpers.colors.ENDC}")
				if failures:
					print(
						f"{helpers.colors.WARNING}{failures} preexisting files failed to extract.\nTo override, use the \"force\" command (-f, --force).{helpers.colors.ENDC}")

		# Clean up this list so we can dump new addon data
		for i in range(len(serverinstalls)):
			for u in range(len(servers)):
				if serverinstalls[i].name == servers[u].name:
					servers[u] = serverinstalls[i]
					break

		self._write_serverinfo(servers)

	def remove(self):
		p = argparse.ArgumentParser(description="remove a plugin/extension")
		p.add_argument("-s", "--servers", help="server(s) to remove from",
		               type=str, dest="servers")
		p.add_argument("-k", "--keep", help="do not remove addon files",
		               action="store_true", dest="keep")
		args, removals = p.parse_known_args(sys.argv[2:])

		servers = self._servers()
		if not len(servers):
			print(
				f"{helpers.colors.WARNING}No known servers exist. Add them with \"smam add [path/to/gamedir]\".{helpers.colors.ENDC}")
			return

		isbyname = False
		if getattr(args, "servers", False):
			# If picking servers by name
			for char in args.servers:
				if char not in "1234567890-,":
					isbyname = True
					break
			if not isbyname:
				indices = helpers.convert(args.servers)
				serverinstalls = [s for s in servers if s.index in indices]
			else:
				names = p.servers.split(",")
				serverinstalls = [s for s in servers if s.name in names]
		else:
			# If they didn't pass an explicit server, remove from all of them
			serverinstalls = servers

		for addon in removals:
			removeall = addon == "all"
			for i in range(len(serverinstalls)):
				if not removeall and not serverinstalls[i].owns(addon):
					print(
						f"{helpers.colors.WARNING}Server #{serverinstalls[i].index} ({serverinstalls[i].name}) does not own addon {addon}. Skipping...{helpers.colors.ENDC}")
					continue

				if not getattr(args, "keep", False):
					if removeall:
						for key in serverinstalls[i].addons.keys():
							serverinstalls[i].remove_addon(key)
					else:
						serverinstalls[i].remove_addon(addon)

				if removeall:
					print(
						f"{helpers.colors.OKCYAN}Successfully removed all addons from server #{serverinstalls[i].index} ({serverinstalls[i].name}).{helpers.colors.ENDC}")
				else:
					print(
						f"{helpers.colors.OKCYAN}Successfully removed addon {addon} from server #{serverinstalls[i].index} ({serverinstalls[i].name}).{helpers.colors.ENDC}")

				if removeall:
					serverinstalls[i].addons = {}
				else:
					del serverinstalls[i].addons[addon]

		# Clean up this list so we can dump new addon data
		for i in range(len(serverinstalls)):
			for u in range(len(servers)):
				if serverinstalls[i].name == servers[u].name:
					servers[u] = serverinstalls[i]
					break

		self._write_serverinfo(servers)

	def info(self):
		p = argparse.ArgumentParser(description="list information for an addon")
		_, addon = p.parse_known_args(sys.argv[2:])

		if not len(addon):
			print(f"{helpers.colors.FAIL}Usage: \"smam list <addon>\".{helpers.colors.ENDC}")
			return

		addons = self._addons()
		if addon[0] not in addons:
			print(
				f"{helpers.colors.FAIL}Failed to locate addon \"{addon[0]}\". Try searching for it with \"smam search\".{helpers.colors.ENDC}")
			return

		addon = addons[addon[0]]

		print(f"{addon.name}:\n\tAuthor: {addon.author}\n\tDescription: {addon.description}\n\tVersion: {addon.version}\n\tURL: {addon.url}")

	def search(self):
		p = argparse.ArgumentParser(description="search for an addon")
		_, addon = p.parse_known_args(sys.argv[2:])

		addon = addon[0]

		addons = self._addons()
		addonstr = []

		if addon in addons:
			addonstr.append(
				f"{addon}{f': {addons[addon].description}' if addons[addon].description is not None else ''}")
			del addons[addon]

		for key, a in addons.items():
			if addon.lower() in key.lower():
				addonstr.append(
					f"{key}{f': {a.description}' if a.description is not None else ''}")

		for a in addonstr:
			print(a)

	def update(self):
		raise NotImplementedError("Command \"update\" is not implemented.")

	def list(self):
		p = argparse.ArgumentParser(description="list server(s) and their addons")
		p.add_argument("-a", "--all", help="list content paths",
		               action="store_true", dest="all")
		args, tolist = p.parse_known_args(sys.argv[2:])

		servers = self._servers()
		serverlist = []
		if not len(tolist):
			serverlist = servers
		else:
			for server in tolist:
				isbyname = False
				# If picking servers by name
				for char in server:
					if char not in "1234567890-,":
						isbyname = True
						break
				if not isbyname:
					indices = helpers.convert(server)
					extend = [s for s in servers if s.index in indices]
					if not len(extend):
						print(f"{helpers.colors.WARNING}Server{'s' if len(indices) != 1 else ''} #{indices} do{'es' if len(indices) == 1 else ''} not exist in server list.{helpers.colors.ENDC}")
						continue
					serverlist.extend(extend)
				else:
					if server == "all":
						serverlist = servers
						break
					if server not in [s.name for s in servers]:
						print(f"{helpers.colors.WARNING}Server \"{server}\" does not exist in server list.{helpers.colors.ENDC}")
					else:
						for s in servers:
							if s.name == server:
								serverlist.append(s)

		if not len(serverlist):
			print(f"{helpers.colors.FAIL}No servers found.{helpers.colors.ENDC}")
			return

		# Remove duplicates
		serverlist = list(set(serverlist))
		serverlist.sort(key=lambda x: x.index)

		for server in serverlist:
			output = f"Server #{server.index} ({server.name})\n    Path: {server.path}\n    Addons:\n"
			for name, contents in server.addons.items():
				output += f"        {name}\n"
				# Path printing
				if getattr(args, "all", False):
					for content in contents:
						output += f"-           {content}\n"

			print(output)

#		print(f"{helpers.colors.OKCYAN}Successfully listed server{'s' if len(serverlist) != 1 else ''} #{[s.index for s in serverlist]}.{helpers.colors.ENDC}")

	def add(self):
		p = argparse.ArgumentParser(description="add a server to SMAM")
		p.add_argument(
			"-n", "--name", help="name of the server being added", dest="name", type=str)
		args, path = p.parse_known_args(sys.argv[2:])

		# I am stupid
		prevcwd = os.getcwd()
		if len(path):
			os.chdir(path[0])
		cwd = os.getcwd()
		os.chdir(prevcwd)

		servers = self._servers()

		for s in servers:
			if cwd == s.path:
				print(f"{helpers.colors.FAIL}Path \"{cwd}\" already exists as server #{s.index} ({s.name}).{helpers.colors.ENDC}")
				return

		# Well this is kinda sucky
		# I wanted to make naming optional (so people can go 'smam add' and call it a day)
		# Insert indexing
		# The things I do for you people
		newserver = Server(name=getattr(args, "name", ""), path=cwd)
		servers.sort(key=lambda x: x.index)

		added = False
		for i, s in enumerate(servers):
			# Missing!
			if s.index != i+1:
				added = True
				newserver.index = i+1
				servers.insert(i, newserver)
				break

		if not added:
			newserver.index = len(servers)+1
			servers.append(newserver)

		os.makedirs(cwd + "/addons", exist_ok=True)
		self._write_serverinfo(servers)

		print(
			f"{helpers.colors.OKCYAN}Successfully created server #{newserver.index} ({newserver.name}) with path \"{newserver.path}\".{helpers.colors.ENDC}")

	def drop(self):
		p = argparse.ArgumentParser(description="drop server(s) from SMAM")
		args, todrop = p.parse_known_args(sys.argv[2:])

		servers = self._servers()
		droppedservers = []
		if not len(todrop):
			print(f"{helpers.colors.FAIL}Please specify which server(s) to drop.{helpers.colors.ENDC}")
			return

		for dropped in todrop:
			isbyname = False
			# If picking servers by name
			for char in dropped:
				if char not in "1234567890-,":
					isbyname = True
					break
			if not isbyname:
				indices = helpers.convert(dropped)
				extend = [s for s in servers if s.index in indices]
				if not len(extend):
					print(f"{helpers.colors.WARNING}Server{'s' if len(indices) != 1 else ''} #{indices} do{'es' if len(indices) == 1 else ''} not exist in server list.{helpers.colors.ENDC}")
					continue
				droppedservers.extend(extend)
			else:
				if dropped == "all":
					droppedservers = servers
					break
				if dropped not in [s.name for s in servers]:
					print(f"{helpers.colors.WARNING}Server \"{dropped}\" does not exist in server list.{helpers.colors.ENDC}")
				else:
					for s in servers:
						if s.name == dropped:
							droppedservers.append(s)

		droppedindices = set(dropped.index for dropped in droppedservers)
		servers = [s for s in servers if s not in droppedservers]

		self._write_serverinfo(servers)
		if len(droppedindices):
			print(
				f"{helpers.colors.OKCYAN}Successfully dropped server{'s' if len(droppedindices) != 1 else ''} #{[s for s in droppedindices]}.{helpers.colors.ENDC}")


def main():
	SMAM()
