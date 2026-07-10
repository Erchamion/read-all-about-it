from pipeline.vetting import keyword_matches, score_paper, score_repo


def test_keyword_matches_is_case_insensitive():
    assert keyword_matches("New AI Model released", ["ai", "model"]) == ["ai", "model"]


def test_keyword_matches_requires_word_boundaries():
    # "ai" must not match inside "maintain"; "rag" not inside "storage".
    assert keyword_matches("we maintain storage", ["ai", "rag"]) == []


def test_keyword_matches_handles_multiword_and_empty():
    assert keyword_matches("Large Language Model agents", ["large language model"]) == [
        "large language model"
    ]
    assert keyword_matches(None, ["ai"]) == []
    assert keyword_matches("", ["ai"]) == []


def test_score_repo_combines_stars_and_matches():
    assert score_repo(0, []) == 0.0
    assert score_repo(255, ["agent", "llm"]) == 10.0  # log2(256)=8 + 2


def test_score_paper_counts_matches():
    assert score_paper([]) == 0.0
    assert score_paper(["llm", "agent", "reasoning"]) == 3.0
