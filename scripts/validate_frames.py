import argparse
import os
from pathlib import Path

import penman
from lxml import etree as ET
from penman import DecodeError


def validate(frame_file, log_file):
	parser = ET.XMLParser(dtd_validation=False, no_network=False) # TODO: Once DTD is ready, set validation=True
	if log_file:
		log_file = open(log_file, 'a')
	all_resource_versions = set()
	found_errors = False
	try:
		xml = ET.parse(str(frame_file), parser=parser)
	except ET.XMLSyntaxError as e:
		print('\033[91m' + frame_file.name)
		if log_file:
			log_file.write(frame_file.name + '\n')
			log_file.write('XML cannot be parsed' + '\n\n')
		else:
			print('XML cannot be parsed\033[0m')
		return
	frame_errors = list()

	for roleset in xml.findall('predicate/roleset'):
		# TODO: Check that we don't have duplicate <usage> tags
		usages = roleset.findall('usagenotes/usage')
		# TODO: verify that these all *have* resource/version attribs
		# TODO: Verify that <amr> "type" matches with one of the versions for that roleset
		# TODO: Verify that all numbered ARGs that show up in examples were defined in <roles>
		resources = [u.get('resource') + ' ' + u.get('version') for u in usages]
		for example in roleset.findall('example'):
			amr = example.find('amr')
			if amr is not None:
				# AMR should be parsable by penman library. TODO: Provide more info in the error text
				try:
					amr_graph = penman.decode(amr.text)
				except DecodeError as e:
					error_text = roleset.get('id') + ': Could not decode AMR example '
					if example.get('name'):
						error_text += '"' + example.get('name') + '" '
					error_text += '-- possibly malformed.'
					frame_errors.append(error_text)
			text = example.find('text')
			pb = example.find('propbank')
			if pb is not None:
				if text is None or not text.text:
					# If an example has <propbank>, it must have <text>
					error_text = roleset.get('id') + ': Example '
					if example.get('name'):
						error_text += '"' + example.get('name') + '" '
					error_text += ' is missing <text> tag.'
					frame_errors.append(error_text)
					tokenized_text = None
				else:
					tokenized_text = text.text.split(' ')
				rel = pb.find('rel')
				if rel is not None:
					# <rel> tags must have text contents
					rel_text = rel.text
					if not rel_text:
						error_text = roleset.get('id') + ': <rel> in example '
						if rel_text:
							error_text += '"' + rel_text + '" '
						error_text += ' is missing text contents.'
						frame_errors.append(error_text)
					# <rel> tags must have a relloc attribute
					relloc = rel.get('relloc')
					if not relloc:
						error_text = roleset.get('id') + ': <rel> '
						if rel_text:
							error_text += '"' + rel_text + '" '
						if example.get('name'):
							error_text += 'in example "' + example.get('name') + '" '
						error_text += ' is missing "relloc" attribute.'
						frame_errors.append(error_text)
					elif rel_text:
						# <rel> tags must have text that corresponds with the relloc indices of in the text.
						relloc = relloc.split(' ')
						if any(not index.isdigit() for index in relloc):
							error_text = roleset.get('id') + ': <rel> '
							if rel_text:
								error_text += '"' + rel_text + '" '
							if example.get('name'):
								error_text += 'in example "' + example.get('name') + '" '
							error_text += ' contains non-numeric indices.'
							frame_errors.append(error_text)
						elif tokenized_text:
							# <rel> text and tokens corresponding with relloc indices must match.
							try:
								rel_span_from_indices = ' '.join([tokenized_text[int(index)] for index in relloc])
							except:
								rel_span_from_indices = None
								error_text = roleset.get('id') + ': <rel> '
								if rel_text:
									error_text += '"' + rel_text + '" '
								if example.get('name'):
									error_text += 'in example "' + example.get('name') + '" '
								error_text += ' has relloc indices out of range for the example text.'
								frame_errors.append(error_text)
							if rel_span_from_indices and rel_span_from_indices != rel_text:
								error_text = roleset.get('id') + ': <rel> '
								if rel_text:
									error_text += '"' + rel_text + '" '
								if example.get('name'):
									error_text += 'in example "' + example.get('name') + '" '
								error_text += ' has text that doesn\'t correspond with the relloc indices: [' + rel_text + '] vs. [' + rel_span_from_indices + ']'
								frame_errors.append(error_text)

				arg_spans = list()
				arg_types = list()
				for arg in pb.findall('arg'):

					# Args should have numeric start/end tags and the correspondence in the example text (separated by whitespace)
					# should match with the contents in the text part of the arg
					arg_text = arg.text
					if not arg_text:
						error_text = roleset.get('id') + ': <arg> '
						if example.get('name'):
							error_text += 'in example "' + example.get('name') + '" '
						error_text += ' has no text contents.'
						frame_errors.append(error_text)
						continue
					start = arg.get('start')
					end = arg.get('end')
					if not start or not end or not start.isdigit() or not end.isdigit() or int(start) > int(end):
						# <arg> start/end indices must be present and valid.
						error_text = roleset.get('id') + ': <arg> '
						if arg_text:
							error_text += '"' + arg_text + '" '
						if example.get('name'):
							error_text += 'in example "' + example.get('name') + '" '
						error_text += ' contains invalid start/end indices.'
						frame_errors.append(error_text)
					elif tokenized_text:
						# <arg> text and tokens corresponding with start/end indices must match.
						try:
							arg_span_from_indices = ' '.join(tokenized_text[int(start):int(end)+1])
						except IndexError:
							arg_span_from_indices = None
							error_text = roleset.get('id') + ': <arg> '
							if arg_text:
								error_text += '"' + arg_text + '" '
							if example.get('name'):
								error_text += 'in example "' + example.get('name') + '" '
							error_text += ' has start/end indices out of range for the example text.'
							frame_errors.append(error_text)
						if arg_span_from_indices and arg_span_from_indices != arg_text:
							error_text = roleset.get('id') + ': <arg> '
							if arg_text:
								error_text += '"' + arg_text + '" '
							if example.get('name'):
								error_text += 'in example "' + example.get('name') + '" '
							error_text += ' has text that doesn\'t correspond with the start/end indices: [' + arg_text + '] vs. [' + arg_span_from_indices + ']'
							frame_errors.append(error_text)
						else:
							arg_spans.append([int(start), int(end)])

					if not arg.get('type', default=None):
						# Args need a type.
						error_text = roleset.get('id') + ': <arg> '
						if arg_text:
							error_text += '"' + arg_text + '" '
						if example.get('name'):
							error_text += 'in example "' + example.get('name') + '" '
						error_text += ' does not have a "type".'
						frame_errors.append(error_text)
					else:
						if arg.get('type') in arg_types and 'M' not in arg.get('type'):
							error_text = roleset.get('id') + ': Example '
							if example.get('name'):
								error_text += '"' + example.get('name') + '" '
							error_text += ' contains duplicate ' + arg.get('type') + 's.'
							frame_errors.append(error_text)
						else:
							arg_types.append(arg.get('type'))
				# TODO: Assert that no two arguments should overlap
				contains_overlaps = False
				for i in range(len(arg_spans)):
					span = arg_spans[i]
					for j in range(i+1, len(arg_spans)):
						other_span = arg_spans[j]
						if span[0] >= other_span[0] and span[1] <=other_span[1]:
							contains_overlaps = True
							break
					if contains_overlaps:
						break
				if contains_overlaps:
					error_text = roleset.get('id') + ': some <arg> tags '
					if example.get('name'):
						error_text += 'in example "' + example.get('name') + '" '
					error_text += ' contain overlapping start/end indices.'
					frame_errors.append(error_text)
	if frame_errors:
		found_errors = True
		print('\033[91m' + frame_file.name)
		if log_file:
			log_file.write(frame_file.name + '\n')
			log_file.write('\n'.join(frame_errors) + '\n\n')
		else:
			print('\n'.join(frame_errors))
	else:
		print('\033[92m' + frame_file.name)
	print('\033[0m', end='')
	if log_file:
		log_file.close()
	return found_errors

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--input", nargs='+', action="store", dest="input", help='Input frame directory or a list of files to check', required=True)
	parser.add_argument("-o", "--output", action="store", dest="output", help='Validation log file (optional)', default=None)

	args = parser.parse_args()
	if args.output and Path(args.output).exists():
		os.remove(args.output)
	frame_files = list()
	for filename in args.input:
		filename = Path(filename)
		assert filename.exists(), str(filename)
		if filename.is_dir():
			frame_files += filename.rglob('*.xml')
		else:
			frame_files.append(filename)
	for frame_file in frame_files:
		validate(frame_file, args.output)
