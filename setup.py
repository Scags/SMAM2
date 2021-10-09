import setuptools

with open("README.md", "r", encoding="utf-8") as f:
	long_description = f.read()

setuptools.setup(
	name="SourceMod-Addon-Manager",
	version="1.0.0.1",
	author="Scag",
	author_email="johnmascagni@gmail.com",
	description="Automatic installer for SourceMod plugins and extensions",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/Scags/SMAM2",
	project_urls={
		"Bug Tracker": "https://github.com/Scags/SMAM2/issues",
	},
	entry_points={
		'console_scripts': [
			'smam = smam.smam:main'
		]
	},
	classifiers=[
		"Programming Language :: Python :: 3",
		"Operating System :: OS Independent",
	],
	package_dir={"": "src"},
	packages=setuptools.find_packages(where="src"),
	python_requires=">=3.6",
)
