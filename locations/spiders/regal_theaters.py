from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class RegalTheatersSpider(SitemapSpider, StructuredDataSpider):
    name = "regal_theaters"
    item_attributes = {"brand": "Regal Theaters", "brand_wikidata": "Q835638"}
    sitemap_urls = ["https://www.regmovies.com/sitemap.xml"]
    sitemap_rules = [("/theatres/", "parse_sd")]
    user_agent = BROWSER_DEFAULT
