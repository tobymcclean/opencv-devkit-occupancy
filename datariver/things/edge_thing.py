from os import path

from datariver.utils import get_river_config_uri
from adlinktech.datariver import DataRiver, JSonTagGroupRegistry, JSonThingClassRegistry, JSonThingProperties

import datariver.utils as eu


class EdgeThing(object):
    '''
        A wrapper around a Data River Thing that if the common project structure
        is followed then alot of the boiler plate code for an application is removed.

        For example by default it assumes that you code is layout in the following way
        - root of application
          -- <app implementation>
          -- config
            -- <thing config file>.json
          -- definitions
            -- TagGroup
              -- <name space>
                -- <tag group definition json file>
            -- ThingClass
              -- <name space>
                -- <thing class definition json file>

        You can then simply specify the config file, Tag Group files (prefixed with namespace) and
        Thing Class files (prefixed with namespace) to create a Thing. All of the defaults can be
        overriden if you decide to follow a different project structure.
    '''

    def __init__(self,
                 config_uri: str = '',
                 properties_str: str = '',
                 tag_group_dir: str = './definitions/TagGroup',
                 thing_class_dir: str = './definitions/ThingClass',
                 tag_groups: tuple = tuple(),
                 thing_cls: tuple = tuple()):
        assert len(properties_str) > 0, f"Config properties must be defined"
        for f in map(lambda tg: path.join(tag_group_dir, f'{tg}.json'), tag_groups):
            assert path.exists(f), f"Can't find Tag Group: {f}"
        for f in map(lambda tc: path.join(thing_class_dir, f'{tc}.json'), thing_cls):
            assert path.exists(f), f"Can't find Thing Class: {f}"

        self.__config_uri = config_uri if config_uri and len(config_uri) > 0 else get_river_config_uri()
        self.__properties_str = properties_str
        self.__tag_group_dir = tag_group_dir
        self.__thing_class_dir = thing_class_dir
        self.__tags_groups = tag_groups
        self.__thing_cls = thing_cls
        self.__dr = DataRiver.get_instance(self.__config_uri)
        self.__thing = self.__create_thing()
        self.__terminate = False

    def __exit__(self):
        self.__terminate = True
        if self.__dr is not None:
            self.__dr.close()

    @property
    def thing(self):
        '''Access to the underlying Data River thing.'''
        return self.__thing

    @property
    def dr(self):
        '''Access to the underlying Data River object'''
        return self.__dr

    @property
    def terminate(self):
        '''Whether the Thing should terminate'''
        return self.__terminate

    def __create_thing(self):
        eu.register_tag_groups(self.__dr, self.__tag_group_dir, self.__tags_groups)
        eu.register_thing_classes(self.__dr, self.__thing_class_dir, self.__thing_cls)

        return eu.create_thing(self.__dr, self.__properties_str)