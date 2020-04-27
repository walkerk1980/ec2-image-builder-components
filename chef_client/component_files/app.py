import json
import yaml
import boto3

def read_component_yaml(component_yaml):
  with open(component_yaml, 'r') as file:
    return yaml.safe_load(file)

def get_existing_component(ib, platform, component_config):
  existing_component = ib.list_components(
    owner = 'Self',
    filters = [
      {
        'name': 'name',
        'values': [component_config.get('name')]
      },
      {
        'name': 'platform',
        'values': [platform]
      }
    ]
  )
  if len(existing_component.get('componentVersionList')) > 0:
    return existing_component.get('componentVersionList')
  else:
    return None

def increment_version_number(version):
  version_list = version.split('.')
  major = version_list[0]
  minor = version_list[1]
  patch = version_list[2]
  patch = str(int(patch) +1)
  return '{0}.{1}.{2}'.format(major, minor, patch)

def increment_past_existing_version(component, version):
  version_match = [ (x) for x in component if x.get('version') == version ]
  if len(version_match) > 0:
    version = increment_version_number(version)
    return increment_past_existing_version(component, version)
  else:
   return version

def create_component(ib, platform, component_config):
  existing_component = get_existing_component(ib, platform, component_config)
  version = '1.0.0'
  changeDescription = component_config.get('changeDescription')
  if not changeDescription:
    changeDescription = ' '
  if component_config.get('version'):
    version = component_config.get('version')
  if existing_component:
    version = increment_past_existing_version(existing_component, version)
  #  return existing_component
  #else:
  new_component = ib.create_component(
    name = component_config.get('name'),
    semanticVersion = version,
    platform = platform,
    changeDescription = changeDescription,
    data = yaml.dump(component_config)
  )
  return new_component

def create_components(ib, compent_list):
  for component in component_def:
    create_component(ib, platform, component_config)

def create_ib_client():
  return boto3.client('imagebuilder')

def lambda_handler(event, context):
  """Sample pure Lambda function

  Parameters
  ----------

  Returns
  ------
   resource_creation_status: dict
  """

  ib = create_ib_client()
  linux_component_yaml = read_component_yaml('components/linux_component.yaml')
  linux_component = create_component(ib, 'Linux', linux_component_yaml)
  windows_component_yaml = read_component_yaml('components/windows_component.yaml')
  windows_component = create_component(ib, 'Windows', windows_component_yaml)

  return {
    "statusCode": 200,
    "body": json.dumps({
      "components": [
        linux_component,
        windows_component
      ],
      # "location": ip.text.replace("\n", "")
    }),
  }
