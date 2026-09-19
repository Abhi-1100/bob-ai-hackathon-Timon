from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routers.upload import _validate_external_url

@pytest.mark.parametrize("url", ["ftp://example.com/feed", "http://localhost:8000", "http://127.0.0.1", "http://10.0.0.1", "http://192.168.1.1"])
def test_rejects_non_public_or_unsupported_urls(url):
    with pytest.raises(ValueError): _validate_external_url(url)
