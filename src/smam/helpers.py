import requests
import io
#import tqdm
#import sys
import zipfile
import tarfile
import fnmatch
import platform

# From https://stackoverflow.com/a/287944

EXCLUSIONS = [
	"*/.*",  # Hidden files/folders
	"*.md",  # Markdown, README files
]


class colors(object):
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

# From https://gist.github.com/amjith/673824


def convert(inp: str) -> list:
	if not inp:  # Empty string must return an empty list
		return []

	pages = []
	comma_separated = []
	# Split the input string based on comma delimitation
	comma_separated = inp.split(",")
	for item in comma_separated:
		if "-" in item:
			a = item.split("-")
			pages.extend(range(int(a[0]), int(a[1])+1))
		else:
			pages.append(int(item))
	return pages


def get_zip(url: str) -> zipfile.ZipFile:
	r = requests.get(url, stream=True)
	# t = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1024,
	#              total=int(r.headers["Content-Length"]), file=sys.stdout)
	# b = bytes()
	ctype = r.headers["Content-Type"]
	# for chunk in r.iter_content(chunk_size=1024):
	# b += chunk
	# t.update(len(chunk))

	if ctype == "application/zip":
		return zipfile.ZipFile(io.BytesIO(r.content))
	return tarfile.open(fileobj=io.BytesIO(r.raw.read()))


def zip2dict(zipf) -> dict:
	if isinstance(zipf, zipfile.ZipFile):
		return {f: zipf.read(f) for f in zipf.namelist()}

	return {
		member.name + ("/" if member.isdir() else ""):
		zipf.extractfile(member).read() if member.isreg() or member.islnk() or member.issym() else b"" for member in zipf.getmembers()
	}


def discern_folder(folder: str, currpath: str, filedict: dict, paths: list, prepend: str) -> None:
	for key, f in list(filedict.items()):
		fullpath = prepend + key
		s = fullpath.split("/")
		try:
			idx = s.index(folder)
			zippath = currpath + "/".join(s[idx:])
			paths.append((zippath, f))
			del filedict[key]
		except:
			pass


def discern_writepaths(path: str, filedict: dict, prepend: str) -> list:
	# Attempt to intelligently find the proper installation directory
	paths = []
	cpy = filedict.copy()

	discern_folder("cfg", path + "/", cpy, paths, prepend)

	# Find the addons folder, if it exists
	if len(cpy):
		discern_folder("addons", path + "/", cpy, paths, prepend)

	# No addons folder, most likely this is within sourcemod then, right?
	if len(cpy):
		discern_folder("sourcemod", path + "/addons/", cpy, paths, prepend)

	# Metamod?
	if len(cpy):
		discern_folder("metamod", path + "/addons/", cpy, paths, prepend)

	# Every sourcemod folder :S
	if len(cpy):
		for s in ["bin", "configs", "data", "extensions", "gamedata", "plugins", "scripting", "translations"]:
			discern_folder(s, path + "/addons/sourcemod/", cpy, paths, prepend)

	# Chaos
	pathfails = 0
	for file in cpy.keys():
		if file != "":
			pathfails += 1
			print(f"{colors.WARNING}Failed to discern path for file \"{file}\"{colors.ENDC}")

	return paths, pathfails


def exclude(filedict: dict, exclude: list, exclusions: list) -> None:
	for path in list(filedict.keys()):
		for ex in exclusions:
			if fnmatch.fnmatch(path, ex):
				del filedict[path]
				continue

		for ex in exclude:
			if fnmatch.fnmatch(path, ex):
				del filedict[path]


def get_files(url: str) -> dict:
	if isinstance(url, dict):
		urlnode = osnode(url)
		d = {}
		for prepend, newurl in urlnode.items():
			newurl = osnode(newurl)
			if isinstance(newurl, list):
				for newnewurl in newurl:
					r = requests.get(newnewurl, stream=True)
					disp = r.headers["Content-Disposition"]
					filename = disp[len("attachment; filename="):].strip("\"")
					d[prepend + filename] = r.content
				continue

			r = requests.get(newurl, stream=True)
			disp = r.headers["Content-Disposition"]
			filename = disp[len("attachment; filename="):].strip("\"")
			d[prepend + filename] = r.content
		return d
	else:
		r = requests.get(url, stream=True)
		disp = r.headers["Content-Disposition"]
		filename = disp[len("attachment; filename="):].strip("\"")
		return {filename: r.content}


def osnode(d: dict):
	if not isinstance(d, dict):
		return d
	return d.get(platform.system().lower(), None) or d


def collect(addon, exclusions: list) -> dict:
	if addon.zipped:
		z = get_zip(addon.url)
		filedict = zip2dict(z)
		exclude(filedict, addon.exclude, exclusions)
	else:
		filedict = get_files(addon.url)
	return filedict


def addpackages(addon, requiredlist: list, installs: list, addons) -> None:
	if not isinstance(requiredlist, list):
		requiredlist = [requiredlist]

	for required in requiredlist:
		if required not in [a.name for a in installs]:
			print(f"\"{addon.name}\" requires addon \"{required}\". Adding to queue.")
			installs.append(addons[required])
