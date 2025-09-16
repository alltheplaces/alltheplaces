from scrapy import Spider
from scrapy.utils.spider import DefaultSpider
from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.clean_strings import CleanStringsPipeline, clean_string


def get_spider() -> Spider:
    spider = DefaultSpider()
    spider.crawler = get_crawler()
    return spider


def test_clean_strings_pipeline():
    pipeline = CleanStringsPipeline()

    item = Feature(
        ref="  https://example.com/12345   ",
        name="test",
        addr_full="test str 123",
        phone="1234567890",
        website="  https://example.com/12345/ ",
        image="  https://example.example.net/image.jpg  ",
        brand="McDonald's",
        brand_wikidata="Q38076",
    )
    spider = get_spider()
    pipeline.process_item(item, spider)
    assert item["ref"] == "https://example.com/12345"
    assert item["name"] == "test"
    assert item["addr_full"] == "test str 123"
    assert item["phone"] == "1234567890"
    assert item["website"] == "https://example.com/12345/"
    assert item["image"] == "https://example.example.net/image.jpg"
    assert item["brand"] == "McDonald's"
    assert item["brand_wikidata"] == "Q38076"
    assert not spider.crawler.stats.get_value("atp/clean_strings/name")
    assert not spider.crawler.stats.get_value("atp/clean_strings/addr_full")
    assert not spider.crawler.stats.get_value("atp/clean_strings/phone")
    assert not spider.crawler.stats.get_value("atp/clean_strings/brand")
    assert not spider.crawler.stats.get_value("atp/clean_strings/brand_wikidata")

    item = Feature(
        name="&nbsp;test &amp; test  ",
        addr_full="  &nbsp;test str 123&nbsp;  ",
        phone="  &nbsp;1234567890&nbsp;  ",
        website="https://example.com?query=title%20EQ%20'%3CMytitle%3E&amp;test'%20",
    )
    spider = get_spider()
    pipeline.process_item(item, spider)
    assert item["name"] == "test & test"
    assert item["addr_full"] == "test str 123"
    assert item["phone"] == "1234567890"
    assert (
        item["website"] == "https://example.com?query=title%20EQ%20'%3CMytitle%3E&amp;test'%20"
    )  # URL should not be unescaped
    assert spider.crawler.stats.get_value("atp/clean_strings/name")
    assert spider.crawler.stats.get_value("atp/clean_strings/addr_full")
    assert spider.crawler.stats.get_value("atp/clean_strings/phone")


def test_clean_strings_function():
    cases = [
        ("", ""),
        ("     ", ""),
        ("&amp; &lt; &gt;", "& < >"),
        ("   Hello World   ", "Hello World"),
        ("CleanString", "CleanString"),
        ("Hello&nbsp;World", "Hello World"),
        ("&quot;Quoted Text&quot;", '"Quoted Text"'),
        ("   &nbsp;Test&nbsp;String&nbsp;   ", "Test\xa0String"),
        ("   &lt;div&gt;Content&lt;/div&gt;   ", "<div>Content</div>"),
        ("Classic Digital Studio & Mp Onl;Ine", "Classic Digital Studio & Mp Onl;Ine"),
        ("Piccola Societa&apos;cooperativa", "Piccola Societa'cooperativa"),
        ("McDonald&#39;s Sacav&#233;m", "McDonald's Sacavém"),
        ("Wind &amp; Tide Bookshop", "Wind & Tide Bookshop"),
        ("RIBEIRÃO DAS NEVES &#8211; MENEZES", "RIBEIRÃO DAS NEVES – MENEZES"),
        ("IMAGE &AMP VISION", "IMAGE & VISION"),
        ("Antoine At Cut &Amp; Style", "Antoine At Cut &Amp; Style"),  # html.unescape is not able to handle &Amp;
    ]
    for input, expected in cases:
        assert clean_string(input) == expected
