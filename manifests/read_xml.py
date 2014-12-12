import xml.etree.ElementTree as XML

manifest_root = XML.parse('tposs.xml').getroot()
stages = []

for buildstage in manifest_root.iter('buildstage'):
	stage = {'id': buildstage.get('id'),
		'dockerlines' : [],
		'bitbake_target' : {'cmd' : [], 'target' : [] }}
	stages.append(stage)

	for stage_command in buildstage.iter():

		if stage_command.tag == 'dockerline':
			stage['dockerlines'].append(stage_command.text)

		if stage_command.tag == 'bitbake_target':

			if stage_command.get('command'):
				stage['dockerlines'].append(stage_command.get('command'))
				stage['dockerlines'].append(stage['dockerlines'].pop() + " " + stage_command.text)
			else:
				stage['dockerlines'].append(stage_command.text)

print("\n".join(map(lambda x: str(x), stages)))
