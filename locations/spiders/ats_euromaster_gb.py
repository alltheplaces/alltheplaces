from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AtsEuromasterGBSpider(CrawlSpider, StructuredDataSpider):
    name = "ats_euromaster_gb"
    item_attributes = {"brand": "ATS Euromaster", "brand_wikidata": "Q4654920"}
    start_urls = ["https://www.atseuromaster.co.uk/centres"]
    rules = [
        Rule(LinkExtractor(allow="/centres/[^/]+$")),
        Rule(LinkExtractor(allow=r"/centres/[^/]+/[^/]+$")),
        Rule(LinkExtractor(allow=r"/centres/[^/]+/[^/]+/[^/]+$"), callback="parse_sd"),
    ]
    wanted_types = ["AutoRepair"]
    time_format = "%H:%M:%S"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["facebook"] = None
        item["branch"] = item.pop("name")
        item["website"] = response.url

        item["ref"] = response.xpath('//*[@class="model-dealer-infos"]/@data-id').get()
        item["state"] = response.xpath('//*[@class="model-dealer-infos"]/@data-region').get()
        item["extras"]["ref:google:place_id"] = response.xpath(
            '//*[@class="model-dealer-infos"]/@data-google-map-place-id'
        ).get()

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
