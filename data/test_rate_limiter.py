import time
from rate_limiter import TokenBucket

def test_token_bucket():
    bucket = TokenBucket(capacity=2, fill_rate=10.0)
    assert bucket.allow(1) is True
    assert bucket.allow(1) is True
    assert bucket.allow(1) is False
