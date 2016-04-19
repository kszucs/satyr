from __future__ import absolute_import, division, print_function

from uuid import uuid4

import cloudpickle
from mesos.interface import mesos_pb2

from .proxies.messages import Cpus, Disk, Mem, TaskInfo, TaskStatus


class PickleMixin(object):

    @property
    def data(self):
        return cloudpickle.loads(self['data'])

    @data.setter
    def data(self, value):
        self['data'] = cloudpickle.dumps(value)


class PythonTaskStatus(PickleMixin, TaskStatus):

    proto = mesos_pb2.TaskStatus(
        labels=mesos_pb2.Labels(
            labels=[mesos_pb2.Label(key='python')]))

    def __init__(self, data=None, **kwargs):
        super(PythonTaskStatus, self).__init__(**kwargs)
        self.data = data


class PythonTask(PickleMixin, TaskInfo):  # TODO: maybe rename basetask

    proto = mesos_pb2.TaskInfo(
        labels=mesos_pb2.Labels(
            labels=[mesos_pb2.Label(key='python')]))

    def __init__(self, fn=None, args=[], kwargs={},
                 resources=[Cpus(1), Mem(64)], on_success=None, **kwds):
        super(PythonTask, self).__init__(**kwds)
        self.resources = resources
        # self.executor.name = 'test-executor'
        self.executor.executor_id.value = self.task_id.value
        self.executor.resources = resources
        self.executor.command.value = 'python -m satyr.executor'
        self.executor.command.shell = True
        self.executor.container.type = 'DOCKER'
        self.executor.container.docker.image = 'lensacom/satyr:latest'
        self.executor.container.docker.network = 'HOST'
        self.executor.container.docker.force_pull_image = False

        self.data = (fn, args, kwargs)  # TODO: assert fn is callable
        self.on_success = on_success  # TODO: assert is callable

    def __call__(self):
        fn, args, kwargs = self.data
        return fn(*args, **kwargs)

    def status(self, state, **kwargs):
        return PythonTaskStatus(task_id=self.task_id, state=state, **kwargs)

    def update(self, status):
        self.state = status

        if status.is_successful() and callable(self.on_success):
            self.on_success(self)

    def result(self):
        if self.state.is_successful():
            return self.state.data
