earyx
=====

`earyx <https://github.com/stvol/earyx>`_ is a framework for developing and
running psychoacoustic experiments. It is inspired by `Psylab
<https://github.com/TGM-Oldenburg/Psylab>`_ a Matlab implementation written by
Martin Hansen.

Documentation is hosted on `Read the docs <http://earyx.readthedocs.org>`_

With **earyx** it is possible to create experiments in the most simple
way. Currently N-AFC (numbered alternate-forced-choice) and Matching experiments
are supported. For running the experiments there are several options. **earyx**
offers a commandline text user interface, a browser based graphical UI and the
possibility to hook in models or additional UI´s (no concrete model implemented yet).

.. contents::
   :depth: 2
   :backlinks: none

Installation
------------

There are several ways to install **earyx**. For now there is no official PyPi
package you can simply install via pip. Notice that **earyx** uses `Pysoundcard
<http://github.com/bastibe/pysoundcard>`_ for playback which itself depends on
the external C library *Portaudio*. Proper Pysoundcard installation is necessary
in order to install **earyx** successfully. For users not so familiar with python
and its package the following step by step description will guide you through
the installation process depending on your platform. Maybe a more practical 
alternative could be sounddevice <https://pypi.python.org/pypi/sounddevice/>.


We recommend to install **earyx** with `miniconda
<http://conda.pydata.org/miniconda.html>`_ .

Ubuntu / OSX / Windows
++++++++++++
If you don't have miniconda installed yet:
Download and install miniconda from http://conda.pydata.org/miniconda.html


Afterwards we recommend to create a virtual environment to install earyx in:

.. code::

 conda create -n earyx python=3
 source activate earyx
 pip install --upgrade pip
 conda install numpy


Now download the **earyx** repository (therefore a git installation is required):

.. code ::

 git clone https://github.com/TGM-Oldenburg/earyx.git
 cd earyx
 source activate earyx
 pip install .


That's it.
Try to run:

.. code::

 python sine_after_noise.py (commandline)

or

.. code::

 python sine_after_noise.py -u gui (gui)

If this works you have installed **earyx** sucessfully, nevertheless you will see some crazy messages in the terminal (using Ubuntu).


Philosophy of earyx
-------------------

**earyx** can be used for a wide range of psychoacoustic experiments but
not for all. For a simple decision whether **earyx** can handle the experiment you
want to build, just answer the following questions.

1. Is there exactly one value you are interested in finding a
   relative or absolute threshold for? - in **earyx** this value is called **variable**
2. Is there at least one other value or value-set the threshold to be measured
   depends on? - in **earyx** this kind of dependencies are called **parameters**
3. Do you plan to determine this threshold either with matching or in N-AFC manner?

In case you answered all of this questions with *yes* **earyx** will do the
job! If not, don't claim. **earyx** has en extremly modular and extendible
design. So feel free to read the API documentation to understand how to extend
**earyx** for your needs.

Structure of an earyx experiment
++++++++++++++++++++++++++++++++

To understand the overall structure of an **earyx** experiment it is necessary
to understand the explanation of the following terms:

Parameters
##########

Parameters define different conditions in which an experiment is
performed.

Variable
########

For this value a threshold is to be measured. Therefore it changes over time
depending on the answers the user gives.

Adapt rule
##########

The behaviour of variable change in relation to the user's answer and given by the
adapt rule. For now, **earyx** supports *1up2down*, *2up1down*, *1up3down* and
*weighted up down*. In **earyx** the adapt rules are also parameters. That
means, you can specify more than one adapt rule and the threshold is determined
using all of them (interleaved or sequential).

Reversals
#########

Reaching a threshold is mainly controlled by reversals. Depending on your
selected adapt rule a reversal occurs if the direction the variable changes its
value reverses. Changing variable direction from up to down is called *upper
reversal* changing from down to up *lower reversal*.

Step size  - start and minimal step size
########################################

The step size defines how much the variable changes from trial to trial. If a
reversal occurs (upper or lower) this step size is halved until the minimal step
size is reached. Then the measurement phase starts.

Measurement phase
#################

Each run is split into two phases. One phase before reaching the minimal step
size and one after which is called *measurement phase*. Only variable values in
this phase are used to determine the interesting threshold which is the median
of this values.

Maximal reversals
#################
This is the stop criterion for a run. When the number of reversals within the
measurement phase reaches the maximum value the run is finished.

Now you are able to understand the two main building blocks of **earyx**: Runs and
Trials.

A **run** is a combination formed from all given parameters and adapt
rules. That means, the more parameters are specified, the more runs
result. Within such a run the parameter settings are fixed and only the
variable changes from presentation to presentation according to the selected adapt
rule. One presentation is called **trial**.

Therefore in principle the overall structure is nearly the same for all **earyx**
experiments. An experiment has at least one run and each of that runs has a
number of trials necessary to determine the threshold.

How to write an experiment
--------------------------

For implementing an experiment you need to build an my_experiment.py (when class called MyExperiment) file containing three methods.

Imports
+++++++

Depending on your experiment choice you have to import *AFCExperiment* or *MatchingExperiment* from *earyx.experiments* and
*Sequential* or *Interleaved* from *earyx.order*.  

It is recommended to use given tools like *gensin*, *rms* and *hanwin* from *earyx.utils* and *numpy* for building your signals.  

Example imports:

.. code:: python
         
 from earyx.experiments import AFCExperiment 
 from earyx.order import Sequential
 from earyx.utils import gensin 
 import numpy as np


Your experiment needs to be a class inheriting from an experiment type and from an order of your choice.

Example:

``class MyExperiment(AFCExperiment,Sequential):``

The following methods have to be implemented:


init experiment
+++++++++++++++

In this method all options and parameters of the experiment need to be implemented. At least one parameter with one value, a variable and an adapt setting are needed. 
There is no limit of parameters and their values furthermore of adapt settings. There is always just one variable, it will be overridden by later variable definitions. 

Example:

.. code:: python

 def init_experiment(self, exp):
     exp.add_parameter("sine_frequenzy",[1000, 2000, 3000], "Hz")
     exp.add_parameter("duration",[1], "s")
     exp.set_variable("sine_level", -20, "dB")
     exp.add_adapt_setting("1up2down",6,8,1)
     # optinal:
     exp.num_afc = 3 #set number of AFC, *default = 3*
     exp.sample_rate = 48000 # set sampling rate, *default = 48000*
     exp.calib = 0 #free to use for calibrate a specific system
     exp.task = "In which Interval do you hear the test tone? (1,2,3)"
     exp.debug = False #user will see the plot of the variable *default = False*
     exp.discard_unfinished_runs = False # *default = False*
     exp.feedback = True #user gets response wrong or rigth, *default = True*
     exp.visual_indicator = True #buttons blinking simultaneous to sound, *default = True*
     exp.description = """This is the description of the experiment"""
     exp.allow_debug = True #user is able to de/activate the debug plotting *default = True* 
     exp.pre_signal = 0.3 # Check signal generation


init run
++++++++

All data and signals which are valid for the whole run need to be implemented here.

Example:

.. code:: python

 def init_run(self, run):
     #Implementing a frozen noise for the whole **run**:
     run.reference_signal = np.random.randn(np.round(run.duration*run.sample_rate))

init trial
++++++++++

All data and signals which are valid for a single trial need to be implemented here.

Example:

.. code:: python

 def init_trial(self, trial):
     ramp_dur = 0.1
     sine_ampl = np.sqrt(2)*10**(trial.variable/20)
     trial.test_signal = gensin(trial.sine_frequenzy,sine_ampl,trial.duration)
     #Add Sine to the frozen noise:
     trial.test_signal += trial.reference_signal
     #Hanwin for test and reference signal:
     trial.test_signal = hanwin(trial.test_signal, np.round(ramp_dur*trial.sample_rate))
     trial.reference_signal = hanwin(trial.reference_signal, np.round(ramp_dur*trial.sample_rate))
     return trial

Complete Experiment
+++++++++++++++++++

The following code is a complete experiment, which you can try out or use as sample for your own
experiment.

Example:

.. code:: python

 from earyx.experiments import AFCExperiment
 from earyx.order import Sequential
 from earyx.utils import gensin, rms
 import numpy as np
 import earyx

 class SineInNoise(AFCExperiment, Sequential):

     def init_experiment(self, exp):
         exp.add_parameter("noise_level", [-40, -60], 'dB')
         exp.set_variable("sine_level", -20, 'dB')
         exp.add_adapt_setting('1up2down', max_reversals = 8,
                              start_step = 5, min_step = 1)

         exp.num_afc = 3
         exp.discard_unfinished_runs = False
         exp.pre_signal = 0.3
         exp.between_signal = (0.3, 0)
         exp.post_signal = 0.2

         exp.description = """This is the description
         of the experiment"""

     def init_run(self, run):
         ref = np.random.randn(np.round(0.3*run.sample_rate))
         ref = ref/rms(ref)*10**(run.noise_level/20)
         run.reference_signal = ref

     def init_trial(self, trial):
         ampl = np.sqrt(2)*10**(trial.variable/20)
         test = gensin(1600, ampl, 0.03, trial.sample_rate)
         pos = np.round((len(trial.reference_signal) - len(test))/2)
         trial.test_signal = trial.reference_signal.copy()
         trial.test_signal[pos:pos+len(test)] += test

 if __name__ == '__main__':
    earyx.start(SineInNoise)

	 
Signal generation
-----------------
In **earyx** there are exactly five different signals with predefined names which are
connected to the output signal.

1. pre_signal
2. between_signal
3. post_signal
4. reference_signal
5. test_signal

Depending on the selected type of experiment (AFC or Matching) they are
automatically prepared for playback. In case of a 3-AFC experiment one possible
signal order could be:

`pre` | `reference` | `between` | `test` | `between` | `reference` | `post`

or in case of a 2-AFC or Matching experiment:

`pre` | `reference` | `between` | `test` | `post`


Signal inheritance
++++++++++++++++++

**earyx** provides a mechanism called **signal inheritance** which means, that
signals will be inherited from stage to stage. Let's have a look at the three
stages ``init_experiment``, ``init_run`` and ``init_experiment``. In each of
them you have access to the five **earyx** signals as attributes. For example, in
``init_experiment`` you can set the ``pre_signal`` via ``exp.pre_signal =
...``. The other stages ``init_run`` and ``init_trial`` also have the attribute
``pre_signal`` and inherit the values from parent stages if already set.  That
means, ``run.pre_signal`` and ``trial.pre_signal`` will automatically set to the
value of ``exp.pre_signal`` defined in ``init_experiment``.  This concept allows
comfortable and memory efficent signal generation. Let's say, you want to design
an experiment in which pre, between and post signal should be the same in all
trials. Simply define them in ``init_experiment``. Maybe your reference signal
should be the same not for the whole experiment but in every trial of one run,
then you can define your ``reference_signal`` in ``init_run``. For
more inspiration see the example experiments.

Mono, stereo, multichannel
++++++++++++++++++++++++++

In **earyx** the experiment creator is responsible for generating valid
signals. That means, for automatic concatenation all signals must have the same
shape. For simplicity we suggest to build your signals as numpy arrays with
shape (SAMPLES, NUM_CHANNELS). In case all your signals are diotic (all channels
are identical), there is one exception from this rule, because you can build
your signals as numpy arrays either with shape (SAMPLES,) or
(SAMPLES,1). Afterwards this single vector will be copied to all channels your
playback system has.

Zero signals
++++++++++++

In most cases `pre_signal`, `between_signal` and `post_signal` should be only
zero signals of given length to control the pause duration between the presented
test or reference signals. Therefore **earyx** provides a comfortable way to define
them.
To generate an zero signal with length `0.3s` you can write:

``pre_signal = 0.3`` which is automatically transformed into
``np.zeros(0.3*sample_rate)``

But there is also an exteded syntax to define multi channel zero signals.

``pre_signal = (0.3,NUM_CHANNELS)`` leads to ``np.zeros((0.3*sample_rate,
NUM_CHANNELS))``

As you can see there are many ways to define proper signals in **earyx**. But to
avoid some trouble always keep in mind: **All your signals *must have* the same shape!**


Calibration
-----------

Calibration is a difficult topic in psychoacoustic experiments because there is
no standarized way. In **earyx** the experiment creator has full control and
responsibility to generate calibrated signals. **earyx** provides little help by
offering the attribute ``calib`` aviable in the whole experiment (``calib`` is 
equivalent to 0dB FS [dB SPL]). It is inherited in the same way like the signals,
see `Signal inheritance`_. You have full freedom how to use this variable for 
controlling your signals.
   

Invocation
----------
The invocation to start an experiment from terminal/command line is

   ``python experiment_name.py``.

You have to be in the same directory as the experiment file.

Flags
   [-u]: Defines the user interface. 
      - ``-u gui`` starts the experiment with a graphical user interface.
      - ``-u egui`` gives you an IP address with which the experiment can be performed
        on another device by calling that IP address in an internet browser. Your
        computer and the other device have to be in the same network for this!

      If this flag is not set the default UI is a text based user interface (TUI).
   
   [-a]: Defines the audio output. 
      - ``-a 1``: Sound from internet browser; default with ``-u gui``
      - ``-a 2``: Sound from internet browser and Python
      - ``-a 3``: Sound from Python; default with no ``[-u]`` option and ``-u egui``

   [-l]: Opens a file dialog. 
      - You can then load an unfinished experiment.

There is an **earyx** server that lets you perform several experiments at the same
time on the same or on a different device. To start the server you have to be in
``YOUR_EARYX_PATH/earyx/``. The invocation works as follows:

   ``python server.py``

After this you will get an IP address that you type or paste in the URL line of
your internet browser. If you use this with other devices you have to be in the
same network. You can choose between all experiments, which are arrange in the folder
``experiments``.  

Here is an example how to load (``-l``) an unfinished experiment in a GUI (``-u gui``)
and with audio output from Python (``-a 3``). Just to show how easy it is to use all flags at once:

   ``python experiment_name.py -u gui -a 3 -l``



History
-------
Both frameworks are developed at the Jade University of Applied
Sciences Oldenburg in which the first version of **earyx** is the result of an one
semester programming project. **earyx** is developed by Sven Hermann, Jonas Klug, Nils
Schreiber, Matthias Stennes, Stephanus Volke and with the help of Bastian Bechtold.

TODOS (Contribute!)
-------------------
If you want to contribute to this project, please fork and contribute!

We are sure that there are a **lot** of cool ideas to improve **earyx**! This is just the beginning!
We are looking for your ideas! In our opinion the next steps to make are:

* complete API documentation 

  * add the documentation to `readthedocs <http://readthedocs.org/>`_
* **earyx** plotting engine for final results

  * at the moment it is not possible to plot thresholds or the like
  * at the moment the position is somehow random, so that it sometimes shows up and sometimes not (this differs from device to) device	
  
* add **earyx** logo to GUI
* correct the display of the plotting window on mobile devices 
* change activate debugging button to a checkbox (in GUI)
* write more testers

  * we use `py.test <http://pytest.org/latest/>`_  
  

No warranty
-----------
**earyx** is distributed without any kind of warranty.

The use of **earyx**, for whatever purpose, is under the complete and
sole responsibility of the user. *Special attention* is drawn to the
fact that **earyx** does not comprise an automatic mechanism to
prevent the delivery of too loud sound pressure levels. It is the
explicit and sole responsibility of the user of **earyx** to make sure that
the generated stimuli, in combination with any further equipment
(sound card, amplifier, headphone or loudspeaker, etc.), will yield the
desired sound level.  

Licence
-------
**earyx** is “free software” and is distributed in OpenSource format under the
terms of the GNU General Public Licence (GPL). This means, amongst others, that
copies of the **earyx** software may be distributed without asking for permission, given that the terms of the GNU GPL are obeyed to.
For more details, see http://www.gnu.org/licenses/ or look at a verbose copy of the GNU GPL in the root directory of **earyx**.
