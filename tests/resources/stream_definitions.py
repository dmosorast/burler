from burler.streams import Stream, stream

@stream("test_stream", tap_stream_id="invoices")
@stream("test_stream", tap_stream_id="contacts")
class TestStream():
    pass
