from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DistriktstandvardenSESpider(SitemapSpider, StructuredDataSpider):
    name = "distriktstandvarden_se"
    item_attributes = {"brand": "Distriktstandvården", "brand_wikidata": "Q10474535"}
    sitemap_urls = ["https://distriktstandvarden.se/dtv_clinic-sitemap.xml"]
    sitemap_rules = [(r"distriktstandvarden\.se/(?!mobil-)([^/]+)/", "parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if coords := response.xpath('//img[@class="clinic-static-map"]/@src').re(
            r"png%7C(-?\d+\.\d+)%2C(-?\d+\.\d+)%26style"
        ):
            item["lat"], item["lon"] = coords
        yield item
