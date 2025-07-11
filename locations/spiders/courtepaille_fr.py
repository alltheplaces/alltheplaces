import json

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CourtepailleFRSpider(JSONBlobSpider):
    name = "courtepaille_fr"
    item_attributes = {"brand": "Courtepaille", "brand_wikidata": "Q3116688"}
    start_urls = ["https://www.courtepaille.com/restaurant/"]

    def extract_json(self, response: Response) -> list[dict]:
        return json.loads(response.xpath("//@data-restaurants-json").get())

    def post_process_item(self, item: Feature, response: Response, feature: dict):
        raw_text = Selector(text=feature["popup"])
        item["branch"] = raw_text.xpath("//h3/text()").get().removeprefix("Courtepaille ")
        item["addr_full"] = raw_text.xpath('//*[@class="card__address"]').xpath("normalize-space()").get()
        item["phone"] = raw_text.xpath('//*[@class="card__phone"]/text()').get()
        item["website"] = raw_text.xpath("//@href").get()
        apply_category(Categories.RESTAURANT, item)
        yield item
