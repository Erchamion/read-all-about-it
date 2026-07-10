from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "pipeline" / "config.yaml"


def load():
    return yaml.safe_load(CONFIG_PATH.read_text())


def test_config_has_required_top_level_keys():
    config = load()
    assert config["news_lookback_days"] == 3
    assert "ai" in config["ai_keywords"]
    assert "llm" in config["research_keywords"]


def test_github_config_shape():
    github = load()["github"]
    assert github["new"]["min_stars"] == 15
    assert github["rising"]["min_stars"] == 200
    assert len(github["search_terms"]) >= 3
    assert "agent" in github["repo_keywords"]


def test_arxiv_config_shape():
    arxiv = load()["arxiv"]
    assert arxiv["categories"] == ["cs.AI", "cs.CL", "cs.LG"]
    assert arxiv["max_papers"] == 30


def test_news_sources_are_well_formed():
    for source in load()["news_sources"]:
        assert source["type"] in {"rss", "scrape"}
        assert source["url"].startswith("https://")
        if source["type"] == "scrape":
            assert "item_selector" in source and "base_url" in source
        else:
            assert isinstance(source.get("filter"), bool)
