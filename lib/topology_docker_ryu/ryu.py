# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Custom Topology Docker Node for Ryu SND controller.

    http://osrg.github.io/ryu/
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from time import sleep
from shutil import copy
from subprocess import Popen
from os.path import basename, join
from shlex import split as shsplit

from topology_docker.node import DockerNode
from topology_docker.utils import ensure_dir
from topology_docker.shell import DockerBashShell


class RyuNode(DockerNode):
    """
    Custom Ryu SDN controller node capable of running custom apps.

    This custom node loads a Ryu docker image. It takes and runs a custom
    app by using ryu-manager.

    The default image is osrg/ryu from:

    - https://hub.docker.com/r/osrg/ryu/
    - https://github.com/osrg/dockerfiles/blob/master/ryu/Dockerfile

    See :class:`topology_docker.node.DockerNode`.

    :param str app: Path the to ``.py`` application that Ryu needs to run.
    :param bool autostart: Automatically start the application once the
     topology is built.
    """

    def __init__(
            self, identifier,
            image='topology/ryu:latest', binds=None,
            app=None, autostart=True,
            **kwargs):

        # Determine shared directory
        shared_dir = '/tmp/topology_{}_{}'.format(identifier, str(id(self)))
        ensure_dir(shared_dir)

        # Add binded directories
        container_binds = [
            '{}:/tmp'.format(shared_dir)
        ]
        if binds is not None:
            container_binds.append(binds)

        super(RyuNode, self).__init__(
            identifier,
            image=image, binds=';'.join(container_binds),
            **kwargs
        )

        # Save location of the shared dir in host
        self.shared_dir = shared_dir

        # Determine app to run
        if app is None:
            app = '/root/ryu-master/ryu/app/simple_switch.py'
        else:
            # Copy the ryu app into the container
            copy(app, self.shared_dir)
            app = join('/tmp', basename(app))
        self.app = app

        # Add bash shell
        self._shells['bash'] = DockerBashShell(
            self.container_id, 'bash'
        )

        # Save autostart option
        self._autostart = autostart

        # Supervisor daemon
        self._supervisord = None

    def notify_post_build(self):
        """
        Get notified that the post build stage of the topology build was
        reached.

        See :meth:`DockerNode.notify_post_build` for more information.
        """

        super(RyuNode, self).notify_post_build()
        self._setup_system()

    def _setup_system(self):
        """
        Setup the controller image for testing.

        #. Bring up the ports connecting to the datapaths
        #. Run ryu-manager
        """

        # Check if ryu should be started by Topology
        if not self._autostart:
            return

        # run ryu app using ryu-manager
        self._supervisord = Popen(shsplit(
            'docker exec {} '
            'sh -c "RYU_COMMAND=\'/root/ryu-master/bin/ryu-manager {} '
            '--verbose\' supervisord"'.format(
                self.container_id,
                self.app
            )
        ))

        # Wait for ryu-manager to start
        config_timeout = 100
        i = 0
        while i < config_timeout:
            config_status = self._docker_exec(
                'supervisorctl status ryu-manager'
            )

            if 'RUNNING' not in config_status:
                sleep(0.1)
            else:
                break
            i += 1

        if i == config_timeout:
            raise RuntimeError(
                'ryu-manager did not reach RUNNING state on supervisor!'
            )


__all__ = ['RyuNode']
