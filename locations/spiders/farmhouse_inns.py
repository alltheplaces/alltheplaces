from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FarmhouseInnsSpider(SitemapSpider, StructuredDataSpider):
    name = "farmhouse_inns"
    item_attributes = {
        "brand": "Farmhouse Inns",
        "brand_wikidata": "Q105504972",
        "country": "GB",
    }
    sitemap_urls = ["https://www.farmhouseinns.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.farmhouseinns\.co\.uk\/pubs\/([-\w]+)\/([-\w]+)$", "parse_sd")]
    wanted_types = ["BarOrPub"]
