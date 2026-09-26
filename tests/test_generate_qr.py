import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import qr_module.models as models


def setup_module(module):
    # isolate tests to a throwaway DB file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    models.DB_PATH = path
    models.init_db()


def test_add_and_get_item():
    models.add_item("ITM-TEST01", "Test Widget")
    item = models.get_item("ITM-TEST01")
    assert item is not None
    assert item["name"] == "Test Widget"
    assert item["status"] == "available"


def test_check_out_then_check_in():
    models.add_item("ITM-TEST02", "Test Gadget")

    out = models.record_scan("ITM-TEST02", "check_out", user="alice")
    assert out["status"] == "issued"
    assert out["issued_to"] == "alice"

    back = models.record_scan("ITM-TEST02", "check_in")
    assert back["status"] == "available"
    assert back["issued_to"] is None


def test_invalid_action_raises():
    models.add_item("ITM-TEST03", "Test Tool")
    try:
        models.record_scan("ITM-TEST03", "invalid_action")
        assert False, "expected ValueError"
    except ValueError:
        pass
