import unittest
import sys
from types import SimpleNamespace
import json
from unittest import mock
from unittest.mock import mock_open
from io import StringIO
from ast import literal_eval
from main import influxdb_gen


NUM_MDADM_TESTS = 11


class MockSubprocess:
    PIPE = 0
    DEVNULL = 1

    def run(self, *args, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=b'{"Controllers": [{"Command Status": {"Misc": "Adapter #0 Smart Array", "Status": "Success"}}]}',
        )


sys.modules["subprocess"] = MockSubprocess()  # type: ignore
import megacli, ssacli, storcli, mdadm


class MockObject:
    def __init__(self, output) -> None:
        self.output = output

    def run(self, args: list):
        raise NotImplementedError

    def get_physical_disk_info(self):
        return self.output


class TestParsers(unittest.TestCase):
    maxDiff = None

    def test_megacli(self):
        with open("test-fixtures/megacli_output_1.txt") as f:
            output = f.read()
        with open("test-fixtures/megacli_parsed_1.txt") as f:
            expected = literal_eval(f.read())
        megacli.megacli = MockObject(output.encode())
        self.assertDictEqual(megacli.get_disk_errors(), expected)

    def test_storcli(self):
        with open("test-fixtures/storcli_output_1.txt") as f:
            output = f.read()
        with open("test-fixtures/storcli_parsed_1.txt") as f:
            expected = literal_eval(f.read())
        storcli.storcli = MockObject(json.loads(output))
        self.assertDictEqual(storcli.get_disk_errors(), expected)

    def test_ssacli(self):
        with open("test-fixtures/ssacli_output_1.txt") as f:
            output = f.read()
        with open("test-fixtures/ssacli_parsed_1.txt") as f:
            expected = literal_eval(f.read())
        ssacli.ssacli = MockObject(output.encode())
        self.assertDictEqual(ssacli.get_disk_errors(), expected)

    def test_mdadm(self):
        for i in range(1, NUM_MDADM_TESTS + 1):
            with open(f"test-fixtures/mdadm_output_{i}.txt") as f:
                output = f.read()
            with open(f"test-fixtures/mdadm_parsed_{i}.txt") as f:
                expected = literal_eval(f.read())
            with mock.patch("builtins.open", mock_open(read_data=output)):
                self.assertDictEqual(
                    mdadm.get_disk_errors(), expected, f"Mdadm Test {i}"
                )


def clear_stdout(mock_stdout: StringIO):
    mock_stdout.truncate(0)
    mock_stdout.seek(0)


class TestInfluxDBFormat(unittest.TestCase):
    maxDiff = None

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_megacli(self, mock_stdout: StringIO):
        with open("test-fixtures/megacli_parsed_1.txt") as f:
            parsed = literal_eval(f.read())
        with open("test-fixtures/megacli_result_1.txt") as f:
            expected = f.read()
        influxdb_gen(parsed)
        self.assertEqual(mock_stdout.getvalue(), expected)
        clear_stdout(mock_stdout)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_storcli(self, mock_stdout: StringIO):
        with open("test-fixtures/storcli_parsed_1.txt") as f:
            parsed = literal_eval(f.read())
        with open("test-fixtures/storcli_result_1.txt") as f:
            expected = f.read()
        influxdb_gen(parsed)
        self.assertEqual(mock_stdout.getvalue(), expected)
        clear_stdout(mock_stdout)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_ssacli(self, mock_stdout: StringIO):
        with open("test-fixtures/ssacli_parsed_1.txt") as f:
            parsed = literal_eval(f.read())
        with open("test-fixtures/ssacli_result_1.txt") as f:
            expected = f.read()
        influxdb_gen(parsed)
        self.assertEqual(mock_stdout.getvalue(), expected)
        clear_stdout(mock_stdout)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_mdadm(self, mock_stdout: StringIO):
        for i in range(1, NUM_MDADM_TESTS + 1):
            with open(f"test-fixtures/mdadm_parsed_{i}.txt") as f:
                parsed = literal_eval(f.read())
            with open(f"test-fixtures/mdadm_result_{i}.txt") as f:
                expected = f.read()
            influxdb_gen(parsed)
            self.assertEqual(mock_stdout.getvalue(), expected, f"Mdadm Test {i}")
            clear_stdout(mock_stdout)


if __name__ == "__main__":
    unittest.main()
