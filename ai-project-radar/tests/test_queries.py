from app.search.queries import EXTRA_QUERIES, SITE_TEMPLATES, generate_queries, select_queries


def test_generate_queries_includes_site_specific_templates():
    queries = generate_queries()
    joined = "\n".join(queries)
    assert "site:upwork.com/freelance-jobs" in joined
    assert "site:freelancer.com/projects" in joined
    assert 'site:linkedin.com/posts "looking for"' in joined
    assert "site:linkedin.com/jobs" in joined
    assert "AI automation" in joined
    assert "n8n" in joined
    assert "implementation partner" in joined
    for extra in EXTRA_QUERIES:
        assert extra in queries
    assert len(queries) == len(set(queries))
    assert len(queries) > len(SITE_TEMPLATES)


def test_select_queries_rotates_but_keeps_size():
    queries = generate_queries()
    first = select_queries(queries, 12)
    second = select_queries(queries, 12)
    assert len(first) == 12
    assert first == second
    assert select_queries(queries, 0) == queries
    assert select_queries(["a", "b"], 10) == ["a", "b"]
