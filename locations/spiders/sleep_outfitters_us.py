from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class SleepOutfittersUSSpider(Spider):
    name = "sleep_outfitters_us"
    item_attributes = {"brand": "Sleep Outfitters", "brand_wikidata": "Q120509459"}
    offset = 0
    page_size = 20
    fields = ["address", "address2", "city", "state", "postal", "lat", "lng", "hours_summary", "phone", "storefront"]
    api = "https://www.sleepoutfitters.com/api/cms/v2/retail-location-pages/"

    def next_request(self) -> JsonRequest:
        return JsonRequest(
            url="{}?{}".format(
                self.api,
                urlencode(
                    {
                        "offset": self.offset,
                        "limit": self.page_size,
                        "fields": ",".join(self.fields),
                    }
                ),
            )
        )

    def start_requests(self):
        yield self.next_request()

    def parse(self, response, **kwargs):
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item["street_address"] = clean_address([item.pop("addr_full", None), location["address2"]])
            item["image"] = location.get("storefront", {}).get("meta", {}).get("download_url")
            item["extras"]["branch"] = item.pop("name", "").replace("Sleep Outfitters", "").strip(", !")

            yield item

        if len(response.json()["items"]) == self.page_size:
            self.offset += self.page_size
            yield self.next_request()
