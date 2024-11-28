from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FarmhouseInnsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "farmhouse_inns_gb"
    item_attributes = {"brand": "Farmhouse Inns", "brand_wikidata": "Q105504972"}
    sitemap_urls = ["https://www.farmhouseinns.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/pubs/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["BarOrPub"]
