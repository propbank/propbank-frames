#!/usr/bin/env python3
"""
Create a human-readable website listing the given frames.
"""

__author__ = "Skatje Myers"
__license__ = "CC-BY-SA-4.0"

import argparse
import os
import re
from pathlib import Path
from lxml import etree as ET

from validate_frames import validate


def main(frame_dir, website_dir, found_errors):
	# Read and extract frame info
	frame_files = frame_dir.rglob('*.xml')
	frames = dict()
	for frame_file in frame_files:
		try:
			xml = ET.parse(str(frame_file))
			frames[frame_file.name] = xml
		except Exception:
			pass  # TODO: If the XML can't be parsed, we're just ignoring the file. Should handle this better.
	website_title = 'PropBank Frames'

	all_rolesets = get_rolesets(frames)

	resources, roleset_to_resource_use = read_usagenotes(frames)

	alias_word_to_rolesets = get_aliases_to_rolesets(frames)

	create_css(website_dir)
	create_javascript(alias_word_to_rolesets, all_rolesets, resources, roleset_to_resource_use, website_dir)

	# Create common HTML elements
	## Create roleset search field
	search_rolesets_form = ET.Element('form', attrib={'autocomplete': 'off',
													  'method': 'post', 'name': 'rolesetSearch', 'style': 'margin:0 auto;width:300px'})
	div = ET.Element('div', attrib={'class': 'autocomplete'})
	search_rolesets_form.append(div)
	input = ET.Element('input', attrib={'id': 'searchRolesets', 'name': 'myRoleset', 'placeholder': 'Roleset ID',
										'type': 'text'})
	div.append(input)
	search_rolesets_form.append(ET.Element('input', attrib={'type': 'submit', 'value': 'Go'}))

	## Create alias search field
	search_aliases_form = ET.Element('form', attrib={'autocomplete': 'off',
													 'method': 'post', 'name': 'aliasSearch', 'style': 'float:right;'})
	div = ET.Element('div', attrib={'class': 'autocomplete'})
	search_aliases_form.append(div)
	input = ET.Element('input',
					   attrib={'id': 'searchAliases', 'name': 'myAlias', 'placeholder': 'Alias', 'type': 'text'})
	div.append(input)
	search_aliases_form.append(ET.Element('input', attrib={'type': 'submit', 'value': 'Search'}))

	## Create resource selection dropdown
	select_resource = ET.Element('select', attrib={'id': 'resource', 'style': 'font-size:30px;float:left;'})
	option = ET.Element('option', {'value': 'ALL'})
	option.text = 'All Frames'
	select_resource.append(option)
	for resource in resources:
		option = ET.Element('option', {'value': resource})
		option.text = resource.replace('_', ' ').replace('-', '.')
		select_resource.append(option)


	## Create header menu
	header_menu = ET.Element('div', attrib={'class': 'headerMenu'})
	header_menu.append(select_resource)
	header_menu.append(search_aliases_form)
	header_menu.append(search_rolesets_form)
	if Path(website_dir, 'frame_errors.txt').exists():
		footer = ET.Element('div', attrib={'class': 'footer'})
		span = ET.Element('span', attrib={'style':'color:red'})
		span.text = 'Warning: Frame validation failed '
		footer.append(span)
		a = ET.Element('a', attrib={'href':'frame_errors.txt'})
		a.text = '(see errors)'
		footer.append(a)

	# Create index.html
	print('Creating index.html')
	html = ET.Element('html', attrib={'lang':'en'})
	head = ET.Element('head')
	title = ET.Element('title')
	title.text = website_title
	head.append(title)
	head.append(ET.Element('link', attrib={'rel': "stylesheet", 'href': 'style.css'}))
	style = ET.Element('style')
	style.text = '.wrapper {grid-template-areas:\n"header"\n"headerMenu"\n"content"\n"footer";\n' \
                'grid-template-columns: 1fr;}\n'
	head.append(style)  # Get rid of the sidebar on the index page.
	html.append(head)
	body = ET.Element('body')
	html.append(body)

	wrapper = ET.Element('div', attrib={'class': 'wrapper'})
	body.append(wrapper)

	header = ET.Element('div', attrib={'class': 'header'})
	header.text = 'Frame Index'
	wrapper.append(header)
	wrapper.append(header_menu)

	content = ET.Element('div', attrib={'class':'content'})
	wrapper.append(content)
	content.append(ET.Element('div', attrib={'class': 'sticky-spacer'}))
	content_content = ET.Element('div', attrib={'class': 'sticky-content'})
	content.append(content_content)
	sorted_frames = list(frames.keys())
	sorted_frames.sort(key=lambda x: x.upper())
	curr_letter = sorted_frames[0][0]
	if curr_letter.isdigit():
		curr_letter = '0-9'
	h = ET.Element('h3')
	h.text = curr_letter.upper()
	alpha = ET.Element('div', attrib={'class': 'alpha'})
	content_content.append(alpha)
	alpha.append(h)
	columns = ET.Element('div', attrib={'class': 'columns'})
	alpha.append(columns)
	for frame_name in sorted_frames:
		if frame_name[0].upper() != curr_letter and not frame_name[0].isdigit():
			curr_letter = frame_name[0].upper()
			if curr_letter.isdigit():
				curr_letter = '0-9'
			h = ET.Element('h3')
			h.text = curr_letter
			alpha = ET.Element('div', attrib={'class': 'alpha'})
			content_content.append(alpha)
			alpha.append(h)
			columns = ET.Element('div', attrib={'class': 'columns'})
			alpha.append(columns)
		relevant_resources = set()
		rolesets = [roleset.get('id') for roleset in frames[frame_name].findall('predicate/roleset')]
		for roleset in rolesets:
			relevant_resources.update(roleset_to_resource_use[roleset])
		relevant_resources = list(relevant_resources)
		p = ET.Element('p', attrib={'class': 'resource-dependent ' + ' '.join(relevant_resources)})
		columns.append(p)
		if frame_name[:-3] == 'index.':
			a = ET.Element('a', attrib={'href': 'f_' + frame_name[:-3] + 'html'})
		else:
			a = ET.Element('a', attrib={'href': frame_name[:-3] + 'html'})
		p.append(a)
		a.text = frame_name[:-4]
	if found_errors:
		wrapper.append(footer)
	body.append(ET.Element('script', attrib={'src': 'https://code.jquery.com/jquery-3.5.1.min.js'}))
	body.append(ET.Element('script', attrib={'src': "script.js"}))
	ET.ElementTree(html).write(str(Path(website_dir, 'index.html')), method='html')

	# Create roleset HTML files: abate.html, etc.
	for frame_name, xml in frames.items():
		print(frame_name[:-3] + 'html')
		if frame_name.startswith('spatial-91') or frame_name.startswith('statistical-test'):
			continue  # TODO: Make compatible with AMR weirdness
		if frame_name[:-3] == 'index.':
			file = Path(website_dir, 'f_' + frame_name[:-3] + 'html')
		else:
			file = Path(website_dir, frame_name[:-3] + 'html')
		html = ET.Element('html', attrib={'lang':'en'})
		head = ET.Element('head')
		title = ET.Element('title')
		title.text = '"' + frame_name[:frame_name.rindex('.')] + '" Rolesets'
		head.append(title)
		html.append(head)
		head.append(ET.Element('link', attrib={'rel': "stylesheet", 'href': 'style.css'}))
		body = ET.Element('body')
		html.append(body)

		wrapper = ET.Element('div', attrib={'class': 'wrapper'})
		body.append(wrapper)

		header = ET.Element('div', attrib={'class': 'header'})
		header.text = 'Rolesets - ' + frame_name[:-4]
		wrapper.append(header)

		wrapper.append(header_menu)

		sidebar = ET.Element('div', attrib={'class': 'sidebar'})
		sidebar.append(ET.Element('div', attrib={'class': 'sticky-spacer'}))
		sidebar_content = ET.Element('div', attrib={'class': 'sticky-content'})
		a = ET.Element('a', attrib={'href': 'index.html'})
		a.text = '⮪ Index'
		sidebar_content.append(a)
		sidebar.append(sidebar_content)
		wrapper.append(sidebar)

		content = ET.Element('div', attrib={'class': 'content'})
		wrapper.append(content)
		content.append(ET.Element('div', attrib={'class': 'sticky-spacer'}))
		content_content = ET.Element('div', attrib={'class': 'sticky-content'})
		content.append(content_content)

		for pred in xml.findall('predicate'):
			pred_heading = ET.Element('h2')
			pred_heading.text = pred.get('lemma')
			content_content.append(pred_heading)
			rs = pred.findall('roleset')
			for roleset in rs:
				div = create_roleset_div(roleset, roleset_to_resource_use)
				content_content.append(div)
				relevant_resources = roleset_to_resource_use[roleset.get('id')]
				a = ET.Element('a', attrib={'href': frame_name[:-3] + 'html#' + roleset.get('id'), 'class': 'resource-dependent ' + ' '.join(relevant_resources)})
				a.text = roleset.get('id')
				sidebar_content.append(a)
		if found_errors:
			wrapper.append(footer)
		body.append(ET.Element('script', attrib={'src': 'https://code.jquery.com/jquery-3.5.1.min.js'}))
		body.append(ET.Element('script', attrib={'src': "script.js"}))
		ET.ElementTree(html).write(str(file), method='html')

	##  Create alias HTML pages for searching by alias
	for alias, rolesets in alias_word_to_rolesets.items():
		print('alias-' + alias + '.html')
		html = ET.Element('html', attrib={'lang':'en'})
		head = ET.Element('head')
		title = ET.Element('title')
		title.text = 'Rolesets for alias "' + alias + '"'
		head.append(title)
		html.append(head)
		head.append(ET.Element('link', attrib={'rel': "stylesheet", 'href': 'style.css'}))
		body = ET.Element('body')
		html.append(body)

		wrapper = ET.Element('div', attrib={'class': 'wrapper'})
		body.append(wrapper)

		header = ET.Element('div', attrib={'class': 'header'})
		header.text = 'Aliases - ' + alias
		wrapper.append(header)

		wrapper.append(header_menu)

		sidebar = ET.Element('div', attrib={'class': 'sidebar'})
		sidebar.append(ET.Element('div', attrib={'class': 'sticky-spacer'}))
		sidebar_content = ET.Element('div', attrib={'class': 'sticky-content'})
		a = ET.Element('a', attrib={'href': 'index.html'})
		a.text = '⮪ Index'  # TODO: What do we put in the sidebar for alias pages?
		sidebar_content.append(a)
		sidebar.append(sidebar_content)
		wrapper.append(sidebar)

		content = ET.Element('div', attrib={'class': 'content'})
		wrapper.append(content)
		content.append(ET.Element('div', attrib={'class': 'sticky-spacer'}))
		content_content = ET.Element('div', attrib={'class': 'sticky-content'})
		content.append(content_content)

		for roleset in rolesets:
			if roleset.get('id').startswith('statistical-test'):
				continue  # TODO: AMR weirdness
			div = create_roleset_div(roleset, roleset_to_resource_use)
			content_content.append(div)
		if found_errors:
			wrapper.append(footer)
		body.append(ET.Element('script', attrib={'src': 'https://code.jquery.com/jquery-3.5.1.min.js'}))
		body.append(ET.Element('script', attrib={'src': "script.js"}))
		if '/' in alias:
			alias = re.sub('/', '-', alias)
		ET.ElementTree(html).write(str(Path(website_dir, 'alias-' + alias + '.html')), method='html')


def get_rolesets(frames):
	all_rolesets = dict()
	for frame_name, xml in frames.items():
		rs = [e.get('id') for e in xml.findall('predicate/roleset')]
		for id in rs:
			all_rolesets[id] = frame_name[:-4]
	return all_rolesets


def read_usagenotes(frames):
	resources = set()
	roleset_to_resource_use = dict()
	for frame_name, xml in frames.items():
		resource_names = [e.get('resource') + '_' + e.get('version').replace('.', '-').replace(' ', '_') for e in
						  xml.findall('predicate/roleset/usagenotes/usage')]
		rs = xml.findall('predicate/roleset')
		for roleset in rs:
			usages = [e.get('resource') + '_' + e.get('version').replace('.', '-').replace(' ', '_') for e in
					  roleset.findall('usagenotes/usage') if e.get('inuse') == '+']
			roleset_to_resource_use[roleset.get('id')] = usages
		resources.update(resource_names)
	resources = list(resources)
	resources = sorted(resources)
	return resources, roleset_to_resource_use


def get_aliases_to_rolesets(frames):
	alias_word_to_rolesets = dict()
	for frame_name, xml in frames.items():
		for roleset in xml.findall('predicate/roleset'):
			aliases = roleset.find('aliases')
			if not aliases:
				continue
			aliases = aliases.findall('alias')
			for alias in aliases:
				if '\n' in alias.text:
					print('')
				if alias.text not in alias_word_to_rolesets:
					alias_word_to_rolesets[alias.text] = [roleset]
				else:
					alias_word_to_rolesets[alias.text].append(roleset)
	for alias, rolesets in alias_word_to_rolesets.items():
		rolesets.sort(key=lambda x: x.get('id'))
	return alias_word_to_rolesets


def get_arg_color(arg):
	if not isinstance(arg, str):
		if arg.name == 'rel':
			return 'LIGHTCORAL'  # Reddish
		else:
			arg = arg['n']
	if arg == '0' or arg == 'ARG0':
		return 'AQUAMARINE'  # Blue
	elif arg == '1' or arg == 'ARG1':
		return 'PALEGREEN'  # Green
	elif arg == '2' or arg == 'ARG2':
		return 'PLUM'  # Purple
	elif arg == '3' or arg == 'ARG3':
		return 'LIGHTSKYBLUE'  # Light blue
	elif arg == '4' or arg == 'ARG4':
		return 'KHAKI'  # Brown
	elif arg == '5' or arg == 'ARG5':
		return 'WHEAT'  # Yellow
	elif arg == '6' or arg == 'ARG6':
		return 'PINK'
	elif arg == '7' or arg == 'ARG7':
		return 'LIGHTSALMON'
	elif arg == '8':
		return 'GREEN'
	elif arg == '9':
		return 'TOMATO'
	elif arg == '10':
		return 'SLATEBLUE'
	elif arg == 'm' or arg == 'M' or arg.startswith('ARGM'):
		return 'GAINSBORO'  # Grey
	elif arg == 'rel':
		return 'LIGHTCORAL'
	elif arg == 'ARGA':
		return 'GREENYELLOW'
	else:
		return 'GAINSBORO'  # TODO: Need some validation on these crazy arg types...


def create_roleset_div(roleset, roleset_to_resource_use):
	div = ET.Element('div', attrib={
		'class': 'roleset resource-dependent ' + ' '.join(roleset_to_resource_use[roleset.get('id')])})
	div.append(ET.Element('a', attrib={'id': roleset.get('id')}))
	roleset_heading = ET.Element('h3')
	div.append(roleset_heading)
	roleset_heading.text = roleset.get('id') + ' - '
	i = ET.Element('i')
	i.text = roleset.get('name')
	roleset_heading.append(i)
	notes = roleset.findall('note')
	for note in notes:
		span = ET.Element('span', attrib={'style': 'font-size:10px;'})
		span.text = note.text
		div.append(span)
		div.append(ET.Element('br'))
	alias_head = ET.Element('h4')
	div.append(alias_head)
	alias_head.text = 'Aliases:'
	aliases = roleset.findall('aliases/alias')
	indent = ET.Element('div', attrib={'style': 'padding-left: 20px;'})
	div.append(indent)
	for alias in aliases:
		ali_tag = ET.Element('span')
		indent.append(ali_tag)
		ali_tag.text = alias.text + ' (' + alias.get('pos') + '.)'
		indent.append(ET.Element('br'))
	roles_head = ET.Element('h4')
	div.append(roles_head)
	roles_head.text = 'Roles:'
	roles = roleset.findall('roles/role')
	indent = ET.Element('div', attrib={'style': 'padding-left: 20px;'})
	div.append(indent)
	for role in roles:
		role_tag = ET.Element('span')
		indent.append(role_tag)
		colour = get_arg_color(role.get('n'))
		span = ET.Element('span', attrib={'style': 'background-color:' + colour})
		role_tag.append(span)
		span.text = 'ARG' + role.get('n').upper() + '-' + role.get('f')
		colon = ET.Element('span')
		colon.text = ': '
		role_tag.append(colon)
		it = ET.Element('i')
		it.text = role.get('descr')
		role_tag.append(it)
		indent.append(ET.Element('br'))
	# TODO: rolelinks
	# TODO: Lexlinks
	examples = roleset.findall('example')
	for example in examples:
		example_div = ET.Element('div', attrib={'class': 'example'})
		div.append(example_div)
		head = ET.Element('h4')
		head.text = example.get('name')
		example_div.append(head)
		if 'src' in example:
			src = ET.Element('span')
			src.text = example.get('src')
			example_div.append(src)
		args = example.findall('propbank/arg') + example.findall('propbank/rel')
		arg_start_to_arg = dict()
		broken_args = list()
		for arg in args:
			# TODO: Multiple args may start at a given spot?
			if arg.tag == 'rel':
				if ' ' in arg.get('relloc'):
					split = arg.get('relloc').split(' ')
					for j in range(len(split)):
						index = split[j]
						arg_start_to_arg[int(index)] = [int(index), 'rel', arg.text.split(' ')[j]]
				else:
					if arg.get('relloc') == '?':
						broken_args.append(arg)
					else:
						arg_start_to_arg[int(arg.get('relloc'))] = [int(arg.get('relloc')), 'rel', arg.text]
			else:
				arg_name = arg.get('type')
				if not arg.get('start').isdigit() or not arg.get('end').isdigit():
					broken_args.append(arg)
				elif int(arg.get('start')) > int(arg.get('end')):
					broken_args.append(arg)
				else:
					arg_start_to_arg[int(arg.get('start'))] = [int(arg.get('end')), arg_name, arg.text]
		if example.find('text') is None or example.find('text').text is None:
			continue
		tokenized = example.find('text').text.split(' ')
		example_string = ''
		i = 0
		while i < len(tokenized):
			if i in arg_start_to_arg:
				example_string += '<div class="tooltip"><span style="background-color: '
				example_string += get_arg_color(arg_start_to_arg[i][1]) + '">' + \
								  arg_start_to_arg[i][2] + \
								  '</span><span class="tooltiptext">' + arg_start_to_arg[i][1] + '</span></div> '
				i += arg_start_to_arg[i][0] + 1 - i
			else:
				if i == len(tokenized) - 1:
					example_string += '<span>' + tokenized[i] + '</span>'
				else:
					example_string += '<span>' + tokenized[i] + ' </span>'
				i += 1

		# Print out broken_args
		for arg in broken_args:
			if arg.text == None:
				continue
			if arg.tag == 'rel':
				example_string += '<br /><span><b>Rel</b>: ' + arg.text + '</span>'
			else:
				example_string += '<br /><span><b>' + arg.get('type') + '</b>: ' + arg.text + '</span>'

		# TODO: Hide AMR examples based on usage tag
		# TODO Use penman to prettify format, if possible.
		amrs = example.findall('amr')
		attrib = {'class': 'roleset resource-dependent ' + ' '.join(roleset_to_resource_use[roleset.get('id')])}
		for amr in amrs:
			amr = amr.text[1:]
			example_string += '<br /><br /><pre>' + amr + '</pre>'
		escaped = example_string.replace('&', '&amp;')
		e = ET.fromstring('<div>' + escaped + '</div>')
		example_div.append(e)
	return div


def create_javascript(alias_word_to_rolesets, all_rolesets, resources, roleset_to_resource_use, website_dir):
	javascript = '\nfunction autocomplete(inp, arr) {' \
				 '\n  /*the autocomplete function takes two arguments,' \
				 '\n  the text field element and an array of possible autocompleted values:*/' \
				 '\n  var currentFocus;' \
				 '\n  /*execute a function when someone writes in the text field:*/' \
				 '\n  inp.addEventListener("input", function(e) {' \
				 '\n      var a, b, i, val = this.value;' \
				 '\n      /*close any already open lists of autocompleted values*/' \
				 '\n      closeAllLists();' \
				 '\n      if (!val) { return false;}' \
				 '\n      currentFocus = -1;' \
				 '\n      /*create a DIV element that will contain the items (values):*/' \
				 '\n      a = document.createElement("DIV");' \
				 '\n      a.setAttribute("id", this.id + "autocomplete-list");' \
				 '\n      a.setAttribute("class", "autocomplete-items");' \
				 '\n      /*append the DIV element as a child of the autocomplete container:*/' \
				 '\n      this.parentNode.appendChild(a);' \
				 '\n      /*for each item in the array...*/' \
				 '\n      for (i = 0; i < arr.length; i++) {' \
				 '\n        /*check if the item starts with the same letters as the text field value:*/' \
				 '\n        if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {' \
				 '\n          /*create a DIV element for each matching element:*/' \
				 '\n          b = document.createElement("DIV");' \
				 '\n		  var currResource = $("select").find("option:selected").val();' \
				 '\n		  if (currResource != "ALL") {' \
				 '\n		      if ((arr[i] in roleset_to_resources && !roleset_to_resources[arr[i]].includes(currResource)) || (arr[i] in alias_to_resources && !alias_to_resources[arr[i]].includes(currResource))) {' \
				 '\n		          continue;' \
				 '\n		      }' \
				 '\n		  }' \
				 '\n          /*make the matching letters bold:*/' \
				 '\n          b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";' \
				 '\n          b.innerHTML += arr[i].substr(val.length);' \
				 '\n          /*insert a input field that will hold the current array item\'s value:*/' \
				 '\n          b.innerHTML += "<input type=\'hidden\' value=\'" + arr[i] + "\'>";' \
				 '\n          /*execute a function when someone clicks on the item value (DIV element):*/' \
				 '\n              b.addEventListener("click", function(e) {' \
				 '\n              /*insert the value for the autocomplete text field:*/' \
				 '\n              inp.value = this.getElementsByTagName("input")[0].value;' \
				 '\n              /*close the list of autocompleted values,' \
				 '\n              (or any other open lists of autocompleted values:*/' \
				 '\n              closeAllLists();' \
				 '\n          });' \
				 '\n          a.appendChild(b);' \
				 '\n        }' \
				 '\n      }' \
				 '\n  });' \
				 '\n  /*execute a function presses a key on the keyboard:*/' \
				 '\n  inp.addEventListener("keydown", function(e) {' \
				 '\n      var x = document.getElementById(this.id + "autocomplete-list");' \
				 '\n      if (x) x = x.getElementsByTagName("div");' \
				 '\n      if (e.keyCode == 40) {' \
				 '\n        /*If the arrow DOWN key is pressed,' \
				 '\n        increase the currentFocus variable:*/' \
				 '\n        currentFocus++;' \
				 '\n        /*and and make the current item more visible:*/' \
				 '\n        addActive(x);' \
				 '\n      } else if (e.keyCode == 38) { //up' \
				 '\n        /*If the arrow UP key is pressed,' \
				 '\n        decrease the currentFocus variable:*/' \
				 '\n        currentFocus--;' \
				 '\n        /*and and make the current item more visible:*/' \
				 '\n        addActive(x);' \
				 '\n      } else if (e.keyCode == 13) {' \
				 '\n        /*If the ENTER key is pressed, prevent the form from being submitted,*/' \
				 '\n        e.preventDefault();' \
				 '\n        if (currentFocus > -1) {' \
				 '\n          /*and simulate a click on the "active" item:*/' \
				 '\n          if (x) x[currentFocus].click();' \
				 '\n        }' \
				 '\n      }' \
				 '\n  });' \
				 '\n  function addActive(x) {' \
				 '\n    /*a function to classify an item as "active":*/' \
				 '\n    if (!x) return false;' \
				 '\n    /*start by removing the "active" class on all items:*/' \
				 '\n    removeActive(x);' \
				 '\n    if (currentFocus >= x.length) currentFocus = 0;' \
				 '\n    if (currentFocus < 0) currentFocus = (x.length - 1);' \
				 '\n    /*add class "autocomplete-active":*/' \
				 '\n    x[currentFocus].classList.add("autocomplete-active");' \
				 '\n  }' \
				 '\n  function removeActive(x) {' \
				 '\n    /*a function to remove the "active" class from all autocomplete items:*/' \
				 '\n    for (var i = 0; i < x.length; i++) {' \
				 '\n      x[i].classList.remove("autocomplete-active");' \
				 '\n    }' \
				 '\n  }' \
				 '\n  function closeAllLists(elmnt) {' \
				 '\n    /*close all autocomplete lists in the document,' \
				 '\n    except the one passed as an argument:*/' \
				 '\n    var x = document.getElementsByClassName("autocomplete-items");' \
				 '\n    for (var i = 0; i < x.length; i++) {' \
				 '\n      if (elmnt != x[i] && elmnt != inp) {' \
				 '\n      x[i].parentNode.removeChild(x[i]);' \
				 '\n    }' \
				 '\n  }' \
				 '\n}' \
				 '\n/*execute a function when someone clicks in the document:*/' \
				 '\ndocument.addEventListener("click", function (e) {' \
				 '\n    closeAllLists(e.target);' \
				 '\n});' \
				 '\n}\n' \
				 'function offsetAnchor() {\n' \
				 '    if(location.hash.length !== 0) {\n' \
				 '        window.scrollTo(window.scrollX, window.scrollY - 100);\n' \
				 '    }\n' \
				 '}\n' \
				 'window.addEventListener("hashchange", offsetAnchor);\n' \
				 'window.setTimeout(offsetAnchor, 1);\n'
	## Roleset to resources:
	javascript += '\nvar roleset_to_resources = {' + ',\n'.join(['"' + roleset + '":["' + '","'.join(resources) + '"]' for roleset, resources in roleset_to_resource_use.items()]) + '};\n'
	## Alias to resources:
	javascript += '\nvar alias_to_resources = {'
	for alias, rolesets in alias_word_to_rolesets.items():
		alias_resources = set()
		for roleset in rolesets:
			alias_resources.update(roleset_to_resource_use[roleset.get('id')])
		alias_resources = list(alias_resources)
		javascript += '"' + alias + '":["' + '","'.join(alias_resources) + '"],\n'
	javascript += '};\n'

	## Roleset search functions:
	javascript += '\nvar rolesets = ["' + '", "'.join(all_rolesets.keys()) + '"]\n\n'
	javascript += '\nautocomplete(document.getElementById("searchRolesets"), rolesets);'
	javascript += '\nvar rolesetToPred ={'
	for roleset, pred in all_rolesets.items():
		javascript += '\n"' + roleset + '": "' + pred + '",'
	javascript += '\n}\n'
	javascript += '\n$("form[name=rolesetSearch]").on("submit", (e) => { e.preventDefault(); window.location=rolesetToPred[$("#searchRolesets").val()] + ".html#" + $("#searchRolesets").val(); });'

	## Alias search functions:
	javascript += '\nvar aliases = ["' + '", "'.join(alias_word_to_rolesets.keys()) + '"]\n\n'
	javascript += '\nautocomplete(document.getElementById("searchAliases"), aliases);'
	javascript += '\n$("form[name=aliasSearch]").on("submit", (e) => { e.preventDefault(); window.location="alias-" + $("#searchAliases").val().replace("/", "-") + ".html#" + $("#searchAliases").val(); });'

	## Resource usage dropdown function:
	javascript += '\nvar resources ={'
	for i in range(len(resources)):
		javascript += '\n"' + str(i) + '": "' + resources[i] + '",'
	javascript += '}\n'
	javascript += '\nfunction showHideUsedElements(){\n' \
				  '    $("select").change(function(){\n' \
				  '        $(this).find("option:selected").each(function(){\n' \
				  '            var optionValue = $(this).val();\n' \
				  '            if(optionValue == "ALL"){\n' \
				  '                $(".resource-dependent").show();\n' \
				  '            } else{\n' \
				  '                $(".resource-dependent").filter("."+optionValue).show();\n' \
				  '                $(".resource-dependent").filter(":not(."+optionValue+")").hide();\n' \
				  '            }\n' \
				  '        localStorage.setItem("usageValue", $(this).val());\n' \
				  '        });\n' \
				  '    }).change();\n' \
				  '};\n' \
				  'var usageValue = localStorage.getItem("usageValue");\n' \
				  'if(usageValue != null) {\n' \
				  '    $("select").val(usageValue);\n' \
				  '}\n\n' \
				  'showHideUsedElements();\n\n'
	Path(website_dir, 'script.js').write_text(javascript)


def create_css(website_dir):
	css_contents = 'html, body { margin: 0; padding: 0 }\n' \
				  '.wrapper {\n' \
				  '  display: grid;\n' \
				  '  /* Header and footer span the entire width, sidebars and content are fixed, with empty space on sides */\n' \
				  '  grid-template-areas:\n' \
				  '    "header header"\n' \
				  '    "headerMenu headerMenu"\n' \
				  '    "sidebar content"\n' \
				  '    "footer footer";\n' \
				  '  /* Only expand middle section vertically (content and sidebars) */\n' \
				  '  grid-template-rows: 0fr 0fr 1fr 0fr;\n' \
				  '  /* 100% width, but static widths for content and sidebars */\n' \
				  '  grid-template-columns: 150px 1fr;\n' \
				  '  /* Force grid to be at least the height of the screen */\n' \
				  '  min-height: 100vh;\n' \
				'}\n' \
				   '.header {\n' \
				   '  grid-area: header;\n' \
				   '\n' \
				   '  /* Stick header to top of grid */\n' \
				   '  position: sticky;\n' \
				   '  top: 0;\n' \
				   '  /* Ensure header appears on top of content/sidebars */\n' \
				   '  z-index: 1;\n' \
				   '\n' \
				   '  /* General appearance */\n' \
				   '  background-color: #f1f1f1;\n' \
				   '  text-align: center;\n' \
				   '  font-size: 1.5rem;\n' \
				   '  line-height: 1.5;\n' \
				   '  padding: 1rem;\n' \
				   '}\n' \
				   '/* Save header height to properly set `padding-top` and `margin-top` for sticky content */\n' \
				   ':root {\n' \
				   '  --header-height: calc(1rem * 1.5 + 1rem * 2);\n' \
				   '}\n' \
				   '\n' \
				   '.headerMenu {\n' \
				   '  grid-area: headerMenu;\n' \
				   '\n' \
				   '  /* Stick header to top of grid */\n' \
				   '  position: sticky;\n' \
				   '  top: 0;\n' \
				   '  /* Ensure header appears on top of content/sidebars */\n' \
				   '  z-index: 1;\n' \
				   '\n' \
				   '  /* General appearance */\n' \
				   '  background-color: #CCC;\n' \
				   '  text-align: center;\n' \
				   '  font-size: 1rem;\n' \
				   '  line-height: 1.5;\n' \
				   '  padding: 1rem;\n' \
				   '}\n' \
				   '/* Save header height to properly set `padding-top` and `margin-top` for sticky content */\n' \
				   ':root {\n' \
				   '  --headerMenu-height: calc(1rem * 1.5 + 1rem * 2 + 1rem);\n' \
				   '}\n' \
				   '\n' \
				   '.sidebar {\n' \
				   '  grid-area: sidebar;\n' \
				   '}\n' \
				   '\n' \
				   '.sidebar {\n' \
				   '  display: flex;\n' \
				   '  flex-direction: column;\n' \
				   '  position: sticky;\n' \
				   '  top: 0;\n' \
				   '  background-color: #777;\n' \
				   '  overflow: auto;\n' \
  				   '  max-height: 100vh;\n' \
				   '}\n' \
				   '.sidebar a {\n' \
				  '  padding: 6px 6px 6px 6px;\n' \
				  '  text-decoration: none;\n' \
				  '  font-size: 18px;\n' \
				  '  text-align: center;\n' \
				  '  color: #222;\n' \
				  '  display: block;\n' \
				  '}\n' \
				  '.sidebar a:hover {\n' \
				  '  color: #f1f1f1;\n' \
				  '}\n' \
				   '\n' \
				   '.content {\n' \
				   '  grid-area: content;\n' \
				   '  /* General appearance */\n' \
				   '  background-color: #e3ffdc;\n' \
				   '}\n' \
				   '.footer {\n' \
				   '  grid-area: footer;\n' \
				   '\n' \
				   '  /* Stick footer to bottom of grid */\n' \
				   '  position: sticky;\n' \
				   '  bottom: 0;\n' \
				   '\n' \
				   '  /* General appearance */\n' \
				   '  background-color: #CCC;\n' \
				   '  text-align: center;\n' \
				   '  font-size: .8rem;\n' \
				   '  line-height: 1.5;\n' \
				   '  padding: .5rem;\n' \
				   '}\n' \
				   '/* Save footer height to properly set `bottom` and `min-height` for sticky content */\n' \
				   ':root {\n' \
				   '  --footer-height: calc(.8rem * 1.5 + .5rem * 2);\n' \
				   '}\n' \
				   '\n' \
				   '.sticky-spacer {\n' \
				   '  flex-grow: 1;\n' \
				   '}\n' \
				   '.sticky-content {\n' \
				   '  position: sticky;\n' \
				   '  bottom: var(--footer-height);\n' \
				   '  min-height: calc(100vh - var(--footer-height));\n' \
				   '  box-sizing: border-box;\n' \
				   '\n' \
				   '  --padding: 10px;\n' \
				   '  padding:\n' \
				   '    calc(var(--headerMenu-height) + var(--padding))\n' \
				   '    var(--padding)\n' \
				   '    var(--padding);\n' \
				   '  margin-top: calc(0px - var(--headerMenu-height));\n' \
				   '}\n' \
				   '.roleset {\n' \
				   '  border: 1px solid #000000;\n' \
				   '  background-color: #fff7c9;\n' \
				   '  margin-bottom: 20px;\n' \
				   '  padding: 10px;\n' \
				   '}\n' \
				   '\n' \
				   '.example {\n' \
				   '  border: 1px solid #000000;\n' \
				   '  background-color: #f7fff4;\n' \
				   '  margin-bottom: 10px;\n' \
				   '  padding: 5px;\n' \
				   '}\n' \
				   '\n' \
				   '.autocomplete {\n' \
				   '  /*the container must be positioned relative:*/\n' \
				   '  position: relative;\n' \
				   '  display: inline-block;\n' \
				   '}\n' \
				   'input {\n' \
				   '  border: 1px solid transparent;\n' \
				   '  background-color: #f1f1f1;\n' \
				   '  padding: 10px;\n' \
				   '  font-size: 16px;\n' \
				   '}\n' \
				   'input[type=text] {\n' \
				   '  background-color: #f1f1f1;\n' \
				   '  width: 100%;\n' \
				   '}\n' \
				   'input[type=submit] {\n' \
				   '  background-color: DodgerBlue;\n' \
				   '  color: #fff;\n' \
				   '}\n' \
				   '.autocomplete-items {\n' \
				   '  position: absolute;\n' \
				   '  border: 1px solid #d4d4d4;\n' \
				   '  border-bottom: none;\n' \
				   '  border-top: none;\n' \
				   '  z-index: 99;\n' \
				   '  /*position the autocomplete items to be the same width as the container:*/\n' \
				   '  top: 100%;\n' \
				   '  left: 0;\n' \
				   '  right: 0;\n' \
				   '}\n' \
				   '.autocomplete-items div {\n' \
				   '  padding: 10px;\n' \
				   '  cursor: pointer;\n' \
				   '  background-color: #fff;\n' \
				   '  color: #000;\n' \
				   '  border-bottom: 1px solid #d4d4d4;\n' \
				   '}\n' \
				   '.autocomplete-items div:hover {\n' \
				   '  /*when hovering an item:*/\n' \
				   '  background-color: #e9e9e9;\n' \
				   '}\n' \
				   '.autocomplete-active {\n' \
				   '  /*when navigating through the items using the arrow keys:*/\n' \
				   '  background-color: DodgerBlue !important;\n' \
				   '  color: #ffffff;\n' \
				   '}\n' \
				   '\n' \
				   '/* Tooltip container */\n' \
				   '.tooltip {\n' \
				   '  position: relative;\n' \
				   '  display: inline-block;\n' \
				   '}\n' \
				   '\n' \
				   '/* Tooltip text */\n' \
				   '.tooltip .tooltiptext {\n' \
				   '  visibility: hidden;\n' \
				   '  width: 120px;\n' \
				   '  background-color: #555;\n' \
				   '  color: #fff;\n' \
				   '  text-align: center;\n' \
				   '  padding: 5px 0;\n' \
				   '  border-radius: 6px;\n' \
				   '\n' \
				   '  /* Position the tooltip text */\n' \
				   '  position: absolute;\n' \
				   '  z-index: 1;\n' \
				   '  bottom: 125%;\n' \
				   '  left: 50%;\n' \
				   '  margin-left: -60px;\n' \
				   '\n' \
				   '  /* Fade in tooltip */\n' \
				   '  opacity: 0;\n' \
				   '  transition: opacity 0.3s;\n' \
				   '}\n' \
				   '\n' \
				   '/* Tooltip arrow */\n' \
				   '.tooltip .tooltiptext::after {\n' \
				   '  content: "";\n' \
				   '  position: absolute;\n' \
				   '  top: 100%;\n' \
				   '  left: 50%;\n' \
				   '  margin-left: -5px;\n' \
				   '  border-width: 5px;\n' \
				   '  border-style: solid;\n' \
				   '  border-color: #555 transparent transparent transparent;\n' \
				   '}\n' \
				   '\n' \
				   '/* Show the tooltip text when you mouse over the tooltip container */\n' \
				   '.tooltip:hover .tooltiptext {\n' \
				   '  visibility: visible;\n' \
				   '  opacity: 1;\n' \
				   '}\n' \
				   '.alpha {\n' \
				   '  border: 1px solid #000000;\n' \
				   '  background-color: #f7fff4;\n' \
				   '  margin-bottom: 10px;\n' \
				   '  padding: 5px;\n' \
				   '}\n' \
				   '\n' \
				   '.columns {\n' \
				   '  -webkit-columns: 4;\n' \
				   '  -moz-columns: 4;\n' \
				   '  columns: 4 auto;\n' \
				   '\n' \
				   '}\n' \
				   '.columns p {\n' \
				   '  margin: 0;\n' \
				   '}\n'

	css_file = Path(website_dir, 'style.css')
	css_file.write_text(css_contents)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--input", action="store", dest="input", help='Input frame directory', required=True)
	parser.add_argument("-o", "--output", action="store", dest="output", help='Output website directory', required=True)

	args = parser.parse_args()
	input_frames = Path(args.input)
	assert input_frames.exists()
	website_dir = Path(args.output)
	website_dir.mkdir(exist_ok=True)
	if Path(website_dir, 'frame_errors.txt').exists():
		os.remove(Path(website_dir, 'frame_errors.txt'))
	need_error_warning = False
	for frame_file in input_frames.rglob('*.xml'):
		found_errors = validate(frame_file, Path(website_dir, 'frame_errors.txt'))  # TODO: We should have it spit out the errors to a file, then make them accessible via HTML
		need_error_warning = need_error_warning or found_errors
	main(input_frames, website_dir, need_error_warning)
