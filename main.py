import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'
    
    # load the graph from the files
    tf.saved_model.loader.load(sess,[vgg_tag],vgg_path)
    # name it as graph
    graph = tf.get_default_graph()
    # grab each layer as its name
    image_input = graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob = graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3_out = graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4_out = graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7_out = graph.get_tensor_by_name(vgg_layer7_out_tensor_name)

    return image_input, keep_prob, layer3_out, layer4_out, layer7_out

tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    # here is we implement the FCN
    # see page 6 of research paper
    # take input which is final layer of vgg 7 and upsample it by 2
    # before that, there is encoder part which is 1x1 convulutional
    # start with create 1 x 1 convu of 1 layer
    # vgg 7 is furthest
    # use regularizer to penalise if weight get too large and get overfitting
    # num_classes is no of feature
    # kernel is 1 since its 1 x 1 convulutional

    # resample vgg_layer7_out by 1x1 Convolution: To go from ?x5x18x4096 to ?x5x18x2
    conv_vgg_7 = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, padding ='same',
     kernel_initializer=tf.truncated_normal_initializer(stddev=0.01))
    # resample vgg_layer4_out out by 1x1 Convolution: To go from ?x10x36x512 to ?x10x36x2
    conv_vgg_4 = tf.layers.conv2d(vgg_layer4_out, num_classes, 1, padding ='same',
     kernel_initializer=tf.truncated_normal_initializer(stddev=0.01))
    # resample vgg_layer3_out out by 1x1 Convolution: To go from ?x20x72x256 to ?x20x72x2
    conv_vgg_3 = tf.layers.conv2d(vgg_layer3_out, num_classes, 1, padding ='same',
     kernel_initializer=tf.truncated_normal_initializer(stddev=0.01))


    # now do deconvulutional layer and upsample it to original size
    # stride value is the one that upsamples it
    # below upsample it by 2

    # upsample vgg_layer7_out_resampled: by factor of 2 in order to go from ?x5x18x2 to ?x10x36x2
    output_1 = tf.layers.conv2d_transpose(conv_vgg_7, num_classes, 4,2,padding = 'same',
     kernel_initializer=tf.truncated_normal_initializer(stddev=0.01))
 
    # gives out the dimension below
    # tf.Print(output, [tf.shape(output)])
    combined_layer1 = tf.add(output_1, conv_vgg_4)

    # fcn_layer2: upsample combined_layer1 by factor of 2 in order to go from ?x10x36x2 to ?x20x72x2
    output_2 = tf.layers.conv2d_transpose(combined_layer1, num_classes, 4,2,padding = 'same',
     kernel_initializer=tf.truncated_normal_initializer(stddev=0.01))

    combined_layer2 = tf.add(output_2, conv_vgg_3)
    # upsample combined_layer2 by factor of 8 in order to go from ?x20x72x2 to ?x160x576x2
    final_output = tf.layers.conv2d_transpose(combined_layer2, num_classes, 16,8,padding = 'same',
     kernel_initializer=tf.truncated_normal_initializer(stddev=0.01))
    
    # now upsample by 2, by 2 then 8
    # do regulairzer for every layer and right padding
    # final output is same size as input

    return final_output
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function

    # resize of logits from 4d to 2d
    # width is how many pixels
    # softmax corss entorup with logits
    # do adam optimizer

    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    class_labels = tf.reshape(correct_label, (-1, num_classes))
    cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits = logits, labels = class_labels ))
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate, epsilon=0.1).minimize(cost) 
    
    return logits, optimizer, cost
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    idx = 0
    learn_rate = 1e-4

    # see the helper get batches 
    for epoch_i in range(epochs):
        for image,label in get_batches_fn(batch_size):
            _, loss = sess.run([train_op, cross_entropy_loss], \
                feed_dict = {input_image: image,
                            correct_label: label,
                            keep_prob: .50, learning_rate: learn_rate})
            # Show every <show_every_n_batches> batches
            if idx % 20 == 0:
                print("loss: {}".format(loss))
            idx += 1

tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    # create template for doing learning rate, float value, 
    # say no of epochs, batch size

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        # put a tf placeholder
        # placeholder tensors
        correct_label = tf.placeholder(tf.float32, [None, image_shape[0], image_shape[1], num_classes])
        learning_rate = tf.placeholder(tf.float32)
        keep_prob = tf.placeholder(tf.float32)


        input_image, keep_prob, layer3_out, layer4_out, layer7_out = load_vgg(sess, vgg_path)
        layer_output = layers(layer3_out, layer4_out, layer7_out, num_classes)
        
        # then call optimizer which gives logit
        logits, cost, optimizer = optimize(layer_output, correct_label, learning_rate, num_classes)


        # TODO: Train NN using the train_nn function
        sess.run(tf.global_variables_initializer())
        # Choose here this param after some trial and error
        epochs = 15
        batch_size = 1

        train_nn(sess, epochs, batch_size, get_batches_fn, optimizer, cost,
            input_image, correct_label, keep_prob, learning_rate)

        # TODO: Save inference data using helper.save_inference_samples
        #  helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape,
            logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video
        # can do 3 label , one for street where car is and the road is not


if __name__ == '__main__':
    run()
