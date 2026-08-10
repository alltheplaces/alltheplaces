from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class ChefAndBrewerGBSpider(SitemapSpider, StructuredDataSpider):
    name = "chef_and_brewer_gb"
    item_attributes = {"brand": "Chef & Brewer", "brand_wikidata": "Q5089491"}
    sitemap_urls = ["https://www.chefandbrewer.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.chefandbrewer\.com\/pubs\/([-\w]+)\/([-\w]+)$", "parse_sd")]
    wanted_types = ["BarOrPub"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
