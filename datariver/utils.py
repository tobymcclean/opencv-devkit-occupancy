import os
import logging
import signal

from typing import List, Any

from decorators.contracts import preconditions

from adlinktech.datariver import DataRiver, JSonTagGroupRegistry, JSonThingClassRegistry, JSonThingProperties
from adlinktech.datariver import as_nvp_seq, IotNvpSeq

DATA_RIVER_CONFIG_ENV_VAR = 'ADLINK_DATARIVER_URI'

def get_abs_file_uri(filepath:str) -> str:
    dirpath = os.path.dirname('')
    return f'file://{str(os.path.join(dirpath, filepath))}'


def iot_safe_copy(obj):
    '''
    Makes a safe copy of an IotNvpSeq wrapping object. IotNvpSeq objects returned by notify_data_available
    become invalid beyond the scope of that function. If used, a segmentation fault will result. This method
    duplicates the underlying IotNvpSeq
    '''
    nvp_seq = as_nvp_seq(obj)
    cls = type(obj)
    copy = cls()
    for nvp in nvp_seq:
        setattr(copy, nvp.name, getattr(obj, nvp.name))

    return copy


def get_river_config_uri() -> str:
    '''
    Get the Data River config URI from the Environment. The config should available in the ADLINK_DATARIVER_URI
    environment variable.

    If the environment variable is not set then the default configuration provided with the Edge SDK will be used. The
    default configuration can be found at $EDGE_SDK_HOME/etc/config/default_datariver_config_v1.2.xml.

    :return: The URI for the Data River configuration to be used in the application.
    '''
    river_conf_env = os.getenv(DATA_RIVER_CONFIG_ENV_VAR)
    if river_conf_env is None:
        river_conf_env = os.environ[DATA_RIVER_CONFIG_ENV_VAR] = \
            'file://{}/etc/config/default_datariver_config_v1.2.xml'.format(os.environ['EDGE_SDK_HOME'])
        logging.info(f'Environment variable {DATA_RIVER_CONFIG_ENV_VAR} not set. Defaulting to: {str(river_conf_env)}')

    return river_conf_env


def register_tag_groups(dr : DataRiver, tag_group_dir : str, tag_groups : List[str]):
    '''
    For each of the Tag Groups listed in tag_groups and whose definition is in tag_groups_dir register them with
    the provided instance of the Data River; dr.

    The tag_groups list should be the name of the file without the .json extension
    '''
    tgr = JSonTagGroupRegistry()

    for tg in tag_groups:
        logging.info(f'Loading Tag Group: {tg}.json from {tag_group_dir}')
        tgr.register_tag_groups_from_uri(get_abs_file_uri(str(os.path.join(tag_group_dir, f'{tg}.json'))))

    dr.add_tag_group_registry(tgr)


def register_thing_classes(dr : DataRiver, thing_class_dir : str, thing_classes : List[str]):
    '''
    For each of the Thing Classes listed in thing_classes and whose definition is in thing_class_dir register them
    with the provided instance of the Data River; dr.

    The thing_classes list shoudl be the name of the file without the .json extension
    '''
    tcr = JSonThingClassRegistry()

    for tc in thing_classes:
        logging.info(f'Loading Thing Class: {tc}.json from {thing_class_dir}')
        tcr.register_thing_classes_from_uri(get_abs_file_uri(str(os.path.join(thing_class_dir, f'{tc}.json'))))

    dr.add_thing_class_registry(tcr)


def create_thing(dr : DataRiver, properties_str: str):
    '''
    Given a string for a Thing, instantiate it in the provided DataRiver and return it.
    '''
    tp = JSonThingProperties()
    tp.read_properties_from_string(properties_str)

    return dr.create_thing(tp)


def write_tag(thing : Any, out : str, data : IotNvpSeq, flow : str = None):
    '''
    Write the provided data to the output; out; of the provided Thing; thing.
    '''
    if flow is None:
        thing.write(out, data)
    else:
        thing.write(out, flow, data)


class SIGTERMHandler:

    def __init__(self, exit_handler):
        self.exit_handler = exit_handler
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)


    def exit_gracefully(self, signum, frame):
        self.exit_handler(signum, frame)

@preconditions(lambda id : id is not None and len(id) > 0,
               lambda contextId : contextId is not None and len(contextId) > 0)
def gen_properties(id:str, contextId:str, description:str = '')->str:
    import json
    data = {}
    data['id'] = id
    data['classId'] = 'VisionPipeline:com.vision.data:v1.0'
    data['contextId'] = contextId
    data['description'] = description if description is not None else ''
    return json.dumps(data)
