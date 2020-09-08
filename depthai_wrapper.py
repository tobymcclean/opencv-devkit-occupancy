import logging as log
import uuid
from pathlib import Path
from typing import List

import cv2

import consts.resource_paths
import depthai

import depthai
from imutils.video import FPS

from config import DepthAIConfig

from datacls import PyDepthDetectionBox, PyDepthDetectionBoxData

class DepthAI:
    @staticmethod
    def create_pipeline(config):
        if not depthai.init_device(consts.resource_paths.device_cmd_fpath):
            log.error('Failed to initialize device raising a RuntimeError')
            raise RuntimeError('Error initializing device. Try to reset it.')
        log.info('Creating DepthAI pipeline...')

        pipeline = depthai.create_pipeline(config)
        if pipeline is None:
            log.error('Failed to create pipeline raising a RuntimeError.')
            raise RuntimeError('Pipeline was not created.')

        log.info('Pipeline created successfully.')
        return pipeline

    def __init__(self, config:DepthAIConfig, stream_id : str,
                 engine_id : str, model_label: str,
                 threshold : float = 0.5):
        self.__config = config
        self.__pipeline = DepthAI.create_pipeline(config.config)
        self.__network_results = []
        self.__threshold = threshold
        self.__model_label = model_label
        self.__labels = config.labels
        log.info(f'Labels: {self.__labels}')
        log.info(f'Labels length: {len(self.__labels)}')
        self.__engine_id = engine_id
        self.__stream_id = stream_id


    def capture(self):
        frame_num = 0
        while True:
            nnet_packets, data_packets = self.__pipeline.get_available_nnet_and_data_packets()
            for _, nnet_packet in enumerate(nnet_packets):
                self.__network_results = []
                for _, e in enumerate(nnet_packet.entries()):
                    if e[0]['id'] == -1.0 or e[0]['confidence'] < self.__threshold:
                        break

                    self.__network_results.append(e[0])
            for packet in data_packets:
                if packet.stream_name == 'previewout':
                    boxes = PyDepthDetectionBox()
                    boxes.stream_id = 'foo'
                    boxes.engine_id = 'engine'
                    boxes.frame_id = frame_num
                    data = packet.getData()
                    if data is None:
                        continue
                    data0 = data[0,:,:]
                    data1 = data[1, :, :]
                    data2 = data[2, :, :]
                    frame = cv2.merge([data0, data1, data2])

                    img_h = frame.shape[0]
                    img_w = frame.shape[1]

                    for e in self.__network_results:
                        try:
                            box = PyDepthDetectionBoxData()
                            box.x1 = float(e['left'])
                            box.y1 = float(e['top'])
                            box.x2 = float(e['right'])
                            box.y2 = float(e['bottom'])
                            box.class_id = e['label']
                            if box.class_id <= len(self.__labels):
                                box.class_label = self.__labels[box.class_id]
                            print(e['confidence'])
                            box.probability = e['confidence']
                            box.dist_x = e['distance_x']
                            box.dist_y = e['distance_y']
                            box.dist_z = e['distance_z']
                            boxes.add_data(box)
                            # boxes.append({
                            #     'id': uuid.uuid4(),
                            #     'detector': self.__model_label,
                            #     'label': e['label'],
                            #     'conf': e['confidence'],
                            #     'left': int(e['left'] * img_w),
                            #     'top': int(e['top'] * img_h),
                            #     'right': int(e['right'] * img_w),
                            #     'bottom': int(e['bottom'] * img_h),
                            #     'distance_x': e['distance_x'],
                            #     'distance_y': e['distance_y'],
                            #     'distance_z': e['distance_z'],
                            # })
                        except :
                            continue
                    yield frame, boxes
                    frame_num += 1


    def __del__(self):
        del self.__pipeline
        depthai.deinit_device()