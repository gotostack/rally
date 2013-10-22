# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
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

import itertools
import random

from rally import exceptions
from rally import osclients
from rally import utils


class Scenario(object):
    """This is base class for any benchmark scenario.
       You should create subclass of this class. And you test scnerios will
       be autodiscoverd and you will be able to specify it in test config.
    """
    registred = False

    @staticmethod
    def register():
        if not Scenario.registred:
            utils.import_modules_from_package("rally.benchmark.scenarios")
            Scenario.registred = True

    @staticmethod
    def get_by_name(name):
        """Returns Scenario class by name."""
        for scenario in utils.itersubclasses(Scenario):
            if name == scenario.__name__:
                return scenario
        raise exceptions.NoSuchScenario(name=name)

    @staticmethod
    def list_benchmark_scenarios():
        """Lists all the existing methods in the benchmark scenario classes.

        Returns the method names in format <Class name>.<Method name>, which
        is used in the test config.

        :returns: List of strings
        """
        utils.import_modules_from_package("rally.benchmark.scenarios")
        benchmark_scenarios = [
            ["%s.%s" % (scenario.__name__, method)
             for method in dir(scenario) if not method.startswith("_")]
            for scenario in utils.itersubclasses(Scenario)
        ]
        benchmark_scenarios_flattened = list(itertools.chain.from_iterable(
                                                        benchmark_scenarios))
        return benchmark_scenarios_flattened

    @classmethod
    def class_init(cls, cloud_endpoints):
        # NOTE(msdubov): Creating here separate openstack clients for each of
        #                the temporary users involved in benchmarking.
        keys = ["username", "password", "tenant_name", "uri"]
        client_managers = [osclients.Clients(*[credentials[k] for k in keys])
                           for credentials in cloud_endpoints["temp_users"]]

        cls.cloud_endpoints = cloud_endpoints
        cls.clients = {
            "nova": [cl.get_nova_client() for cl in client_managers],
            "keystone": [cl.get_keystone_client() for cl in client_managers],
            "glance": [cl.get_glance_client() for cl in client_managers],
            "cinder": [cl.get_cinder_client() for cl in client_managers],
        }

    @classmethod
    def client(cls, client_type):
        """Return a client of the given type for a random tenant/user."""
        return random.choice(cls.clients[client_type])

    @classmethod
    def init(cls, config):
        """This method will be called with test config. It purpose is to
            prepare test enviorment. E.g. if you would like to test
            performance of assing of FloatingIps here you will create 200k
            FloatinigIps anre retun information about it to
        """
        return {}

    @classmethod
    def cleanup(cls, context):
        """This method will be called with context that was returned by init,
            after test scneario will be finished. And it should free all
            allocated resources.
        """
