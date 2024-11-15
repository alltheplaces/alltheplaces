import json
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.items import Feature


class Fitness19USSpider(CrawlSpider):
    name = "fitness19_us"
    item_attributes = {"brand": "Fitness 19", "brand_wikidata": "Q121787953", "extras": Categories.GYM.value}
    start_urls = ["https://www.fitness19.com/convenient-locations/"]
    rules = [Rule(LinkExtractor(allow="/centers/"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if location := response.xpath('//*[@class="jet-map"]/@data-init').get():
            item = Feature()
            item["ref"] = item["website"] = response.url
            item["branch"] = (
                response.xpath('//meta[@property="og:title"]/@content')
                .get()
                .split(" |")[0]
                .removeprefix("Fitness 19 Gym ")
            )
            coordinates = json.loads(location).pop("center")
            item["lat"] = coordinates["lat"]
            item["lon"] = coordinates["lng"]
            location_info = response.xpath('//span[@class="elementor-icon-list-text"]/text()').getall()
            item["addr_full"], item["phone"] = location_info[:2]
            yield item
        else:
            # Collect POIs for urls redirecting to alternate website, https://www.fit19.com/locations/.
            # This website also doesn't list all POIs, so we are relying upon two websites, to collect them all.
            location = chompjs.parse_js_object(response.xpath('//script[contains(text(),"geolocation")]').get())
            item = DictParser.parse(location)
            item["ref"] = location.get("club_number")
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            item["website"] = response.url
            yield item
