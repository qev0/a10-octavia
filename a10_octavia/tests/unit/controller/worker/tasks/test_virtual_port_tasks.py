#    Copyright 2020, A10 Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import imp
try:
    from unittest import mock
except ImportError:
    import mock

from octavia.common import data_models as o_data_models

from oslo_config import cfg
from oslo_config import fixture as oslo_fixture

from a10_octavia.common import config_options
from a10_octavia.common import data_models
from a10_octavia.controller.worker.tasks import virtual_port_tasks as task
from a10_octavia.tests.common import a10constants
from a10_octavia.tests.unit import base

VTHUNDER = data_models.VThunder()
LB = o_data_models.LoadBalancer(id=a10constants.MOCK_LOAD_BALANCER_ID)


class TestHandlerVirtualPortTasks(base.BaseTaskTestCase):

    def setUp(self):
        super(TestHandlerVirtualPortTasks, self).setUp()
        imp.reload(task)
        self.client_mock = mock.Mock()
        self.conf = self.useFixture(oslo_fixture.Config(cfg.CONF))
        self.conf.register_opts(config_options.A10_LISTENER_OPTS,
                                group=a10constants.LISTENER_CONF_SECTION)
        self.conf.register_opts(config_options.A10_GLOBAL_OPTS,
                                group=a10constants.A10_GLOBAL_CONF_SECTION)

    def tearDown(self):
        super(TestHandlerVirtualPortTasks, self).tearDown()
        self.conf.reset()

    def _mock_listener(self, protocol, conn_limit):
        listener = o_data_models.Listener(id=a10constants.MOCK_LISTENER_ID)
        listener.protocol = protocol
        listener.connection_limit = conn_limit
        return listener

    def _create_shared_template(self, template_type, template_config,
                                mock_protocol, mock_templates):
        template_type = template_type.lower()
        mock_templates.return_value = 'template-{}-shared'.format(template_type)
        listener = self._mock_listener(template_type.upper(), 1000)
        mock_protocol.return_value = listener.protocol

        listener_task = task.ListenerCreate()
        listener_task.axapi_client = self.client_mock
        self.conf.config(group=a10constants.A10_GLOBAL_CONF_SECTION,
                         use_shared_for_template_lookup=True)
        self.conf.config(group=a10constants.LISTENER_CONF_SECTION, **template_config)
        listener_task.CONF = self.conf

        device_templates = {"template": {
            "{}-list".format(template_type): [{
                template_type: {"name": list(template_config.values())[0]}
            }]
        }
        }
        listener_task.axapi_client.slb.template.templates.get.return_value = device_templates
        return listener_task, listener

    @mock.patch('a10_octavia.controller.worker.tasks.utils.shared_template_modifier')
    @mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol')
    def test_create_listener_with_template_http_shared(self, mock_protocol, mock_templates):
        vthunder = copy.deepcopy(VTHUNDER)
        vthunder.partition_name = "my_partition"
        listener_task, listener = self._create_shared_template(
            'http', {'template_http': 'temp1'}, mock_protocol, mock_templates)
        listener_task.execute(LB, listener, vthunder)
        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('template-http-shared', kwargs['virtual_port_templates'])

    @mock.patch('a10_octavia.controller.worker.tasks.utils.shared_template_modifier')
    @mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol')
    def test_create_listener_with_template_tcp_shared(self, mock_protocol, mock_templates):
        vthunder = copy.deepcopy(VTHUNDER)
        vthunder.partition_name = "my_partition"
        listener_task, listener = self._create_shared_template(
            'tcp', {'template_tcp': 'temp1'}, mock_protocol, mock_templates)
        listener_task.execute(LB, listener, vthunder)
        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('template-tcp-shared', kwargs['virtual_port_templates'])

    @mock.patch('a10_octavia.controller.worker.tasks.utils.shared_template_modifier')
    @mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol')
    def test_create_listener_with_template_policy_shared(self, mock_protocol, mock_templates):
        vthunder = copy.deepcopy(VTHUNDER)
        vthunder.partition_name = "my_partition"
        listener_task, listener = self._create_shared_template(
            'policy', {'template_policy': 'temp1'}, mock_protocol, mock_templates)
        listener_task.execute(LB, listener, vthunder)
        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('template-policy-shared', kwargs['virtual_port_templates'])

    @mock.patch('a10_octavia.controller.worker.tasks.utils.shared_template_modifier')
    @mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol')
    def test_create_listener_with_template_virtual_port_shared(self, mock_protocol, mock_templates):
        vthunder = copy.deepcopy(VTHUNDER)
        vthunder.partition_name = "my_partition"
        listener_task, listener = self._create_shared_template(
            'virtual-port', {'template_virtual_port': 'temp1'}, mock_protocol, mock_templates)
        listener_task.execute(LB, listener, vthunder)
        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('template-virtual-port-shared', kwargs['virtual_port_templates'])

    @mock.patch('a10_octavia.controller.worker.tasks.utils.shared_template_modifier')
    @mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol')
    def test_create_listener_with_template_http(self, mock_protocol, mock_templates):
        vthunder = copy.deepcopy(VTHUNDER)
        vthunder.partition_name = "shared"
        listener_task, listener = self._create_shared_template(
            'http', {'template_http': 'temp1'}, mock_protocol, mock_templates)
        listener_task.execute(LB, listener, vthunder)
        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('template-http', kwargs['virtual_port_templates'])

    @mock.patch('a10_octavia.controller.worker.tasks.utils.shared_template_modifier')
    @mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol')
    def test_create_listener_with_template_tcp(self, mock_protocol, mock_templates):
        vthunder = copy.deepcopy(VTHUNDER)
        vthunder.partition_name = "shared"
        listener_task, listener = self._create_shared_template(
            'tcp', {'template_tcp': 'temp1'}, mock_protocol, mock_templates)
        listener_task.execute(LB, listener, vthunder)
        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('template-tcp', kwargs['virtual_port_templates'])

    @mock.patch('a10_octavia.controller.worker.tasks.utils.shared_template_modifier')
    @mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol')
    def test_create_listener_with_template_policy(self, mock_protocol, mock_templates):
        vthunder = copy.deepcopy(VTHUNDER)
        vthunder.partition_name = "shared"
        listener_task, listener = self._create_shared_template(
            'policy', {'template_policy': 'temp1'}, mock_protocol, mock_templates)
        listener_task.execute(LB, listener, vthunder)
        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('template-policy', kwargs['virtual_port_templates'])

    @mock.patch('a10_octavia.controller.worker.tasks.utils.shared_template_modifier')
    @mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol')
    def test_create_listener_with_template_virtual_port(self, mock_protocol, mock_templates):
        vthunder = copy.deepcopy(VTHUNDER)
        vthunder.partition_name = "shared"
        listener_task, listener = self._create_shared_template(
            'virtual-port', {'template_virtual_port': 'temp1'}, mock_protocol, mock_templates)
        listener_task.execute(LB, listener, vthunder)
        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('template-virtual-port', kwargs['virtual_port_templates'])

    def test_create_http_virtual_port_use_rcv_hop(self):
        listener = self._mock_listener('HTTP', 1000)

        listener_task = task.ListenerCreate()
        listener_task.axapi_client = self.client_mock
        self.conf.config(group=a10constants.LISTENER_CONF_SECTION,
                         use_rcv_hop_for_resp=True)
        listener_task.CONF = self.conf

        with mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol',
                        return_value=listener.protocol):
            listener_task.execute(LB, listener, VTHUNDER)

        args, kwargs = self.client_mock.slb.virtual_server.vport.create.call_args
        self.assertIn('use_rcv_hop', kwargs)
        self.assertTrue(kwargs.get('use_rcv_hop'))

    def test_update_http_virtual_port_use_rcv_hop(self):
        listener = self._mock_listener('HTTP', 1000)

        listener_task = task.ListenerUpdate()
        listener_task.axapi_client = self.client_mock
        self.conf.config(group=a10constants.LISTENER_CONF_SECTION,
                         use_rcv_hop_for_resp=False)
        listener_task.CONF = self.conf

        with mock.patch('a10_octavia.common.openstack_mappings.virtual_port_protocol',
                        return_value=listener.protocol):
            listener_task.execute(LB, listener, VTHUNDER)

        args, kwargs = self.client_mock.slb.virtual_server.vport.update.call_args
        self.assertIn('use_rcv_hop', kwargs)
        self.assertFalse(kwargs.get('use_rcv_hop'))
