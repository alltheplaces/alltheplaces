import json

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class FogoDeChaoSpider(Spider):
    name = "fogo_de_chao"
    item_attributes = {"brand": "Fogo de Chão", "brand_wikidata": "Q5464133"}
    start_urls = ["https://fogodechao.com/locations/"]
    skip_auto_cc_spider_name = True  # Brazil, not Germany...

    def parse(self, response):
        script = response.xpath("//script[starts-with(text(), 'locationsData =')]/text()").get()
        locations_data = json.loads(script[script.find("{") : script.rfind("}") + 1])

        for ref, location in locations_data.items():
            if location["coming_soon_url"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = ref
            item["addr_full"] = merge_address_lines([location["address1"], location["address2"]])
            item["branch"] = item.pop("name")
            item["state"] = location["state"]
            item["website"] = response.urljoin(location["url"])
            yield item
