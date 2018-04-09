import tensorflow as tf
import sys
from Quantize import QConv
from Quantize import QFullyConnect
from Quantize import QAvgPool


#slim = tf.contrib.slim
conv2d=tf.contrib.layers.conv2d
max_pool2d=tf.contrib.layers.max_pool2d
fully_connected=tf.contrib.layers.fully_connected
avg_pool2d=tf.contrib.layers.avg_pool2d

def generic_factory(layer_function, q_layer_function, 
                    intr_q_map=None, extr_q_map=None, weight_q_map=None):
    ''' Generic function for layer factories.
    Args:
        layer_function: Layer applied if no intrinsic quantization (usually slim-layers).
        q_layer_function: Layer applied if intrinsic quantization.
        intr_q_map: Dictionary containing mapping from layers to quantizers 
                    for intrinsic quantization.
        extr_q_map: Dictionary containing mapping from layers to quantizers 
                    for extrinsic quantization.
        weight_q_map: Dictionary containing mapping from layers to quantizers 
                    for weight quantization.
    Returns:
        A function which can be called like a layer
    '''
    def func(*args,**kwargs):
        layer_ID=tf.get_variable_scope().name + "/" + kwargs["scope"]
        is_quantized=False
        # Intrinsic quantization
        if intr_q_map is not None:
            # add intrinsic quantization, if in intr qmap.
            if ( any(layer in layer_ID for layer in intr_q_map.keys()) ):
                layer = next(layer for layer in intr_q_map.keys() if(
                        layer in layer_ID) )
                tf.logging.info('Quantizing (intr) layer %s'%layer_ID)
                kwargs['quantizer']=intr_q_map[layer]
                is_quantized=True

        # Weight quantization
        if weight_q_map is not None:
            # add weight quantization, if in weight qmap.
            if ( any(layer in layer_ID for layer in weight_q_map.keys()) ):
                layer = next(layer for layer in weight_q_map.keys() if(
                        layer in layer_ID) )
                tf.logging.info('Quantizing (weights) layer %s'%layer_ID)
                kwargs['weight_quantizer']=weight_q_map[layer]
                is_quantized=True
        
        if is_quantized:     
            net=q_layer_function(*args,**kwargs)
        else:
            net=layer_function(*args,**kwargs)

        # Extrinsic Quantization
        if extr_q_map is None:
            return net
        elif ( any(layer in layer_ID for layer in extr_q_map.keys()) ):
            layer = next(layer for layer in extr_q_map.keys() if(
                        layer in layer_ID) )
            tf.logging.info('Quantizing (extr) layer %s'%layer_ID)
            return extr_q_map[layer].quantize(net)
        else:
            return net
    return func


def conv2d_factory(intr_q_map=None, extr_q_map=None, weight_q_map=None):
    return generic_factory(conv2d, QConv.conv2d, 
                           intr_q_map=intr_q_map, extr_q_map=extr_q_map, 
                           weight_q_map=weight_q_map)    

def fully_connected_factory(intr_q_map=None, extr_q_map=None, weight_q_map=None):
    return generic_factory(fully_connected, QFullyConnect.fully_connected, 
                           intr_q_map=intr_q_map, extr_q_map=extr_q_map,
                           weight_q_map=weight_q_map)  


def max_pool2d_factory(intr_q_map=None, extr_q_map=None):
    # this layer has no intrinsic quantization.
    # apply extrinsic quantization in either case 
    _extr_q_map= dict(extr_q_map) if extr_q_map is not None else {}
    if intr_q_map is not None:
        _extr_q_map.update(intr_q_map)
    if _extr_q_map == {}:
        _extr_q_map=None
    return generic_factory(max_pool2d, slim.max_pool2d, 
                           intr_q_map=None, extr_q_map=_extr_q_map)  


def avg_pool2d_factory(intr_q_map=None, extr_q_map=None):
    return generic_factory(avg_pool2d, QAvgPool.avg_pool2d, 
                           intr_q_map=intr_q_map, extr_q_map=extr_q_map)  


