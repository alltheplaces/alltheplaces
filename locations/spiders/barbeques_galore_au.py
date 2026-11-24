import json

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.json_blob_spider import JSONBlobSpider


class BarbequesGaloreAUSpider(JSONBlobSpider):
    name = "barbeques_galore_au"
    item_attributes = {"brand": "Barbeques Galore", "brand_wikidata": "Q4859570"}
    start_urls = ["https://www.barbequesgalore.com.au/pages/store-locator"]

    def parse(self, response: TextResponse):
        json_data = json.loads(response.xpath('//script[contains(text(),"suburb")]/text()').get())
        for location in json_data:
            item = DictParser.parse(location)
            item["website"] = item["ref"] = response.urljoin(item["website"])
            item["branch"] = item.pop("name")
            apply_category(Categories.SHOP_BBQ, item)
            yield item
