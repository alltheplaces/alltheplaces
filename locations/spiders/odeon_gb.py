import json

from scrapy import Spider

from locations.dict_parser import DictParser


class OdeonGBSpider(Spider):
    name = "odeon_gb"
    item_attributes = {"brand": "Odeon", "brand_wikidata": "Q6127470"}
    start_urls = ["https://www.odeon.co.uk/cinemas/"]
    requires_proxy = True

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath("//@data-v-site-list").get())
        for location in data["config"]["cinemas"]:
            location["address"] = ", ".join(
                filter(
                    None,
                    [
                        location.pop("addressLine1"),
                        location.pop("addressLine2"),
                        location.pop("addressLine3"),
                        location.pop("addressLine4"),
                        "United Kingdom",
                    ],
                )
            )
            location["url"] = f'https://www.odeon.co.uk{location["url"]}'
            yield DictParser.parse(location)
