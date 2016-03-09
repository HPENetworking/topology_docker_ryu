=================
Ryu Topology Node
=================

Using the Ryu Controller
------------------------

The Ryu controller is made available as a Topology node. The implementation is
based on `osrg's ryu Dockerfiles <https://github.com/osrg/dockerfiles>`_. Check
current repository under ``docker/Dockerfile`` for our docker container.

Ryu supports applications, which are written in Python as described in the
`Ryu documentation <http://ryu.readthedocs.org/en/latest/>`_.

To start a Ryu node declare it in your topology as:

::

   [type=ryu name="Ctrl 1" app="/path/to/my/app/ryu.py"] ctrl

The app parameter is the path to a python Ryu application. The sample
``simple_switch`` application is run by default. Use an absolute path here,
preferably with a base path set by an environment variable for portability.
Your application will be run as:

::

   PYTHONPATH=. ryu-manager my-app.py --verbose

``ryu-manager`` will listen for connections in every available interface.
The stdout log is accessible in the container at ``/tmp`` or in your host
machine at ``/tmp/topology_<NODE_NAME>_<NODE_ID>``.

You may include any specific ryu-manager options by killing the process with:

::

   switch('supervisorctl stop ryu-manager')

And then manually running it, but be sure to send it to the background:

::

   switch('PYTHONPATH=. ryu-manager my-app.py --verbose &>/tmp/ryu.log &')

You may also pass your own RYU_COMMAND environment variable to supervisor and
re-run the daemon:

::

   switch('RYU_COMMAND="/path/to/ryu-manager /path/to/my-app.py --verbose" supervisord')

You may have to remove the supervisor sock file with:

::

   switch('unlink /var/run/supervisor.sock')

Once the controller instance is running, you should be able to establish a TCP
connection from any reachable switch. Ryu will listen at all interfaces by
default.

For Open vSwitch, assuming you have a oobm port with the ip ``10.0.10.2``:

::

    # Configuration:
    # - Create a virtual bridge
    # - Drop packets if the connection to controller fails
    # - Add frontal ports to virtual bridge
    # - Give the virtual bridge an IP address
    # - Bring up virtual bridge
    # - Connect to the OpenFlow controller
    commands = """
    ovs-vsctl add-br br0
    ovs-vsctl set-fail-mode br0 secure
    ovs-vsctl add-port br0 1
    ovs-vsctl add-port br0 2
    ip addr add 10.0.10.3/24 dev br0
    ip link set br0 up
    ovs-vsctl set-controller br0 tcp:10.0.10.1:6633
    """
    sw1.libs.common.assert_batch(commands)

    # Wait for OVS to connect to controller
    time.sleep(5)

    # Assert that switch is connected to Ryu
    vsctl_sw1_show = sw1('ovs-vsctl show')
    assert 'is_connected: true' in vsctl_sw1_show


Debugging Ryu Node
------------------

Ryu is started by supervisor.

- If you have access to the running container, supervisorctl allows you to
  check the status and logs of the ryu process.
- If the Topology startup fails, stdout and stderr logs for every supervisor
  process are kept in the container at the /tmp folder, which is shared with
  your host machine at ``/tmp/topology_<NODE_NAME>_<NODE_ID>``, so that you are
  able to check those logs afterwards.
- Check the ``supervisord.conf`` file for details on how the services are being
  started.
