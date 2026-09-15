from app.normalize import content_hash, detect_platform, normalize_url, relative_time


def test_normalize_url_strips_tracking_and_www():
    url = "https://WWW.Upwork.com/freelance-jobs/apply/AI/?utm_source=x&fbclid=1&q=keep"
    assert normalize_url(url) == "https://upwork.com/freelance-jobs/apply/AI?q=keep"


def test_normalize_url_trailing_slash():
    assert normalize_url("https://linkedin.com/posts/abc/") == "https://linkedin.com/posts/abc"


def test_detect_platform():
    assert detect_platform("https://www.upwork.com/jobs/x") == "Upwork"
    assert detect_platform("https://www.freelancer.com/projects/x") == "Freelancer"
    assert detect_platform("https://www.linkedin.com/posts/x") == "LinkedIn"


def test_content_hash_stable_and_case_insensitive_title():
    a = content_hash("https://x.com/a", "Hello", "World")
    b = content_hash("https://x.com/a/", "HELLO", "world")
    assert a == b
    assert a != content_hash("https://x.com/b", "Hello", "World")


def test_relative_time_passthrough_ago():
    assert relative_time("2h ago") == "2h ago"
