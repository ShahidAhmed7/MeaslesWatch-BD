from hashlib import sha256

import pytest

from measleswatch.ingest import data_contract_sha256, load_config, verify_study_contract


OLD = b'country = "Bangladesh"\n[modal]\nmax_new_tokens = 128\n[pilot]\nuser_message = "old"\n'
NEW = b'country = "Bangladesh"\n[modal]\nmax_new_tokens = 4096\n[pilot]\nuser_message = "new"\n'


def legacy_project(tmp_path):
    settings = tmp_path / "study.toml"
    settings.write_bytes(NEW)
    original_hash = sha256(OLD).hexdigest()
    directory = tmp_path / "study_snapshots"
    directory.mkdir()
    archive = directory / f"{original_hash}.toml"
    archive.write_bytes(OLD)
    return settings, archive, {"config_sha256": original_hash}


def test_runtime_only_change_keeps_legacy_data_contract(tmp_path):
    settings, archive, manifest = legacy_project(tmp_path)
    expected = data_contract_sha256(load_config(archive))
    assert verify_study_contract(settings, manifest) == expected
    assert data_contract_sha256(load_config(settings)) == expected


def test_changed_scientific_contract_is_rejected(tmp_path):
    settings, _, manifest = legacy_project(tmp_path)
    settings.write_bytes(NEW.replace(b"Bangladesh", b"Bhutan"))
    with pytest.raises(ValueError, match="data contract differs"):
        verify_study_contract(settings, manifest)


def test_corrupted_or_missing_archive_is_not_trusted(tmp_path):
    settings, archive, manifest = legacy_project(tmp_path)
    archive.write_bytes(OLD + b"\n")
    with pytest.raises(ValueError, match="hash-matching study snapshot"):
        verify_study_contract(settings, manifest)
    with pytest.raises(ValueError, match="hash-matching study snapshot"):
        verify_study_contract(settings, {"config_sha256": "0" * 64})


def test_new_manifest_uses_data_contract_digest(tmp_path):
    settings, _, _ = legacy_project(tmp_path)
    manifest = {"data_contract_sha256": data_contract_sha256(load_config(settings))}
    assert verify_study_contract(settings, manifest) == manifest["data_contract_sha256"]
    settings.write_bytes(NEW.replace(b"Bangladesh", b"Bhutan"))
    with pytest.raises(ValueError, match="data contract differs"):
        verify_study_contract(settings, manifest)
