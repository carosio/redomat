import xml.etree.ElementTree as XML

manifest_root = XML.parse('tposs.xml').getroot()
build_cmd = {}

stages = []

for buildstage in manifest_root.iter('buildstage'):
	cmd = ""
	target = ""
	stage = {'id': buildstage.get('id')}
	stages.append(stage)

	for stage_command in buildstage.iter():
		if stage_command == 'dockerline':
			stage['commands'].append({...})

		if bitbake_target.get('command'):
			cmd += bitbake_target.get('command') + " "
		target += bitbake_target.text + " "
		stage['cmd'] = cmd + target


# xml find all buildstages and buildcommands etc.
#for buildstage in manifest_root.findall('buildstage'):
#	build_cmd.update({buildstage.get('id'):None})
#	BS = build
#	for cmd in buildstage.findall('bitbake_target'):
#		text += cmd.get('command') + " "
#	for cmd in buildstage.findall('bitbake_target'):
#		text += cmd.text + " "
#	build_cmd.update({buildstage.get('id') : text})
print("\n".join(map(lambda x: str(x), stages)))
