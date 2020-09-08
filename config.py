import logging as log
import json
from pathlib import Path

import consts.resource_paths
from depthai import get_nn_to_depth_bbox_mapping
from depthai_helpers.cli_utils import PrintColors
from depthai_helpers.mobilenet_ssd_handler import decode_mobilenet_ssd, show_mobilenet_ssd
from depthai_helpers import utils

from depthai_utils import get_model_files

class DepthAIConfig:
    def __init__(self, args):
        self.cnn_camera = args['cnn_camera']
        self.shaves = args['shaves']
        self.cmx_slices = args['cmx_slices']
        self.NN_engines = args['NN_engines']
        self.config = None
        self.full_fov_nn = args['full_fov_nn']
        self.swap_lr = args['swap_lr']
        self.field_of_view = args['field_of_view']
        self.rgb_field_of_view = args['rgb_field_of_view']
        self.baseline = args['baseline']
        self.rgb_baseline = args['rgb_baseline']
        self.store_eeprom = args['store_eeprom']
        self.clear_eeprom = args['clear_eeprom']
        self.override_eeprom = args['override_eeprom']
        self.rgb_resolution = args['rgb_resolution']
        self.rgb_fps = args['rgb_fps']
        self.mono_resolution = args['mono_resolution']
        self.mono_fps = args['mono_fps']
        self.board = args['board']
        self.config_overwrite = args['config_overwrite']
        self.compile_model = self.shaves is not None and self.cmx_slices is not None and self.NN_engines
        self.stream_list = args['streams']
        self.force_usb2 = args['force_usb2']
        self.dev_debug = args['dev_debug']
        self.disable_depth = args['disable_depth']
        self.cnn_model = args['cnn_model']
        self.cnn_model2 = args['cnn_model2']
        self.video = args['video']
        self.nn2_depth = get_nn_to_depth_bbox_mapping()
        self.__configure()
        self.__compile_model()
        self.__load_config()
        self.__config_recording_file()
        self.stream_names = [stream if isinstance(stream, str) else stream['name'] for stream in self.stream_list]
        self.disparity_confidence_threshold = args['disparity_confidence_threshold']

    @property
    def record_video(self) -> bool:
        return self.video is not None

    @property
    def enable_object_tracker(self):
        return 'object_tracker' in self.stream_names

    def add_video_stream(self) -> None:
        if self.config['streams'].count('video') == 0:
            self.config['streams'].append('video')


    def remove_video_stream(self) -> None:
        if self.config['streams'].count('video') > 0:
            self.config['streams'].remove('video')

    def __configure(self):
        if self.config_overwrite:
            self.config_overwrite = json.loads(self.config_overwrite)

        if self.force_usb2:
            log.info(f'{PrintColors.WARNING.value}FORCE USB2 MODE{PrintColors.ENDC.value}')
            self.cmd_file = consts.resource_paths.device_usb2_cmd_fpath
        else:
            self.cmd_file = consts.resource_paths.device_cmd_fpath
        if self.dev_debug:
            self.cmd_file = ''
            log.info('depth ai will not load cmd file into device')
        self.calc_dist_to_bb = True
        if self.disable_depth:
            self.calc_dist_to_bb = False
        self.decode_nn = decode_mobilenet_ssd
        self.show_nn = show_mobilenet_ssd
        if self.cnn_model:
            self.blob_file, self.blob_file_config = get_model_files(self.calc_dist_to_bb, self.cnn_model)
        if not Path(self.blob_file).exists():
            log.error(f'{PrintColors.WARNING.value}NN2 blob not found in {self.blob_file}{PrintColors.ENDC.value}')
            raise FileNotFoundError
        if not Path(self.blob_file_config).exists():
            log.error(f'{PrintColors.WARNING.value}NN2 json not found in {self.blob_file_config}{PrintColors.ENDC.value}')
            raise FileNotFoundError
        self.blob_file2 = ""
        self.blob_file_config2 = ""
        self.cnn_model2 = None
        if self.cnn_model2:
            log.info(f"Using CNN2: {self.cnn_model2}")
            self.blob_file2, self.blob_file_config2 = get_model_files(False, self.cnn_model2)
            if not Path(self.blob_file2).exists():
                log.error(f'{PrintColors.WARNING.value}NN2 blob not found in {self.blob_file2}{PrintColors.ENDC.value}')
                raise FileNotFoundError
            if not Path(self.blob_file_config2).exists():
                log.error(
                    f'{PrintColors.WARNING.value}NN2 json not found in {self. blob_file_config2}{PrintColors.ENDC.value}')
                raise FileNotFoundError
        with open(self.blob_file_config) as f:
            data = json.load(f)
        try:
            self.labels = data['mappings']['labels']
        except:
            log.warning(f'{PrintColors.WARNING.value}Labels not found in json!{PrintColors.ENDC.value}')
            self.labels = None

        if self.cnn_camera == 'left_right' and self.NN_engines is None:
            self.NN_engines = 2
            self.shaves = 6 if self.shaves is None else self.shaves - self.shaves % 2
            self.cmx_slices = 6 if self.cmx_slices is None else self.cmx_slices - self.cmx_slices % 2
            self.compile_model = True
            log.info('Running NN on both cams requires 2 NN engines')
        self.default_blob = True
        if self.compile_model:
            self.default_blob = False


    def __load_config(self):
        self.config = self.__get_default_config()
        res, board_config = self.__get_board_config()
        if not res:
            log.error('There was a problem loading the board config.')
            raise Exception('There was a problem loading the board config.')
        self.config = utils.merge(board_config, self.config)
        if self.config_overwrite is not None:
            self.config = utils.merge(self.config_overwrite, self.config)
            log.info(f'Merged pipeline config with overwrite: {self.config}')


    def __get_default_config(self):
        # Do not modify the default values in the config Dict below directly. Instead, use the `-co` argument when running this script.
        return {
            # Possible streams:
            # ['left', 'right','previewout', 'metaout', 'depth_raw', 'disparity', 'disparity_color']
            # If "left" is used, it must be in the first position.
            # To test depth use:
            # 'streams': [{'name': 'depth_raw', "max_fps": 12.0}, {'name': 'previewout', "max_fps": 12.0}, ],
            'streams': self.stream_list,
            'depth':
                {
                    'calibration_file': consts.resource_paths.calib_fpath,
                    'padding_factor': 0.3,
                    'depth_limit_m': 10.0,  # In meters, for filtering purpose during x,y,z calc
                    'confidence_threshold': 0.5,
                    # Depth is calculated for bounding boxes with confidence higher than this number
                },
            'ai':
                {
                    'blob_file': self.blob_file,
                    'blob_file_config': self.blob_file_config,
                    'blob_file2': self.blob_file2,
                    'blob_file_config2': self.blob_file_config2,
                    'calc_dist_to_bb': self.calc_dist_to_bb,
                    'keep_aspect_ratio': not self.full_fov_nn,
                    'camera_input': self.cnn_camera,
                    'shaves': self.shaves,
                    'cmx_slices': self.cmx_slices,
                    'NN_engines': self.NN_engines,
                },
            # object tracker
            'ot':
                {
                    'max_tracklets': 20,  # maximum 20 is supported
                    'confidence_threshold': 0.5,  # object is tracked only for detections over this threshold
                },
            'board_config':
                {
                    'swap_left_and_right_cameras': self.swap_lr,
                    # True for 1097 (RPi Compute) and 1098OBC (USB w/onboard cameras)
                    'left_fov_deg': self.field_of_view,  # Same on 1097 and 1098OBC
                    'rgb_fov_deg': self.rgb_field_of_view,
                    'left_to_right_distance_cm': self.baseline,  # Distance between stereo cameras
                    'left_to_rgb_distance_cm': self.rgb_baseline,  # Currently unused
                    'store_to_eeprom': self.store_eeprom,
                    'clear_eeprom': self.clear_eeprom,
                    'override_eeprom': self.override_eeprom,
                },
            'camera':
                {
                    'rgb':
                        {
                            # 3840x2160, 1920x1080
                            # only UHD/1080p/30 fps supported for now
                            'resolution_h': self.rgb_resolution,
                            'fps': self.rgb_fps,
                        },
                    'mono':
                        {
                            # 1280x720, 1280x800, 640x400 (binning enabled)
                            'resolution_h': self.mono_resolution,
                            'fps': self.mono_fps,
                        },
                },
            # 'video_config':
            # {
            #    'rateCtrlMode': 'cbr',
            #    'profile': 'h265_main', # Options: 'h264_baseline' / 'h264_main' / 'h264_high' / 'h265_main'
            #    'bitrate': 8000000, # When using CBR
            #    'maxBitrate': 8000000, # When using CBR
            #    'keyframeFrequency': 30,
            #    'numBFrames': 0,
            #    'quality': 80 # (0 - 100%) When using VBR
            # }
        }


    def __get_board_config(self) -> (bool, dict):
        board_config = {}
        if self.board:
            board_path = Path(self.board)
            if not board_path.exists():
                board_path = Path(consts.resource_paths.boards_dir_path) / Path(self.board.upper()).with_suffix('.json')
                if not board_path.exists():
                    log.error(f'Board config not found: {board_path}')
                    return False, board_config
            with open(board_path) as fp:
                board_config = json.load(fp)

        return True, board_config


    def __compile_model(self) -> None:
        if self.compile_model:
            self.default_blob = False
            if self.NN_engines == 2:
                if self.shaves % 2 == 1 or self.cmx_slices % 2 == 1:
                    log.error(
                        f'{PrintColors.RED.value}shaves and cmx_slices must be an even number when using 2 neural compute engines{PrintColors.ENDC.value}')
                    raise ValueError(
                        'DepthAIConfig: shaves and cmx_slices must be an even number when using 2 neural compute engines')
                shave_nr_opt = int(self.shaves / 2)
                cmx_slices_opt = int(self.cmx_slices / 2)
            else:
                shave_nr_opt = int(self.shaves)
                cmx_slices_opt = int(self.cmx_slices)
            outblob_file = f'b{self.blob_file}.sh{str(self.shaves)}cmx{str(self.cmx_slices)}NCE{str(self.NN_engines)}'
            if not Path(outblob_file).exists():
                log.info(
                    f'{PrintColors.RED.value}Compiling model for {str(self.shaves)} shaves, {str(self.cmx_slices)} cmx_slices and {str(config.NN_engines)} NN_engines{PrintColors.ENDC.value}')
                ret = depthai.download_blob((self.cnn_model, shave_nr_opt, cmx_slices_opt, self.NN_engines, outblob_file))
                log.info(f'Blob download result {str(ret)}')
                if (ret != 0):
                    log.warning(
                        f'{PrintColors.WARNING.value}Model compile failed. Failing back to default.{PrintColors.ENDC.value}')
                    self.default_blob = True
                else:
                    self.blob_file = outblob_file
            else:
                log.info(
                    f'{PrintColors.GREEN.value}Compiled mode found: compiled for {str(self.shaves)} shaves, {str(self.cmx_slices)} and {str(self.NN_engines)} NN_engines{PrintColors.ENDC.value}')
                self.blob_file = outblob_file

            if self.cnn_model2:
                outblob_file = f'b{self.blob_file2}.sh{str(self.shaves)}cmx{str(self.cmx_slices)}NCE{str(self.NN_engines)}'
                if (not Path(outblob_file).exists()):
                    log.info(
                        f'{PrintColors.RED.value}Compiling model2 for {str(self.shaves)} shaves, {str(self.cmx_slices)} cmx_slices and {str(self.NN_engines)} NN_engines{PrintColors.ENDC.value}')
                    ret = depthai.download_blob((self.cnn_model2, shave_nr_opt, cmx_slices_opt, self.NN_engines, outblob_file))
                    log.info(f'Blob download result {str(ret)}')
                    if (ret != 0):
                        log.warning(
                            f'{PrintColors.WARNING.value}Model2 compile failed. Failing back to default.{PrintColors.ENDC.value}')
                        self.default_blob = True
                    else:
                       self.blob_file2 = outblob_file
        if self.default_blob:
            self.shaves = 7
            self.cmx_slices = 7
            self.NN_engines = 1

    def __config_recording_file(self):
        # Append video stream if video recording was requested and stream
        # is not already specified
        self.video_file = None
        if self.record_video:
            # open video file
            try:
                video_file = open(self.video, 'wb')
                self.add_video_stream()
            except IOError:
                log.error("Could open video file for writing. Disabled video output stream.")
                self.remove_video_stream()
