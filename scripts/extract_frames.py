#!/usr/bin/env python3
"""
Extract only the frames that are applicable to the specified resource/version.
"""

__author__ = "Skatje Myers"
__license__ = "CC-BY-SA-4.0"

import argparse
import os
from lxml import etree as ET
from pathlib import Path


def main(args):
	for file in Path(args.input).rglob("*.xml"):
		tree = ET.parse(str(file))
		root = tree.getroot()
		for pred in root:
			for roleset in pred:
				usage_tags = roleset.find('usagenotes').findall('usage')
				should_include = None
				for usage in usage_tags:
					if usage.attrib['resource'].lower() == args.resource.lower() and usage.attrib['version'].lower() == args.version.lower():
						if usage.attrib['inuse'] == '+':
							should_include = True
						else:
							should_include = False
						break
				assert should_include != None, 'Roleset is missing a usage tag for this resource/version! Please file an issue on GitHub.'
				if not should_include:
					pred.remove(roleset)
			if len(list(pred.iter('roleset'))) == 0:
				root.remove(pred)
		if len(list(root.iter('roleset'))) == 0:
			if Path(args.input) == Path(args.output):
				# if input/output dirs are the same, make sure to delete any files that don't contain relevant rolesets
				os.remove(Path(args.output, file.name))
		else:
			tree.write(str(Path(args.output, file.name)), xml_declaration=True, encoding='utf-8', standalone=False)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--input", action="store", dest="input", help='Input frame directory', required=True)
	parser.add_argument("-o", "--output", action="store", dest="output", help='Output frame directory', required=True)
	parser.add_argument("-r", "--resource", action="store", dest="resource", required=True)
	parser.add_argument("-v", "--version", action="store", dest="version", required=True)

	args = parser.parse_args()
	if Path(args.input) == Path(args.output):
		response = input('Input and output directories are the same -- Overwrite frames? Y/n')
		if response not in ['Y', 'y']:
			print('Cancelled extraction.')
			exit()
	if args.resource.lower() == 'propbank':
		if args.version.lower() not in ['2.1.5', '3.1', '3.4', 'flickr 1.0']:
			print('Unknown "version" value for ' + args.resource + ': ' + args.version)
			exit()
	elif args.resource.lower() == 'amr':
		if args.version.lower() not in ['spatial 1.0', 'thyme 1.0']:
			print('Unknown "version" value for ' + args.resource + ': ' + args.version)
			exit()
	else:
		print('Invalid resource specified. Should be "AMR" or "PropBank", but was given ' + args.resource + '.')
		exit()
	Path(args.output).mkdir(exist_ok=True)
	main(args)
