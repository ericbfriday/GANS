
import numpy as np
import tensorflow as tf
from preprocess import preprocess
import os
import sys

HEIGHT, WIDTH, CHANNEL = 128, 128, 3
BATCH_SIZE = 32
EPOCHS = 100
SAMPLE_SIZE = 8
random_dim = 100
learning_rate = 0.01


def generator(input_tensor, random_dim):
    start_dim = 8 # starting dimension of the
    CHANNEL = 3 # end channels
    #channel dimension list
    c4,c3,c2,c1 = 256,128,64,32

    with tf.variable_scope('gen') as scope:
    #add a dense layer to make it
        dense_1 = tf.layers.dense(input_tensor, units=start_dim*start_dim*c4, activation=tf.nn.relu)
        batch_norm_1 = tf.contrib.layers.batch_norm(dense_1)

        conv1 = tf.reshape(batch_norm_1,shape=[-1,start_dim,start_dim,c4])

        #Deconvolution operarions
        deconv1 = tf.layers.conv2d_transpose(conv1,filters=c3,kernel_size=[3,3],strides=[2,2],padding='SAME',kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
        batch_norm_deconv_1 = tf.contrib.layers.batch_norm(deconv1)
        act1 = tf.nn.relu(batch_norm_deconv_1)

        deconv2 = tf.layers.conv2d_transpose(act1,filters=c2,kernel_size=[3,3],strides=[2,2],padding='SAME',kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
        batch_norm_deconv_2 = tf.contrib.layers.batch_norm(deconv2)
        act2 = tf.nn.relu(batch_norm_deconv_2)

        deconv3 = tf.layers.conv2d_transpose(act2,filters=c1,kernel_size=[3,3],strides=[2,2],padding='SAME',kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
        batch_norm_deconv_3 = tf.contrib.layers.batch_norm(deconv3)
        act3 = tf.nn.relu(batch_norm_deconv_3)

        deconv4 = tf.layers.conv2d_transpose(act3,filters=CHANNEL,kernel_size=[3,3],strides=[2,2],padding='SAME',kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
        batch_norm_deconv_4 = tf.contrib.layers.batch_norm(deconv4)
        act4 = tf.nn.tanh(batch_norm_deconv_4, name='generator')
        return act4



def discriminator(image,reuse=False):
    c4,c3,c2,c1 = 256,128,64,32
    with tf.variable_scope('disc') as scope:
        if reuse:
            scope.reuse_variables()
        conv1 = tf.layers.conv2d(image,filters=c1,kernel_size=[5,5],strides=[2,2],padding='SAME',kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
        batch_norm_1 = tf.contrib.layers.batch_norm(conv1)
        act1 = tf.nn.relu(batch_norm_1)

        conv2 = tf.layers.conv2d(act1,filters=c2,kernel_size=[5,5],strides=[2,2],padding='SAME',kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
        batch_norm_2 = tf.contrib.layers.batch_norm(conv2)
        act2 = tf.nn.relu(batch_norm_2)

        conv3 = tf.layers.conv2d(act2,filters=c3,kernel_size=[5,5],strides=[2,2],padding='SAME',kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
        batch_norm_3 = tf.contrib.layers.batch_norm(conv3)
        act3 = tf.nn.relu(batch_norm_3)


        conv4 = tf.layers.conv2d(act3,filters=c4,kernel_size=[5,5],strides=[2,2],padding='SAME',kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
        batch_norm_4 = tf.contrib.layers.batch_norm(conv4)
        act4 = tf.nn.relu(batch_norm_4)
        flattend = tf.reshape(act4,[-1,np.product(act4.get_shape()[1:])])
        logits =  tf.layers.dense(flattend,units=1)
        activated = tf.nn.sigmoid(logits,name='discriminator')

        return activated


def train():
    X = preprocess().load().X
    m = X.shape[0]
    d_iters = 10
    gLosses = []
    dLosses = []

    real_image = tf.placeholder(dtype=tf.float32,shape=[None,HEIGHT,WIDTH,CHANNEL],name='image_input')
    random_inp = tf.placeholder(dtype=tf.float32,shape=[None,random_dim],name='random_inp')

    fake_image_generator = generator(random_inp, random_dim)
    real_result = discriminator(real_image)
    fake_result = discriminator(fake_image_generator,reuse=True)


    # loss functions
    d_loss = tf.reduce_mean(fake_result) - tf.reduce_mean(real_result)
    g_loss = - tf.reduce_mean(fake_result)

    d_weights = [var for var in tf.trainable_variables() if 'disc' in var.name]

    trainer_d = tf.train.RMSPropOptimizer(learning_rate=learning_rate).minimize(d_loss)
    trainer_g = tf.train.RMSPropOptimizer(learning_rate=learning_rate).minimize(g_loss)
    d_clip = [v.assign(tf.clip_by_value(v, -0.01,0.01)) for v in d_weights]

    init = tf.global_variables_initializer()
    saver = tf.train.Saver(max_to_keep=4)
    sess = tf.Session()
    sess.run(init)
    print "-----------------------------------Starting to train---------------------------------"
    sys.stdout.flush()

    for epoch in range(EPOCHS):
        np.random.shuffle(X)
        for batch_num in range(0,m,BATCH_SIZE):
            ## discriminator loop
            curr_batch = X[batch_num:batch_num+BATCH_SIZE]
            for d_n in range(d_iters):
                choice = np.random.randint(0,curr_batch.shape[0],(SAMPLE_SIZE))
                curr_sample = curr_batch[choice]
                #random input
                train_noise = np.random.uniform(-1.0, 1.0, size=[SAMPLE_SIZE, random_dim]).astype(np.float32)
                sess.run(d_clip)
                #train the desc
                _, dLoss = sess.run([trainer_d, d_loss], feed_dict={real_image:curr_sample,random_inp:train_noise})
                dLosses.append(dLoss)

            train_noise = np.random.uniform(-1.0, 1.0, size=[SAMPLE_SIZE, random_dim]).astype(np.float32)
            _, gLoss = sess.run([trainer_g, g_loss],feed_dict={random_inp:train_noise})

            gLosses.append(gLoss)

        # save the model
        if epoch%2==0:
            print "EPOCH: "+str(epoch)
        if(epoch%2==0):
            saver.save(sess,'models/PokeGanModelV1/model', global_step=epoch, write_meta_graph=False)

        # if(epoch%5==0):
        #     #save some images
        #     os.makedirs('genrated/'+str(epochs))
        #     sample_noise = np.random.uniform(-1.0, 1.0, size=[batch_size, random_dim]).astype(np.float32)
        #     gen_images = sess.run(fake_image)
        #     save_images(gen_images, epochs)
        #
        # with open("controlTraining.txt",'r') as f:
        #     control = f.read()
        #     if control.strip() == "1":
        #        print "stopping the training process .........."
        #        sys.stdout.flush()
        #        break


    saver.save(sess,'PokeGanModel', global_step=EPOCHS, write_meta_graph=False)
    # os.makedirs('genrated/'+str(EPOCHS))
    # sample_noise = np.random.uniform(-1.0, 1.0, size=[batch_size, random_dim]).astype(np.float32)
    # gen_images = sess.run(fake_image)
    # save_images(gen_images, epochs)

def test():
    pass

def save_images(genrated, epochs):
    pass

train()
