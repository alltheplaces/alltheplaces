import re
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import scrapy
from scrapy.exceptions import UsageError

import locations.commands.sitemap as sitemap_mod
from locations.commands.sitemap import MySitemapSpider, SitemapCommand


@pytest.fixture(autouse=True)
def reset_class_state():
    MySitemapSpider.matched_patterns = {}
    MySitemapSpider.pages = False
    MySitemapSpider.requires_proxy = False
    MySitemapSpider.sitemap_urls = []
    yield
    MySitemapSpider.matched_patterns = {}
    MySitemapSpider.pages = False
    MySitemapSpider.requires_proxy = False
    MySitemapSpider.sitemap_urls = []


@pytest.fixture
def spider(monkeypatch):
    sp = MySitemapSpider()
    sp.sitemap_alternate_links = False
    sp._follow = [re.compile(".*")]
    sp.sitemap_filter = lambda s: s

    monkeypatch.setattr(
        MySitemapSpider,
        "_get_sitemap_body",
        lambda self, response: response.body,
        raising=True,
    )
    return sp


@pytest.mark.parametrize(
    "url,should_match",
    [
        ("https://example.com/store/123", True),
        ("https://example.com/about", False),
    ],
)
def test_extract_possible_store_counts(spider, url, should_match, monkeypatch):
    monkeypatch.setattr(
        MySitemapSpider,
        "common_sitemap_patterns",
        [r"/store/\d+$"],
        raising=False,
    )

    spider.extract_possible_store(url)

    if should_match:
        assert sum(spider.matched_patterns.values()) == 1
        assert len(spider.matched_patterns) == 1

        spider.extract_possible_store(url)
        assert len(spider.matched_patterns) == 1
        assert list(spider.matched_patterns.values())[0] == 2
    else:
        assert spider.matched_patterns == {}


def test_parse_sitemap_robots_yields_requests(monkeypatch, spider):
    monkeypatch.setattr(
        sitemap_mod,
        "sitemap_urls_from_robots",
        lambda text, base_url=None: ["https://site/s1.xml", "https://site/s2.xml"],
        raising=True,
    )

    req = scrapy.Request("https://site/robots.txt")
    resp = scrapy.http.TextResponse(
        url="https://site/robots.txt",
        request=req,
        body=b"Sitemap: https://site/s1.xml",
        encoding="utf-8",
    )

    out = list(spider._parse_sitemap(resp))
    assert len(out) == 2
    assert all(isinstance(req, scrapy.Request) for req in out)
    assert {req.url for req in out} == {"https://site/s1.xml", "https://site/s2.xml"}
    assert all(req.callback == spider._parse_sitemap for req in out)


def test_parse_sitemap_sitemapindex_follows(monkeypatch, spider):
    class FakeSitemap:
        def __init__(self, body):
            self.type = "sitemapindex"

    monkeypatch.setattr(sitemap_mod, "Sitemap", FakeSitemap, raising=True)
    monkeypatch.setattr(
        sitemap_mod,
        "iterloc",
        lambda it, alt_links: iter(["https://example.com/sm-keep.xml", "https://example.com/other.xml"]),
        raising=True,
    )

    req = scrapy.Request("https://site/sitemap.xml")
    resp = scrapy.http.TextResponse(url="https://site/sitemap.xml", request=req, body=b"<sitemapindex/>")

    spider._follow = [re.compile("keep")]

    out = list(spider._parse_sitemap(resp))
    assert len(out) == 1
    assert isinstance(out[0], scrapy.Request)
    assert out[0].url == "https://example.com/sm-keep.xml"
    assert out[0].callback == spider._parse_sitemap


def test_parse_sitemap_urlset_pages_true_triggers_extract(monkeypatch, spider, capsys):
    class FakeSitemap:
        def __init__(self, body):
            self.type = "urlset"

    monkeypatch.setattr(sitemap_mod, "Sitemap", FakeSitemap, raising=True)
    monkeypatch.setattr(
        sitemap_mod,
        "iterloc",
        lambda it, alt_links: iter(["https://example.com/store/999", "https://example.com/about"]),
        raising=True,
    )

    monkeypatch.setattr(
        MySitemapSpider,
        "common_sitemap_patterns",
        [r"/store/\d+$"],
        raising=False,
    )

    spider.pages = True
    req = scrapy.Request("https://site/sitemap.xml")
    resp = scrapy.http.TextResponse(url="https://site/sitemap.xml", request=req, body=b"<urlset/>")

    out = list(spider._parse_sitemap(resp))
    assert out == []

    assert len(spider.matched_patterns) == 1
    assert sum(spider.matched_patterns.values()) == 1

    captured = capsys.readouterr()
    assert "Possible patterns" in captured.out


def test_sitemap_command_run_happy_path_with_auto_robots(monkeypatch, capsys):
    cmd = SitemapCommand()

    fake_stats = MagicMock()
    fake_stats.get_stats.return_value = {"pages_crawled": 42}
    fake_crawler = SimpleNamespace(stats=fake_stats)
    cp = MagicMock()
    cp.create_crawler.return_value = fake_crawler
    cmd.crawler_process = cp

    opts = SimpleNamespace(
        requires_proxy=True,
        pages=True,
        stats=True,
        spargs={},
    )

    cmd.run(["https://example.com"], opts)

    assert MySitemapSpider.sitemap_urls == ["https://example.com/robots.txt"]
    assert MySitemapSpider.requires_proxy is True
    assert MySitemapSpider.pages is True

    cp.create_crawler.assert_called_once()
    cp.crawl.assert_called_once_with(fake_crawler)
    cp.start.assert_called_once()

    out = capsys.readouterr().out
    assert "pages_crawled: 42" in out


def test_sitemap_command_run_raises_on_missing_arg():
    cmd = SitemapCommand()
    opts = SimpleNamespace(requires_proxy=False, pages=False, stats=False, spargs={})
    with pytest.raises(UsageError):
        cmd.run([], opts)
