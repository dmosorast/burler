from unittest import TestCase
from burler.taps import Tap
from burler.streams import Stream

class TestStreamMetaClass(TestCase):
    def test_subclassing_stream_registers_with_tap(self):
        class TestStream(Stream):
            pass
        self.assertIn("test_stream", Tap.streams)
