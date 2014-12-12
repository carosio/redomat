import xml.etree.ElementTree as XML

manifest_root = XML.parse('tposs.xml').getroot()
build_cmd = {}

for buildstage in manifest_root.findall('buildstage'):
	cmd = ""
	target = ""
	ID = buildstage.get('id')
	build_cmd.update({ID : None})
	for bitbake_target in buildstage.findall('bitbake_target'):
		if bitbake_target.get('command') is not "":
			cmd += bitbake_target.get('command') + " "
		target += bitbake_target.text + " "
		build_cmd.update({ID : cmd + target})


# xml find all buildstages and buildcommands etc.
#for buildstage in manifest_root.findall('buildstage'):
#	build_cmd.update({buildstage.get('id'):None})
#	BS = build
#	for cmd in buildstage.findall('bitbake_target'):
#		text += cmd.get('command') + " "
#	for cmd in buildstage.findall('bitbake_target'):
#		text += cmd.text + " "
#	build_cmd.update({buildstage.get('id') : text})
print(build_cmd)
