import json
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class TangerSpider(Spider):
    name = "tanger"
    item_attributes = {"brand": "Tanger Outlets", "brand_wikidata": "Q7682888"}
    start_urls = ["https://www.tanger.com/find-a-tanger"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for center in json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"][
            "centers"
        ]:
            for address in center["fullAddressCS"]:
                item = DictParser.parse({**center, **address})
                item["street_address"] = merge_address_lines([address["address1"], address["address2"]])
                item["phone"] = center["centerPhoneNumber"] or center["contactTelephoneNumber"]
                item.pop("name")
                if len(center["fullAddressCS"]) > 1:
                    item["branch"] = address["addressLabel"].removeprefix("Tanger ")
                    item["ref"] = "{}-{}".format(center["slug"], item["branch"].lower().replace(" ", "-"))
                else:
                    item["branch"] = center["name"]
                    item["ref"] = center["slug"]
                item["website"] = response.urljoin("/{}".format(center["slug"]))

                item["opening_hours"] = OpeningHours()
                for rule in center["hours"]:
                    item["opening_hours"].add_range(DAYS[rule["day_index"]], rule["open"], rule["close"])

                apply_category(Categories.SHOP_MALL, item)

                yield item
