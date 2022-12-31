from google.protobuf import timestamp_pb2


def timestamp_now() -> timestamp_pb2.Timestamp:
    now = timestamp_pb2.Timestamp()
    now.GetCurrentTime()
    return now
