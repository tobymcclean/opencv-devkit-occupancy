from adlinktech.datariver import IotValue, IotNvp, IotNvpSeq, IotByteSeq_from_buffer

class PyDetectionBoxData:
    def __init__(self, obj_id = 0, obj_label = '', class_id = 0, class_label = '', x1 = 0.0, y1 = 0.0, x2 = 0.0, y2 = 0.0, probability = 0.0, meta = ''):
        self.__obj_id = IotValue()
        self.__obj_label = IotValue()
        self.__class_id = IotValue()
        self.__class_label = IotValue()
        self.__x1 = IotValue()
        self.__y1 = IotValue()
        self.__x2 = IotValue()
        self.__y2 = IotValue()
        self.__probability = IotValue()
        self.__meta = IotValue()

        self.obj_id = obj_id
        self.obj_label = obj_label
        self.class_id = class_id
        self.class_label = class_label
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.probability = probability
        self.meta = meta

    @property
    def obj_id(self):
        return self.__obj_id.int32

    @obj_id.setter
    def obj_id(self, value):
        self.__obj_id.int32 = value

    @property
    def obj_label(self):
        return self.__obj_label.string

    @obj_label.setter
    def obj_label(self, value):
        self.__obj_label.string = value if value is not None else ''

    @property
    def class_id(self):
        return self.__class_id.int32

    @class_id.setter
    def class_id(self, value):
        try:
            self.__class_id.int32 = int(value)
        except TypeError:
            print(f'Classid type error {value}')
            self.__class_id.int32 = -1


    @property
    def class_label(self):
        return self.__class_label.string

    @class_label.setter
    def class_label(self, value):
        self.__class_label.string = value if value is not None else ''

    @property
    def x1(self):
        return self.__x1.float32

    @x1.setter
    def x1(self, value):
        self.__x1.float32 = value

    @property
    def y1(self):
        return self.__y1.float32

    @y1.setter
    def y1(self, value):
        self.__y1.float32 = value

    @property
    def x2(self):
        return self.__x2.float32

    @x2.setter
    def x2(self, value):
        self.__x2.float32 = value

    @property
    def y2(self):
        return self.__y2.float32

    @y2.setter
    def y2(self, value):
        self.__y2.float32 = value

    @property
    def probability(self):
        return self.__probability.float32

    @probability.setter
    def probability(self, value):
        self.__probability.float32 = value

    @property
    def meta(self):
        return self.__meta.string

    @meta.setter
    def meta(self, value):
        self.__meta.string = value if value is not None else ''

    @property
    def dr_data(self):
        data = IotNvpSeq()
        data.append(IotNvp('obj_id', self.__obj_id))
        data.append(IotNvp('obj_label', self.__obj_label))
        data.append(IotNvp('class_id', self.__class_id))
        data.append(IotNvp('class_label', self.__class_label))
        data.append(IotNvp('x1', self.__x1))
        data.append(IotNvp('y1', self.__y1))
        data.append(IotNvp('x2', self.__x2))
        data.append(IotNvp('y2', self.__y2))
        data.append(IotNvp('probability', self.__probability))
        data.append(IotNvp('meta', self.__meta))
        return data


class PyDepthDetectionBoxData(PyDetectionBoxData):
    def __init__(self, obj_id=0, obj_label='', class_id=0, class_label='', x1=0.0, y1=0.0, x2=0.0, y2=0.0,
                 probability=0.0, meta='', dist_x=0.0, dist_y=0.0, dist_z=0.0):
        super().__init__(obj_id, obj_label,class_id, class_label, x1, y1, x2, y2, probability, meta)
        self.__dist_x = IotValue()
        self.__dist_y = IotValue()
        self.__dist_z = IotValue()

        self.dist_x = dist_x
        self.dist_y = dist_y
        self.dist_z = dist_z


    @property
    def dist_x(self) -> float:
        return self.__dist_x.float64

    @dist_x.setter
    def dist_x(self, value: float) -> None:
        self.__dist_x.float64 = value

    @property
    def dist_y(self) -> float:
        return self.__dist_y.float64

    @dist_y.setter
    def dist_y(self, value: float) -> None:
        self.__dist_y.float64 = value

    @property
    def dist_z(self) -> float:
        return self.__dist_z.float64

    @dist_z.setter
    def dist_z(self, value: float) -> None:
        self.__dist_z.float64 = value

    @property
    def dr_data(self):
        data = super().dr_data
        data.append(IotNvp('dist_x', self.__dist_x))
        data.append(IotNvp('dist_y', self.__dist_y))
        data.append(IotNvp('dist_z', self.__dist_z))
        return data

class PyDetectionBox:

    def __init__(self, engine_id = '', stream_id = '', frame_id=0):
        self.__engine_id = IotValue()
        self.__stream_id = IotValue()
        self.__frame_id = IotValue()
        self.__data = IotNvpSeq()

        self.engine_id = engine_id
        self.stream_id = stream_id
        self.frame_id = frame_id

    @property
    def engine_id(self):
        return self.__engine_id.string

    @engine_id.setter
    def engine_id(self, value):
        self.__engine_id.string = value

    @property
    def stream_id(self):
        return self.__stream_id.string

    @stream_id.setter
    def stream_id(self, value):
        self.__stream_id.string = value

    @property
    def frame_id(self):
        return self.__frame_id.uint32

    @frame_id.setter
    def frame_id(self, value):
        self.__frame_id.uint32 = value


    def add_data(self, value: PyDetectionBoxData):
        seq = value.dr_data
        value = IotValue()
        value.nvp_seq = seq
        it = IotNvp()
        it.value = value
        self.__data.push_back(it)


    def add_box(self,
                obj_id, obj_label, class_id, class_label, x1, y1, x2, y2, probability, meta):
        self.add_data(PyDetectionBoxData(obj_id, obj_label, class_id, class_label, x1, y1, x2, y2, probability, meta))

    @property
    def dr_data(self) -> IotNvpSeq:
        data = IotNvpSeq()
        data.append(IotNvp('engine_id', self.__engine_id))
        data.append(IotNvp('stream_id', self.__stream_id))
        data.append(IotNvp('frame_id', self.__frame_id))
        dbox_value = IotValue()
        dbox_value.nvp_seq = self.__data
        data.append(IotNvp('data', dbox_value))
        return data


class PyDepthDetectionBox(PyDetectionBox):

    def add_box(self,
                obj_id, obj_label, class_id, class_label, x1, y1, x2, y2, probability, meta,
                dist_x, dist_y, dist_z):
        self.add_data(PyDepthDetectionBoxData(obj_id, obj_label, class_id, class_label, x1, y1, x2, y2,
                                              probability, meta, dist_x, dist_y, dist_z))

