# Copyright 2020 The SODA Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from oslo_utils import importutils

from delfin import exception
from delfin.common import constants


class AlertHandlerTestCase(unittest.TestCase):
    ALERT_HANDLER_CLASS = 'delfin.drivers.huawei.oceanstor.alert_handler' \
                          '.AlertHandler'

    def _get_alert_handler(self):
        alert_handler_class = importutils.import_class(
            self.ALERT_HANDLER_CLASS)
        alert_handler = alert_handler_class()
        return alert_handler

    def _get_fake_alert_info(self):
        alert_info = {
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.2.0': 'location=location1',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.4.0': 'Trap Test Alarm',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.5.0': '2',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.6.0': '1',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.7.0': '4294967294',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.9.0': '4294967295',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.10.0': 'This is just for'
                                                   ' testing.Please '
                                                   'ignore it',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.11.0': '1',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.3.0': 'Sample advice',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.1.0': 'Array',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.8.0': '2020-6-25,1:42:26.0'
        }

        return alert_info

    def _get_fake_incomplete_alert_info(self):
        # hwIsmReportingAlarmFaultCategory is missing here
        alert_info = {
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.2.0': 'location=location1',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.4.0': 'Trap Test Alarm',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.5.0': '2',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.6.0': '1',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.7.0': '4294967294',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.9.0': '4294967295',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.10.0': 'This is just '
                                                   'for testing.'
                                                   'Please '
                                                   'ignore it',
            '1.3.6.1.4.1.2011.2.91.10.3.1.1.8': '2020-6-25,1:42:26.0'
        }

        return alert_info

    def _get_fake_queried_alert(self):
        alert_info = [{
            'eventID': 1234,
            'name': 'sample-event',
            'level': 2,
            'eventType': 0,
            'sequence': '1234',
            'startTime': 13200000,
            'description': 'This is just for  testing.Please ignore it',
            'suggestion': 'Sample advice',
            'location': 'location1'
        }]

        return alert_info

    def test_parse_alert_with_all_necessary_info(self):
        """ Success flow with all necessary parameters"""
        alert_handler_inst = self._get_alert_handler()
        alert = self._get_fake_alert_info()

        expected_alert_model = {
            'alert_id': alert['1.3.6.1.4.1.2011.2.91.10.3.1.1.7.0'],
            'alert_name': alert[
                '1.3.6.1.4.1.2011.2.91.10.3.1.1.4.0'],
            'severity': constants.Severity.CRITICAL,
            'category': constants.Category.FAULT,
            'type': constants.EventType.EQUIPMENT_ALARM,
            'sequence_number': alert['1.3.6.1.4.1.2011.2.91.10.3.1.1.9.0'],
            'description': alert[
                '1.3.6.1.4.1.2011.2.91.10.3.1.1.10.0'],
            'recovery_advice': alert['1.3.6.1.4.1.2011.2.91.10.3.1.1.3.0'],
            'resource_type': constants.DEFAULT_RESOURCE_TYPE,
            'location': 'Node code='
                        + alert['1.3.6.1.4.1.2011.2.91.10.3.1.1.1.0']
                        + ',' + alert['1.3.6.1.4.1.2011.2.91.10.3.1.1.2.0']
        }
        context = {}
        alert_model = alert_handler_inst.parse_alert(context, alert)
        # Equating occur_time so that complete model can be validated
        expected_alert_model['occur_time'] = alert_model['occur_time']

        # Verify that all other fields are matching
        self.assertDictEqual(expected_alert_model, alert_model)

    def test_parse_alert_without_mandatory_info(self):
        """ Error flow with some mandatory parameters missing"""
        alert_handler_inst = self._get_alert_handler()
        context = {}
        alert = self._get_fake_incomplete_alert_info()
        self.assertRaisesRegex(exception.InvalidInput,
                               "Mandatory information "
                               "hwIsmReportingAlarmNodeCode missing in alert "
                               "message.",
                               alert_handler_inst.parse_alert, context, alert)

    def test_parse_queried_alerts_inside_range(self):
        """ Success flow with all necessary parameters"""
        alert_handler_inst = self._get_alert_handler()
        alert = self._get_fake_queried_alert()

        expected_alert_model = [{
            'alert_id': alert[0]['eventID'],
            'alert_name': alert[0]['name'],
            'severity': constants.Severity.INFORMATIONAL,
            'category': constants.Category.EVENT,
            'type': constants.EventType.NOT_SPECIFIED,
            'sequence_number': alert[0]['sequence'],
            'description': alert[0]['description'],
            'recovery_advice': alert[0]['suggestion'],
            'resource_type': constants.DEFAULT_RESOURCE_TYPE,
            'location': alert[0]['location'],
            'occur_time': alert[0]['startTime'] * 1000
        }]

        # With both valid begin_time and end_time
        query_para = {'begin_time': 13100000, 'end_time': 13300000}
        alert_model = alert_handler_inst.parse_queried_alerts(alert,
                                                              query_para)
        # Verify that all other fields are matching
        self.assertDictEqual(expected_alert_model[0], alert_model[0])

        # With only valid begin_time
        query_para = {'begin_time': 13100000}
        alert_model = alert_handler_inst.parse_queried_alerts(alert,
                                                              query_para)
        # Verify that all other fields are matching
        self.assertDictEqual(expected_alert_model[0], alert_model[0])

        # With only valid end_time
        query_para = {'end_time': 13300000}
        alert_model = alert_handler_inst.parse_queried_alerts(alert,
                                                              query_para)
        # Verify that all other fields are matching
        self.assertDictEqual(expected_alert_model[0], alert_model[0])

    def test_parse_queried_alerts_outside_range(self):
        """ Success flow with all necessary parameters"""
        alert_handler_inst = self._get_alert_handler()
        alert = self._get_fake_queried_alert()

        query_para = {'begin_time': 13300000, 'end_time': 13400000}
        alert_model = alert_handler_inst.parse_queried_alerts(alert,
                                                              query_para)

        # Verify that when input alert is out of begin and end time,
        # it is skipped
        self.assertEqual(len(alert_model), 0)
