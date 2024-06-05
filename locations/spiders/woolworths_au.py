import scrapy

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class WoolworthsAUSpider(scrapy.Spider):
    name = "woolworths_au"
    item_attributes = {"brand": "Woolworths", "brand_wikidata": "Q3249145"}
    allowed_domains = ["woolworths.com.au"]
    start_urls = [
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=10000&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&postcode=*"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "AU"

    def parse(self, response):
        data = response.json()

        for i in data["Stores"]:
            if not i["IsOpen"]:
                continue

            i["street_address"] = clean_address([i["AddressLine1"], i["AddressLine2"]])
            i["ref"] = i.pop("StoreNo")
            i["city"] = i.pop("Suburb")

            item = DictParser.parse(i)

            item["website"] = (
                "https://www.woolworths.com.au/shop/storelocator/"
                + "-".join([item["state"], item["city"], item["ref"], i["Division"]]).lower()
            )

            # TODO: types needs some work, NSI seems out of date too
            item["extras"] = {"type": i["Division"]}

            yield item
