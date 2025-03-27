import pytest
import json

from unittest.mock import patch

from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes

from ansible_collections.theko2fi.multipass.plugins.modules import multipass_config_get

class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass

class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass

def fake_fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)

def fake_exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)

@pytest.fixture
def mock_ansible_module(monkeypatch):
    monkeypatch.setattr(multipass_config_get.AnsibleModule, 'exit_json', fake_exit_json)
    monkeypatch.setattr(multipass_config_get.AnsibleModule, 'fail_json', fake_fail_json)

def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

@pytest.mark.parametrize(
    "testdata",
    [
        ({'key': 'local.driver'})
    ]
)
@patch("ansible_collections.theko2fi.multipass.plugins.module_utils.multipass.MultipassClientSDK.get", return_value = "hyperv")
def test_valid_config_key(mock_multipassclientsdk, mock_ansible_module, testdata):
    set_module_args(testdata)
    with pytest.raises(AnsibleExitJson) as exc_info:
        multipass_config_get.main()
    assert exc_info.type is AnsibleExitJson
    assert exc_info.value.args[0]['changed'] is False
    assert exc_info.value.args[0]['result'] == "hyperv"



@pytest.mark.parametrize(
    "testdata",
    [
        ({'key': 'yuutyui'})
    ]
)
@patch("ansible_collections.theko2fi.multipass.plugins.module_utils.multipass.MultipassClientSDK.get", side_effect = Exception("Key not found"))
def test_invalid_config_key(mock_multipassclientsdk, mock_ansible_module, testdata):
    set_module_args(testdata)
    with pytest.raises(AnsibleFailJson) as exc_info:
        multipass_config_get.main()
    assert "Key not found" in str(exc_info.value)