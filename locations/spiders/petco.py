from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PetcoSpider(SitemapSpider, StructuredDataSpider):
    name = "petco"
    item_attributes = {"brand": "Petco", "brand_wikidata": "Q7171798"}
    sitemap_urls = ["https://stores.petco.com/sitemap.xml"]
    sitemap_rules = [(r"pet-supplies-(.+).html$", "parse_sd")]
    download_delay = 0.5
    drop_attributes = {"image"}
