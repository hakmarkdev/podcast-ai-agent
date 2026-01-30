from pathlib import Path
from src.utils import sanitize_filename, check_disk_space, estimate_ram_requirement

def test_sanitize_filename():
    assert sanitize_filename("test.mp3") == "test.mp3"
    assert sanitize_filename("test/file.mp3") == "test_file.mp3"
    assert sanitize_filename("test\\file.mp3") == "test_file.mp3"
    assert sanitize_filename('test"file".mp3') == "test_file_.mp3"
    assert sanitize_filename("..test..") == "test"

def test_check_disk_space(tmp_path):
    assert check_disk_space(tmp_path, 0.001) == True
    assert check_disk_space(tmp_path, 1e9) == False

def test_ram_estimation():
    assert estimate_ram_requirement("tiny") == 200
    assert estimate_ram_requirement("large-v3") == 8000
    assert estimate_ram_requirement("invalid") == 1000
