import scrapy

from locations.structured_data_spider import StructuredDataSpider


class AshleyFurnitureSpider(scrapy.spiders.SitemapSpider, StructuredDataSpider):
    name = "ashley_furniture"
    item_attributes = {"brand": "Ashley Furniture", "brand_wikidata": "Q4805437"}
    sitemap_urls = ["https://stores.ashleyfurniture.com/sitemap_index.xml"]
    sitemap_rules = [("/store/", "parse_sd")]
    drop_attributes = {"image"}
    wanted_types = ["FurnitureStore"]

