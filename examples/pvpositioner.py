#!/usr/bin/env python2.7
'''A simple test for :class:`PVPositioner`'''

import time
import epics

import config
from ophyd.controls import (PVPositioner, PVPositionerPC)
from ophyd.controls.signal import (EpicsSignal, EpicsSignalRO)
from ophyd.controls.device import (Component as C)

logger = None


def put_complete_test():
    logger.info('--> PV Positioner, using put completion and a DONE pv')

    class MyPositioner(PVPositionerPC):
        '''PV positioner, put completion with a done pv'''
        setpoint = C(EpicsSignal, '.VAL')
        readback = C(EpicsSignalRO, '.RBV')
        done = C(EpicsSignalRO, '.MOVN')
        done_value = 0

    pos = MyPositioner(config.motor_recs[0], name='mypos_pc_done')
    pos.wait_for_connection()

    high_lim = pos.setpoint.high_limit
    try:
        pos.check_value(high_lim + 1)
    except ValueError as ex:
        logger.info('Check value for single failed, as expected (%s)', ex)
    else:
        print('high lim is %f' % high_lim)
        raise ValueError('check_value should have failed')

    stat = pos.move(1, wait=False)
    logger.info('--> post-move request, moving=%s', pos.moving)

    while not stat.done:
        logger.info('--> moving... %s error=%s', stat, stat.error)
        time.sleep(0.1)

    pos.move(-1, wait=True)
    logger.info('--> synchronous move request, moving=%s', pos.moving)

    logger.info('--> PV Positioner, using put completion and no DONE pv')

    # PV positioner, put completion, no done pv
    class MyPositioner(PVPositionerPC):
        '''PV positioner, put completion with a done pv'''
        setpoint = C(EpicsSignal, '.VAL')
        readback = C(EpicsSignalRO, '.RBV')

    pos = MyPositioner(config.motor_recs[0], name='mypos_pc_nodone')

    stat = pos.move(2, wait=False)
    logger.info('--> post-move request, moving=%s', pos.moving)

    while not stat.done:
        logger.info('--> moving... %s', stat)
        time.sleep(0.1)

    pos.move(0, wait=True)
    logger.info('--> synchronous move request, moving=%s', pos.moving)


def callback(sub_type=None, timestamp=None, value=None, **kwargs):
    logger.info('[callback] [%s] (type=%s) value=%s', timestamp, sub_type,
                value)


def done_moving(**kwargs):
    logger.info('Done moving %s', kwargs)


def test():
    global logger

    loggers = ('ophyd.controls',
               )

    config.setup_loggers(loggers)
    logger = config.logger

    fm = config.fake_motors[0]

    # ensure we start at 0 for this simple test
    epics.caput(fm['setpoint'], 0)
    epics.caput(fm['actuate'], 1)
    time.sleep(2)

    if 0:
        pos = PVPositioner(fm['setpoint'],
                           readback=fm['readback'],
                           act=fm['actuate'], act_val=1,
                           stop=fm['stop'], stop_val=1,
                           done=fm['moving'], done_val=1,
                           put_complete=False,
                           )

        pos.subscribe(callback, event_type=pos.SUB_DONE)

        pos.subscribe(callback, event_type=pos.SUB_READBACK)

        logger.info('---- test #1 ----')
        logger.info('--> move to 1')
        pos.move(1)
        logger.info('--> move to 0')
        pos.move(0)

        logger.info('---- test #2 ----')
        logger.info('--> move to 1')
        pos.move(1, wait=False)
        time.sleep(0.5)
        logger.info('--> stop')
        pos.stop()
        logger.info('--> sleep')
        time.sleep(1)
        logger.info('--> move to 0')
        pos.move(0, wait=False, moved_cb=done_moving)
        logger.info('--> post-move request, moving=%s', pos.moving)
        time.sleep(2)
        # m2.move(1)

    put_complete_test()

if __name__ == '__main__':
    test()
