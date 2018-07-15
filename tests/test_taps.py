from unittest import TestCase
from burler.taps import Tap
from burler.exceptions import ConfigValidationException

from datetime import datetime # For equivalent schema and voluptuous definitions
from schema import Schema as SSchema, And
from voluptuous import Schema as VSchema, Required, All, Length, Date

class TestTapConfigValidation(TestCase):
    list_config_spec = ['start_date', 'auth_key']
    dict_config_spec = {'start_date': 'doesn\'tmatter', 'auth_key': 'helloiamakey'}
    vconfig_spec = VSchema({Required('start_date'): Date(), Required('auth_key'): All(str, Length(min=32,max=32))})
    sconfig_spec = SSchema({'start_date': And(str, lambda s: datetime.strptime(s, '%Y-%m-%d')), 'auth_key': And(str, lambda s: len(s) == 32)})

    # List-based key inference usage
    def test_list_config_inferred_schema_succeeds_with_all_keys(self):
        tap = Tap(config_spec=self.list_config_spec)
        conf = {'start_date':'hi', 'auth_key': 'thisismykey'}
        expected_keys = set(['start_date','auth_key'])
        self.assertEqual(set(tap.validate_config(conf).keys()), expected_keys)

    def test_list_config_inferred_schema_fails_on_missing_key(self):
        tap = Tap(config_spec=self.list_config_spec)
        conf = {'start_date':'hi'}
        with self.assertRaises(ConfigValidationException):
            tap.validate_config(conf)

    def test_list_config_inferred_schema_succeeds_with_extra_keys(self):
        tap = Tap(config_spec=self.list_config_spec)
        conf = {'start_date':'hi', 'auth_key': 'thisismykey', 'page_size': 42}
        expected_keys = set(['start_date','auth_key','page_size'])
        self.assertEqual(set(tap.validate_config(conf).keys()), expected_keys)

    # Dict-based key inference usage
    def test_dict_config_inferred_schema_succeeds_with_all_keys(self):
        tap = Tap(config_spec=self.dict_config_spec)
        conf = {'start_date':'hi', 'auth_key': 'thisismykey'}
        expected_keys = set(['start_date','auth_key'])
        self.assertEqual(set(tap.validate_config(conf).keys()), expected_keys)

    def test_dict_config_inferred_schema_fails_on_missing_key(self):
        tap = Tap(config_spec=self.dict_config_spec)
        conf = {'start_date':'hi'}
        with self.assertRaises(ConfigValidationException):
            tap.validate_config(conf)

    def test_dict_config_inferred_schema_succeeds_with_extra_keys(self):
        tap = Tap(config_spec=self.dict_config_spec)
        conf = {'start_date':'hi', 'auth_key': 'thisismykey', 'page_size': 42}
        expected_keys = set(['start_date','auth_key','page_size'])
        self.assertEqual(set(tap.validate_config(conf).keys()), expected_keys)

    # Voluptuous usage
    def test_voluptuous_config_succeeds_with_all_keys(self):
        tap = Tap(config_spec=self.vconfig_spec)
        conf = {'start_date':'2015-03-14', 'auth_key': '0123456789abcdef0123456789abcdef'}
        expected_keys = set(['start_date','auth_key'])
        self.assertEqual(set(tap.validate_config(conf).keys()), expected_keys)

    def test_voluptuous_config_fails_on_missing_key(self):
        tap = Tap(config_spec=self.vconfig_spec)
        conf = {'start_date':'2015-03-14'}
        with self.assertRaises(ConfigValidationException):
            tap.validate_config(conf)

    # schema usage
    def test_schema_config_succeeds_with_all_keys(self):
        tap = Tap(config_spec=self.sconfig_spec)
        conf = {'start_date':'2015-03-14', 'auth_key': '0123456789abcdef0123456789abcdef'}
        expected_keys = set(['start_date','auth_key'])
        self.assertEqual(set(tap.validate_config(conf).keys()), expected_keys)

    def test_schema_config_fails_on_missing_key(self):
        tap = Tap(config_spec=self.sconfig_spec)
        conf = {'start_date':'2015-03-14'}
        with self.assertRaises(ConfigValidationException):
            tap.validate_config(conf)
