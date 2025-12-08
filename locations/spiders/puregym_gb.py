from urllib.parse import parse_qs, urlparse

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class PuregymGBSpider(CrawlSpider, StructuredDataSpider):
    name = "puregym_gb"
    item_attributes = {"brand": "PureGym", "brand_wikidata": "Q18345898", "country": "GB"}
    wanted_types = ["HealthClub"]
    start_urls = ["https://www.puregym.com/gyms/"]
    rules = [Rule(LinkExtractor(allow="/gyms/"), callback="parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["address"] = ld_data.get("location", {}).get("address")

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["image"] = None

        if img := response.xpath('//img[contains(@src, "tiles.stadiamaps.com")]/@src').get():
            q = parse_qs(urlparse(img)[4])
            if "center" in q:
                item["lat"], item["lon"] = q["center"][0].split(",", 1)

        yield item
