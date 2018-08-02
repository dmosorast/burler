from unittest import TestCase
from burler.taps import Tap
from burler.streams import Stream, stream
from burler.exceptions import DuplicateStream

class TestStreamMetaClass(TestCase):
    def test_subclassing_stream_registers_with_tap(self):
        class TestStream(Stream):
            pass
        self.assertIn("test_stream", Tap.streams)

    def test_subclassing_stream_twice_throws(self):
        with self.assertRaises(DuplicateStream):
            class TestStream(Stream):
                pass
            class test_stream(Stream):
                pass

    def test_duplicate_stream_resolution_example_does_not_throw(self):
        @stream("test_stream", tap_stream_id="invoices")
        @stream("test_stream", tap_stream_id="contacts")
        class TestStream():
            pass
        self.assertIn("invoices", Tap.streams)
        self.assertIn("contacts", Tap.streams)
