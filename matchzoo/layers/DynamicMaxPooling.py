from keras.layers import Input
from keras import backend as K
from keras.engine.topology import Layer
import numpy as np

class DynamicMaxPooling(Layer):

    def __init__(self, psize1, psize2, **kwargs):
        self.psize1 = psize1
        self.psize2 = psize2
        super(DynamicMaxPooling, self).__init__(**kwargs)

    def build(self, input_shape):
        #self.dpool_index = Input(name='dpool_index', shape=[input_shape[1], input_shape[2], 3], dtype='int32')
        input_shape_one = input_shape[0]
        self.msize1 = input_shape_one[1]
        self.msize2 = input_shape_one[2]
        super(DynamicMaxPooling, self).build(input_shape)  # Be sure to call this somewhere!

    def call(self, data):
        x, self.dpool_index = data
        x_expand = K.tf.gather_nd(x, self.dpool_index)
        stride1 = self.msize1 / self.psize1
        stride2 = self.msize2 / self.psize2
        
        suggestion1 = self.msize1 / stride1
        suggestion2 = self.msize2 / stride2

        if suggestion1!=self.psize1 or suggestion2!=self.psize2:
            print("DynamicMaxPooling Layer can not generate (%s x %s) output feature map,"
                "please use (%s x %s instead.)" % (self.psize1, self.psize2, suggestion1, suggestion2))
            exit()

        x_pool = K.tf.nn.max_pool(x_expand, 
                    [1, self.msize1 / self.psize1, self.msize2 / self.psize2, 1], 
                    [1, self.msize1 / self.psize1, self.msize2 / self.psize2, 1], 
                    "VALID")
        return x_pool

    def compute_output_shape(self, input_shape):
        input_shape_one = input_shape[0]
        return (None, self.psize1, self.psize2, input_shape_one[3])

    @staticmethod
    def dynamic_pooling_index(len1, len2, max_len1, max_len2, compress_ratio1 = 1, compress_ratio2 = 1):
        def dpool_index_(batch_idx, len1_one, len2_one, max_len1, max_len2):
            stride1 = 1.0 * max_len1 / len1_one
            stride2 = 1.0 * max_len2 / len2_one
            idx1_one = [int(i/stride1) for i in range(max_len1)]
            idx2_one = [int(i/stride2) for i in range(max_len2)]
            mesh1, mesh2 = np.meshgrid(idx1_one, idx2_one)
            index_one = np.transpose(np.stack([np.ones(mesh1.shape) * batch_idx, mesh1, mesh2]), (2,1,0))
            return index_one
        index = []
        dpool_bias1 = dpool_bias2 = 0
        if max_len1 % compress_ratio1 != 0:
            dpool_bias1 = 1
        if max_len2 % compress_ratio2 != 0:
            dpool_bias2 = 1
        cur_max_len1 = max_len1//compress_ratio1+dpool_bias1
        cur_max_len2 = max_len2//compress_ratio2+dpool_bias2
        for i in range(len(len1)):
            index.append(dpool_index_(i, len1[i]//compress_ratio1, len2[i]//compress_ratio2, cur_max_len1, cur_max_len2))
        return np.array(index)
