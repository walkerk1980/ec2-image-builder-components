import json
import yaml
import boto3
from crhelper import CfnResource
import logging
import cfnresponse

logger = logging.getLogger(__name__)
# Initialise the custom_resource_helper, all inputs are optional, this example shows the defaults
custom_resource_helper = CfnResource(json_logging=False, log_level='WARN', boto_level='WARN', sleep_on_delete=30)

try:
    ## Init code goes here
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
    if component_config.get('version'):
      version = component_config.get('version')
    changeDescription = component_config.get('changeDescription')
    if not changeDescription:
      changeDescription = ' '
    new_component = ib.create_component(
      name = component_config.get('name'),
      semanticVersion = version,
      platform = platform,
      changeDescription = changeDescription,
      data = yaml.dump(component_config)
    )
    return new_component

  def update_component(ib, platform, component_config):
    existing_component = get_existing_component(ib, platform, component_config)
    return create_component(ib, platform, component_config)

  def create_components(ib, compent_list):
    for component in component_def:
      create_component(ib, platform, component_config)

  def create_ib_client():
    return boto3.client('imagebuilder')

except Exception as e:
    custom_resource_helper.init_failure(e)

@custom_resource_helper.create
def create(event, context):
    logger.info("Got Create")
    if not event.get('ResourceProperties').get('Platform') and not event.get('ResourceProperties').get('Version'):
      raise ValueError("Component must include the properties Platform and Version")
    ib = create_ib_client()
    platform = event.get('ResourceProperties').get('Platform')
    version = event.get('ResourceProperties').get('Version')
    component_yaml = read_component_yaml('components/{0}_component.yaml'.format(platform.lower()))
    if version:
      component_yaml.update({"version": version})
    component = create_component(ib, platform, component_yaml)
    custom_resource_helper.Data.update({"component": component})
    return component.get('componentBuildVersionArn')

@custom_resource_helper.update
def update(event, context):
    logger.info("Got Update")
    # If the update resulted in a new resource being created, return an id for the new resource. 
    # CloudFormation will send a delete event with the old id when stack update completes
    if not event.get('ResourceProperties').get('Platform') and not event.get('ResourceProperties').get('Version'):
      raise ValueError("Component must include the properties Platform and Version")
    try:
      ib = create_ib_client()
      platform = event.get('ResourceProperties').get('Platform')
      version = event.get('ResourceProperties').get('Version')
      component_yaml = read_component_yaml('components/{0}_component.yaml'.format(platform.lower()))
      if version:
        component_yaml.update({"version": version})
      component_build_version_arn = event.get('PhysicalResourceId')
      ib.delete_component(
          componentBuildVersionArn=component_build_version_arn
      )
      component = update_component(ib, platform, component_yaml)
      custom_resource_helper.Data.update({"component": component})
    except ib.exceptions.ResourceNotFoundException as e:
      print(e)
    return component.get('componentBuildVersionArn')

@custom_resource_helper.delete
def delete(event, context):
    logger.info("Got Delete")
    # Delete never returns anything. Should not fail if the underlying resources are already deleted.
    # Desired state.
    try:
      ib = create_ib_client()
      component_build_version_arn = event.get('PhysicalResourceId')
      ib.delete_component(
        componentBuildVersionArn=component_build_version_arn
      )
    except ib.exceptions.ResourceNotFoundException as e:
      print(e)

def lambda_handler(event, context):
  custom_resource_helper(event, context)

