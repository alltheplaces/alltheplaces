from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RegalTheatersSpider(SitemapSpider, StructuredDataSpider):
    name = "regal_theaters"
    item_attributes = {"brand": "Regal Theaters", "brand_wikidata": "Q835638"}
    sitemap_urls = ["https://www.regmovies.com/sitemap.xml"]
    sitemap_rules = [("/theatres/", "parse_sd")]
    requires_proxy = True
    wanted_types = ["MovieTheater"]
