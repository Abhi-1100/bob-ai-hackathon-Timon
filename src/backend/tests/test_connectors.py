import asyncio
import json

from services.connectors import FileTailerConnector


def test_file_tailer_handles_partial_lines(tmp_path):
    path = tmp_path / "eve.json"
    path.write_text(json.dumps({"timestamp": "a"}) + "\n{" , encoding="utf-8")
    connector = FileTailerConnector(str(path))
    first = asyncio.run(connector.fetch())
    assert first == [{"timestamp": "a"}]
    with path.open("a", encoding="utf-8") as handle:
        handle.write('"timestamp": "b"}\n')
    second = asyncio.run(connector.fetch(connector.cursor))
    assert second == [{"timestamp": "b"}]
