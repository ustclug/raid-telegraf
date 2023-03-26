import unittest
import sys
from types import SimpleNamespace
import json
from unittest import mock
from io import StringIO
from ast import literal_eval
from main import influxdb_gen


class MockSubprocess:
    PIPE = 0

    def run(self, *args, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=b'{"Controllers": [{"Command Status": {"Misc": "Adapter #0 Smart Array", "Status": "Success"}}]}',
        )


sys.modules["subprocess"] = MockSubprocess()
import megacli, ssacli, storcli


class MockObject:
    def __init__(self, output) -> None:
        self.output = output

    def run(self, args: list):
        raise NotImplementedError

    def get_physical_disk_info(self):
        return self.output


class TestParsers(unittest.TestCase):
    def test_megacli_1(self):
        with open("test-fixtures/megacli_output_1.txt") as f:
            output = f.read()
        with open("test-fixtures/megacli_parsed_1.txt") as f:
            expected = literal_eval(f.read())
        megacli.megacli = MockObject(output.encode())
        self.assertDictEqual(megacli.get_disk_errors(), expected)

    def test_storcli_1(self):
        with open("test-fixtures/storcli_output_1.txt") as f:
            output = f.read()
        with open("test-fixtures/storcli_parsed_1.txt") as f:
            expected = literal_eval(f.read())
        storcli.storcli = MockObject(json.loads(output))
        self.assertDictEqual(storcli.get_disk_errors(), expected)

    def test_ssacli_1(self):
        with open("test-fixtures/ssacli_output_1.txt") as f:
            output = f.read()
        with open("test-fixtures/ssacli_parsed_1.txt") as f:
            expected = literal_eval(f.read())
        ssacli.ssacli = MockObject(output.encode())
        self.assertDictEqual(ssacli.get_disk_errors(), expected)


class TestInfluxDBFormat(unittest.TestCase):
    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_megacli_1(self, mock_stdout: StringIO):
        with open("test-fixtures/megacli_parsed_1.txt") as f:
            parsed = literal_eval(f.read())
        with open("test-fixtures/megacli_result_1.txt") as f:
            expected = f.read()
        influxdb_gen(parsed)
        self.assertEqual(mock_stdout.getvalue(), expected)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_storcli_1(self, mock_stdout: StringIO):
        with open("test-fixtures/storcli_parsed_1.txt") as f:
            parsed = literal_eval(f.read())
        with open("test-fixtures/storcli_result_1.txt") as f:
            expected = f.read()
        influxdb_gen(parsed)
        self.assertEqual(mock_stdout.getvalue(), expected)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_ssacli_1(self, mock_stdout: StringIO):
        with open("test-fixtures/ssacli_parsed_1.txt") as f:
            parsed = literal_eval(f.read())
        with open("test-fixtures/ssacli_result_1.txt") as f:
            expected = f.read()
        influxdb_gen(parsed)
        self.assertEqual(mock_stdout.getvalue(), expected)


if __name__ == "__main__":
    unittest.main()
