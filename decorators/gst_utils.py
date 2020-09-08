import logging as log

from utils import gst_utils as utils

import gi

gi.require_version('Gst', '1.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gst

def gst_element(type:str, config_func, name:str, app_config, pipeline : Gst.Pipeline):
    log.info(f'Creating Gst element {name} an instance of {type}')
    el = utils.create_element(type, name)
    log.info(f'Adding {name} to the Gst pipeline.')
    pipeline.add(el)
    log.info(f'Configuring element {name}')
    config_func(el, app_config)
    return el


def gst_element_factory(type : str, config_func):
    def create(name, app_config, pipeline):
        return gst_element(type, config_func, name, app_config, pipeline)
    return create



