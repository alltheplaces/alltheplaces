from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SubwaySpider(SitemapSpider, StructuredDataSpider):
    name = "subway"
    item_attributes = {"brand": "Subway", "brand_wikidata": "Q244457"}
    allowed_domains = ["restaurants.subway.com"]
    sitemap_urls = ["https://restaurants.subway.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    drop_attributes = {"image"}

    def pre_process_data(self, ld_data, **kwargs):
        if isinstance(ld_data["name"], list):
            # We actually want the second name in the Microdata
            ld_data["name"] = ld_data["name"][-1]
