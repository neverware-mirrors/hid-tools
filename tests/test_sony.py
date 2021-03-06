#!/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Benjamin Tissoires <benjamin.tissoires@gmail.com>
# Copyright (c) 2020 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from .test_gamepad import BaseTest
from hidtools.device.sony_gamepad import PS3Controller, PS4ControllerBluetooth, PS4ControllerUSB, PSTouchPoint

import libevdev
import logging
import pytest
logger = logging.getLogger('hidtools.test.sony')


class SonyBaseTest:
    class SonyTest(BaseTest.TestGamepad):
        pass

    class SonyPS4ControllerTest(SonyTest):
        def test_accelerometer(self):
            uhdev = self.uhdev
            evdev = uhdev.get_evdev("Accelerometer")

            for x in range(-32000, 32000, 4000):
                r = uhdev.event(accel=(x, None, None))
                events = uhdev.next_sync_events("Accelerometer")
                self.debug_reports(r, uhdev, events)

                assert libevdev.InputEvent(libevdev.EV_ABS.ABS_X) in events
                value = evdev.value[libevdev.EV_ABS.ABS_X]
                # Check against range due to small loss in precision due
                # to inverse calibration, followed by calibration by hid-sony.
                assert x - 1 <= value <= x + 1

            for y in range(-32000, 32000, 4000):
                r = uhdev.event(accel=(None, y, None))
                events = uhdev.next_sync_events("Accelerometer")
                self.debug_reports(r, uhdev, events)

                assert libevdev.InputEvent(libevdev.EV_ABS.ABS_Y) in events
                value = evdev.value[libevdev.EV_ABS.ABS_Y]
                assert y - 1 <= value <= y + 1

            for z in range(-32000, 32000, 4000):
                r = uhdev.event(accel=(None, None, z))
                events = uhdev.next_sync_events("Accelerometer")
                self.debug_reports(r, uhdev, events)

                assert libevdev.InputEvent(libevdev.EV_ABS.ABS_Z) in events
                value = evdev.value[libevdev.EV_ABS.ABS_Z]
                assert z - 1 <= value <= z + 1

        def test_gyroscope(self):
            uhdev = self.uhdev
            evdev = uhdev.get_evdev("Accelerometer")

            for rx in range(-2000000, 2000000, 200000):
                r = uhdev.event(gyro=(rx, None, None))
                events = uhdev.next_sync_events("Accelerometer")
                self.debug_reports(r, uhdev, events)

                assert libevdev.InputEvent(libevdev.EV_ABS.ABS_RX) in events
                value = evdev.value[libevdev.EV_ABS.ABS_RX]
                # Sensor internal value is 16-bit, but calibrated is 22-bit, so
                # 6-bit (64) difference, so allow a range of +/- 64.
                assert rx - 64 <= value <= rx + 64

            for ry in range(-2000000, 2000000, 200000):
                r = uhdev.event(gyro=(None, ry, None))
                events = uhdev.next_sync_events("Accelerometer")
                self.debug_reports(r, uhdev, events)

                assert libevdev.InputEvent(libevdev.EV_ABS.ABS_RY) in events
                value = evdev.value[libevdev.EV_ABS.ABS_RY]
                assert ry - 64 <= value <= ry + 64

            for rz in range(-2000000, 2000000, 200000):
                r = uhdev.event(gyro=(None, None, rz))
                events = uhdev.next_sync_events("Accelerometer")
                self.debug_reports(r, uhdev, events)

                assert libevdev.InputEvent(libevdev.EV_ABS.ABS_RZ) in events
                value = evdev.value[libevdev.EV_ABS.ABS_RZ]
                assert rz - 64 <= value <= rz + 64

        def test_mt_single_touch(self):
            """send a single touch in the first slot of the device,
            and release it."""
            uhdev = self.uhdev
            evdev = uhdev.get_evdev("Touch Pad")

            t0 = PSTouchPoint(1, 50, 100)
            r = uhdev.event(touch=[t0])
            events = uhdev.next_sync_events("Touch Pad")
            self.debug_reports(r, uhdev, events)

            assert libevdev.InputEvent(libevdev.EV_KEY.BTN_TOUCH, 1) in events
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == 0
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_POSITION_X] == 50
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_POSITION_Y] == 100

            t0.tipswitch = False
            r = uhdev.event(touch=[t0])
            events = uhdev.next_sync_events("Touch Pad")
            self.debug_reports(r, uhdev, events)
            assert libevdev.InputEvent(libevdev.EV_KEY.BTN_TOUCH, 0) in events
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == -1

        def test_mt_dual_touch(self):
            """Send 2 touches in the first 2 slots.
            Make sure the kernel sees this as a dual touch.
            Release and check

            Note: PTP will send here BTN_DOUBLETAP emulation"""
            uhdev = self.uhdev
            evdev = uhdev.get_evdev("Touch Pad")

            t0 = PSTouchPoint(1, 50, 100)
            t1 = PSTouchPoint(2, 150, 200)

            r = uhdev.event(touch=[t0])
            events = uhdev.next_sync_events("Touch Pad")
            self.debug_reports(r, uhdev, events)

            assert libevdev.InputEvent(libevdev.EV_KEY.BTN_TOUCH, 1) in events
            assert evdev.value[libevdev.EV_KEY.BTN_TOUCH] == 1
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == 0
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_POSITION_X] == 50
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_POSITION_Y] == 100
            assert evdev.slots[1][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == -1

            r = uhdev.event(touch=[t0, t1])
            events = uhdev.next_sync_events("Touch Pad")
            self.debug_reports(r, uhdev, events)
            assert libevdev.InputEvent(libevdev.EV_KEY.BTN_TOUCH) not in events
            assert evdev.value[libevdev.EV_KEY.BTN_TOUCH] == 1
            assert libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_POSITION_X, 5) not in events
            assert libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_POSITION_Y, 10) not in events
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == 0
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_POSITION_X] == 50
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_POSITION_Y] == 100
            assert evdev.slots[1][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == 1
            assert evdev.slots[1][libevdev.EV_ABS.ABS_MT_POSITION_X] == 150
            assert evdev.slots[1][libevdev.EV_ABS.ABS_MT_POSITION_Y] == 200

            t0.tipswitch = False
            r = uhdev.event(touch=[t0, t1])
            events = uhdev.next_sync_events("Touch Pad")
            self.debug_reports(r, uhdev, events)
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == -1
            assert evdev.slots[1][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == 1
            assert libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_POSITION_X) not in events
            assert libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_POSITION_Y) not in events

            t1.tipswitch = False
            r = uhdev.event(touch=[t1])

            events = uhdev.next_sync_events("Touch Pad")
            self.debug_reports(r, uhdev, events)
            assert evdev.slots[0][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == -1
            assert evdev.slots[1][libevdev.EV_ABS.ABS_MT_TRACKING_ID] == -1


class TestPS3Controller(SonyBaseTest.SonyTest):
    def create_device(self):
        return PS3Controller()

    @pytest.fixture(autouse=True)
    def start_controller(self):
        # emulate a 'PS' button press to tell the kernel we are ready to accept events
        self.assert_button(17)

        # drain any remaining udev events
        while self.uhdev.dispatch(10):
            pass

        def test_led(self):
            for k, v in self.uhdev.led_classes.items():
                # the kernel might have set a LED for us
                logger.info(f'{k}: {v.brightness}')

                idx = int(k[-1]) - 1
                assert self.uhdev.hw_leds.get_led(idx)[0] == bool(v.brightness)

                v.brightness = 0
                self.uhdev.dispatch(10)
                assert self.uhdev.hw_leds.get_led(idx)[0] is False

                v.brightness = v.max_brightness
                self.uhdev.dispatch(10)
                assert self.uhdev.hw_leds.get_led(idx)[0]


class TestPS4ControllerBluetooth(SonyBaseTest.SonyPS4ControllerTest):
    def create_device(self):
        return PS4ControllerBluetooth()


class TestPS4ControllerUSB(SonyBaseTest.SonyPS4ControllerTest):
    def create_device(self):
        return PS4ControllerUSB()
