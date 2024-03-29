#!/usr/bin/env python3

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

import gym
import numpy as np
import tensorflow as tf
from tensorflow.contrib.layers import *
from pylab import *
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook

import sys



parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-l', '--load-model', metavar='NPZ',
                    help='NPZ file containing model weights/biases')
args = parser.parse_args()



env = gym.make('CartPole-v0') #Change 1

RNG_SEED=1
tf.set_random_seed(RNG_SEED)
env.seed(RNG_SEED)

hidden_size = 2 #Change 2
alpha = 0.0001  #Change 3
TINY = 1e-8
gamma = 0.99 #Change 4

weights_init = xavier_initializer(uniform=False)
relu_init = tf.constant_initializer(0.1)

if args.load_model:
    model = np.load(args.load_model)
    hw_init = tf.constant_initializer(model['hidden/weights'])
    hb_init = tf.constant_initializer(model['hidden/biases'])
    mw_init = tf.constant_initializer(model['mus/weights'])
    mb_init = tf.constant_initializer(model['mus/biases'])
    sw_init = tf.constant_initializer(model['sigmas/weights'])
    sb_init = tf.constant_initializer(model['sigmas/biases'])
else:
    hw_init = weights_init
    hb_init = relu_init
    mw_init = weights_init
    mb_init = relu_init
    sw_init = weights_init
    sb_init = relu_init

try:
    output_units = env.action_space.shape[0]
except AttributeError:
    output_units = env.action_space.n

input_shape = env.observation_space.shape[0]
NUM_INPUT_FEATURES = 4 
x = tf.placeholder(tf.float32, shape=(None, NUM_INPUT_FEATURES), name='x')
y = tf.placeholder(tf.int32, shape=(None, output_units), name='y') #Change 5



hidden = fully_connected( #Change 6
    inputs=x,
    num_outputs=hidden_size,
    activation_fn=tf.nn.softmax,
    weights_initializer=hw_init,
    weights_regularizer=None,
    biases_initializer=hb_init,
    scope='hidden')

all_vars = tf.global_variables()

pi = tf.contrib.distributions.Bernoulli(p=hidden, name='pi') #Change 7
pi_sample = pi.sample()
log_pi = pi.log_prob(y, name='log_pi')

Returns = tf.placeholder(tf.float32, name='Returns')
optimizer = tf.train.GradientDescentOptimizer(alpha)
train_op = optimizer.minimize(-1.0 * Returns * log_pi)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

MEMORY=25
MAX_STEPS = env.spec.tags.get('wrapper_config.TimeLimit.max_episode_steps')

#for plotting
steps = []
average_steps = []
track_returns = []
track_steps = []
weight1 = []
weight2 = []
weight3 = []
weight4 = []

for ep in range(4000):

    obs = env.reset()

    G = 0
    ep_states = []
    ep_actions = []
    ep_rewards = [0]
    done = False
    t = 0
    I = 1
    while not done:
        ep_states.append(obs)
        #env.render()
        action = sess.run([pi_sample], feed_dict={x:[obs]})[0][0]
        ep_actions.append(action)
        obs, reward, done, info = env.step(action[0]) #Change 8
        ep_rewards.append(reward * I)
        G += reward * I
        I *= gamma

        t += 1
        if t >= MAX_STEPS:
            break

    if not args.load_model:
        returns = np.array([G - np.cumsum(ep_rewards[:-1])]).T
        index = ep % MEMORY
        
        
        _ = sess.run([train_op],
                    feed_dict={x:np.array(ep_states),
                                y:np.array(ep_actions),
                                Returns:returns })
    steps.append(t)
    track_returns.append(G)
    track_returns = track_returns[-MEMORY:]
    mean_return = np.mean(track_returns)
    
    track_steps.append(t)
    track_steps = track_steps[-MEMORY:]
    mean_steps = np.mean(track_steps)
    average_steps.append(mean_steps)
    
    with tf.variable_scope("hidden", reuse=True):
        weights = sess.run(tf.get_variable("weights")[:,0])
        weight1.append(weights[0])
        weight2.append(weights[1])
        weight3.append(weights[2])
        weight4.append(weights[3])
    
    if ep % 100 == 0:
        
        print("Episode {} finished after {} steps with return {}".format(ep, t, G))
        #print("Mean return over the last {} episodes is {}".format(MEMORY,
                                                                #mean_return))

        print("Average number of steps over the last {} episode is {}".format(MEMORY, mean_steps))
        with tf.variable_scope("hidden", reuse=True):
            print("incoming weights:", sess.run(tf.get_variable("weights")[:,0]))


sess.close()

#Plot Performance
tot_epis = 4000
x_axis = linspace(0, tot_epis, len(steps))
plt_steps = plt.plot(x_axis, steps, label = 'Steps')
plt_steps = plt.plot(x_axis, average_steps, label = 'Mean Steps')
plt.xlabel('Episode Number')
plt.ylabel('Number of Steps')
plt.title('Performance')
plt.legend(["Steps", "Mean Steps"], loc=7)
plt.savefig("cartpole.png")
f1 = plt.figure() #needed to display on different windows
#plt.show()


#Plot Weights
x_axis = linspace(0, tot_epis, len(steps))
plt_steps = plt.plot(x_axis, weight1, label = 'Weight 1')
plt_steps = plt.plot(x_axis, weight2, label = 'Weight 2')
plt_steps = plt.plot(x_axis, weight3, label = 'Weight 3')
plt_steps = plt.plot(x_axis, weight4, label = 'Weight 4')

plt.xlabel('Episode Number')
plt.ylabel('Weights')
plt.title('Weights vs. Episode Number')
plt.legend(['Weight 1', 'Weight 2', 'Weight 3', 'Weight 4'], loc=7)
plt.savefig("cartpole_weights.png")
f2 = plt.figure() #needed to display on different windows


plt.show()




