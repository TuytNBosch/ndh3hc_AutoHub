import os
import stat

import pytest

from autohub.services.common.file_access import write_block_reason


def test_writable_file_has_no_reason(tmp_path):
    file = tmp_path / "a.xlsx"
    file.write_bytes(b"x")
    assert write_block_reason(str(file)) == ""


def test_missing_file(tmp_path):
    assert "does not exist" in write_block_reason(str(tmp_path / "none.xlsx"))


def test_lock_file_is_reported(tmp_path):
    file = tmp_path / "a.xlsx"
    file.write_bytes(b"x")
    (tmp_path / "~$a.xlsx").write_bytes(b"x")
    assert "lock file" in write_block_reason(str(file))


@pytest.mark.skipif(os.name == "nt" or os.geteuid() == 0, reason="root ignores permissions")
def test_read_only_attribute(tmp_path):
    file = tmp_path / "a.xlsx"
    file.write_bytes(b"x")
    file.chmod(stat.S_IREAD)
    assert "Read-only" in write_block_reason(str(file))
