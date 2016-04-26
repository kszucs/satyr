import pytest
from mesos.interface import mesos_pb2
from satyr.proxies.messages import (CommandInfo, Cpus, Disk, FrameworkID,
                                    FrameworkInfo, Map, Mem, MessageProxy,
                                    Offer, RegisterProxies, TaskID, TaskInfo,
                                    TaskStatus, decode, encode)


@pytest.fixture
def d():
    return {'a': 1,
            'b': [{'j': 9},
                  {'g': 7, 'h': 8}],
            'c': {'d': 4,
                  'e': {'f': 6}}}


def test_map_init(d):
    m = Map(**d)
    assert isinstance(m, Map)
    assert isinstance(m, dict)


def test_map_get(d):
    m = Map(**d)
    assert m['a'] == 1
    assert m['c']['e']['f'] == 6
    assert m['b'][0]['j'] == 9
    assert m['b'][1]['g'] == 7
    assert isinstance(m['b'], list)
    assert isinstance(m['b'][1], Map)


def test_map_dot_get(d):
    m = Map(**d)
    assert m.a == 1
    assert m.c.e.f == 6
    assert m.b[0].j == 9
    assert m.b[1].g == 7
    assert isinstance(m.b, list)
    assert isinstance(m.b[1], Map)


def test_map_set(d):
    m = Map(**d)
    m['A'] = 11
    m['a'] = 'one'
    m['z'] = {'Z': {'omega': 20}}
    assert m['a'] == 'one'
    assert m['A'] == 11
    assert m['z']['Z']['omega'] == 20
    assert isinstance(m['z'], Map)
    assert isinstance(m['z']['Z'], Map)


def test_map_dot_set(d):
    m = Map(**d)
    m.A = 11
    m.a = 'one'
    m.z = {'Z': {'omega': 20}}
    assert m.a == 'one'
    assert m.A == 11
    assert m.z.Z.omega == 20
    assert isinstance(m.z, Map)
    assert isinstance(m.z.Z, Map)


def test_map_set_missing(d):
    m = Map(**d)
    m['y']['o']['w'] = 9
    m.y.w.o = 6

    assert m['y']['o']['w'] == 9
    assert m.y.w.o == 6


def test_hash():
    d1 = Map(a=Map(b=3), c=5)
    d2 = Map(a=Map(b=3), c=5)
    d3 = Map(a=Map(b=6), c=5)

    assert hash(d1) == hash(d2)
    assert hash(d1) != hash(d3)
    assert hash(d2) != hash(d3)


def test_dict_hashing():
    d1 = Map(a=Map(b=3), c=5)
    d2 = Map(a=Map(b=3), c=5)
    d3 = Map(a=Map(b=6), c=5)

    c = {}
    c[d2.a] = d2
    c[d3.a] = d3

    assert c[d2.a] == d2
    assert c[d3.a] == d3


def test_register_proxies():
    class Base(object):
        __metaclass__ = RegisterProxies
        proto = 'base'

    class First(Base):
        proto = 'first'

    class Second(Base):
        proto = 'second'

    class Third(Base):
        proto = 'third'

    assert Base.registry == [('third', Third),
                             ('second', Second),
                             ('first', First),
                             ('base', Base)]


def test_encode_resources():
    pb = encode(Cpus(0.1))
    assert pb.scalar.value == 0.1
    assert pb.name == 'cpus'
    assert pb.type == mesos_pb2.Value.SCALAR

    pb = encode(Mem(16))
    assert pb.scalar.value == 16
    assert pb.name == 'mem'
    assert pb.type == mesos_pb2.Value.SCALAR

    pb = encode(Disk(256))
    assert pb.scalar.value == 256
    assert pb.name == 'disk'
    assert pb.type == mesos_pb2.Value.SCALAR


def test_encode_task_info():
    task = TaskInfo(name='test-task',
                    id=TaskID(value='test-task-id'),
                    resources=[Cpus(0.1), Mem(16)],
                    command=CommandInfo(value='testcmd'))
    pb = encode(task)
    assert pb.name == 'test-task'
    assert pb.task_id.value == 'test-task-id'
    assert pb.resources[0].name == 'cpus'
    assert pb.resources[0].scalar.value == 0.1
    assert pb.resources[1].name == 'mem'
    assert pb.resources[1].scalar.value == 16
    assert pb.command.value == 'testcmd'


def test_decode_framework_info():
    message = mesos_pb2.FrameworkInfo(id=mesos_pb2.FrameworkID(value='test'))
    wrapped = decode(message)

    assert isinstance(wrapped, MessageProxy)
    assert isinstance(wrapped, FrameworkInfo)
    assert isinstance(wrapped.id, MessageProxy)
    assert isinstance(wrapped.id, FrameworkID)


def test_resources_mixin():
    o1 = Offer(resources=[Cpus(1), Mem(128), Disk(0)])
    o2 = Offer(resources=[Cpus(2), Mem(256), Disk(1024)])

    t1 = TaskInfo(resources=[Cpus(0.5), Mem(128), Disk(0)])
    t2 = TaskInfo(resources=[Cpus(1), Mem(256), Disk(512)])

    assert o1.cpus == 1
    assert o1.mem == 128
    assert o2.cpus == 2
    assert o2.disk == 1024

    assert t1.cpus == 0.5
    assert t1.mem == 128
    assert t2.cpus == 1
    assert t2.disk == 512

    assert o1 == o1
    assert o1 < o2
    assert o1 <= o2
    assert o2 > o1
    assert o2 >= o1

    assert t1 == t1
    assert t1 < t2
    assert t1 <= t2
    assert t2 > t1
    assert t2 >= t1

    assert o1 >= t1
    assert o2 >= t1
    assert o2 >= t2
    assert t2 >= o1


def test_encode_task_info():
    t = TaskInfo(name='test-task',
                 id=TaskID(value='test-task-id'),
                 resources=[Cpus(0.1), Mem(16)],
                 command=CommandInfo(value='echo 100'))

    p = encode(t)
    assert isinstance(p, mesos_pb2.TaskInfo)
    assert p.command.value == 'echo 100'
    assert p.name == 'test-task'
    assert p.resources[0].name == 'cpus'
    assert p.resources[0].scalar.value == 0.1
    assert p.task_id.value == 'test-task-id'


def test_non_strict_encode_task_info():
    t = TaskInfo(name='test-task',
                 id=TaskID(value='test-task-id'),
                 resources=[Cpus(0.1), Mem(16)],
                 command=CommandInfo(value='echo 100'))
    t.result = 'some binary data'
    t.status = TaskStatus()

    p = encode(t)
    assert isinstance(p, mesos_pb2.TaskInfo)
    assert p.command.value == 'echo 100'
    with pytest.raises(AttributeError):
        p.status