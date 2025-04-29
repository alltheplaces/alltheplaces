from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TgiFridaysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "tgi_fridays_us"
    item_attributes = {"brand": "TGI Fridays", "brand_wikidata": "Q1524184"}
    sitemap_urls = ["https://locations.tgifridays.com/robots.txt"]
    sitemap_rules = [(r"locations\.tgifridays\.com/[a-z]{2}/[-\w]+/[-\w]+\.html$", "parse_sd")]
    drop_attributes = {"facebook", "twitter"}
