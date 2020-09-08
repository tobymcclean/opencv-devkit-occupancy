import logging as log
import sys
import json

from datariver.things.edge_thing import EdgeThing
from datariver.utils import write_tag
from depthai_helpers.cli_utils import parse_args
from depthai_wrapper import DepthAI
from config import DepthAIConfig

PROPERTIES_FILE = './etc/config/properties.json'

log.basicConfig(format='[ %(levelname)s ] %(message)s',
                level=log.INFO, stream=sys.stdout)

def init_edge_thing():
    with open(PROPERTIES_FILE) as f:
        properties_str = json.load(f)
        properties_str = json.dumps(properties_str) if properties_str is not None else None

    return EdgeThing(properties_str=properties_str,
                     tag_groups=['com.vision.data/DepthDetectionBox'],
                     thing_cls=['com.vision.data/DepthAI'])


class Main:

    def __init__(self, config : DepthAIConfig, model_label : str):
        self.__depthai = DepthAI(config, 'mcclean.home.oakd-1', 'oakd-1', model_label, )
        self.__edge_thing = init_edge_thing()


    def __publish_frame(self, frame, boxes):
        write_tag(self.__edge_thing.thing, 'DetectionBoxData', boxes.dr_data)


    def run(self):
        try:
            log.info('Setup complete, processing frames')
            for frame, results in self.__depthai.capture():
                self.__publish_frame(frame, results)
        finally:
            del self.__depthai


if __name__ == '__main__':
    try:
        args = vars(parse_args())
    except:
        log.error('Problem parsing the command line arguments')
    config = DepthAIConfig(args)
    main = Main(config, 'people')
    main.run()

