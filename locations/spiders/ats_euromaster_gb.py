from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AtsEuromasterGBSpider(SitemapSpider, StructuredDataSpider):
    name = "ats_euromaster_gb"
    item_attributes = {"brand": "ATS Euromaster", "brand_wikidata": "Q4654920"}
    sitemap_urls = ["https://www.atseuromaster.co.uk/robots.txt"]
    sitemap_rules = [(r"/centres/[^/]+/[^/]+/[^/]+$", "parse")]
    wanted_types = ["AutoRepair"]
    time_format = "%H:%M:%S"

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
