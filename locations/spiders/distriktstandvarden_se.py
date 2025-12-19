from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
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

        if item["name"].startswith("Välkommen till specialistkliniken på "):
            item["branch"] = item["name"].removeprefix("Välkommen till specialistkliniken på ")
            item["name"] = "Distriktstandvården Specialistkliniken"
        elif item["name"].startswith("Välkommen till din tandläkare i "):
            item["branch"] = item.pop("name").removeprefix("Välkommen till din tandläkare i ")
        else:
            item["name"] = None

        apply_category(Categories.DENTIST, item)

        yield item
