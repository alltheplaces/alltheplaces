import re
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.central_england_cooperative import set_operator


class AnPostIESpider(Spider):
    name = "an_post_ie"
    AN_POST = {"brand": "An Post", "brand_wikidata": "Q482490"}
    start_urls = ["https://www.anpost.com/Store-Locator"]

    cats = {
        "Parcel Locker": Categories.PARCEL_LOCKER,
        "Post Office": Categories.POST_OFFICE,
    }

    def parse(self, response):
        subscription_key = re.search(
            r"intAPISubscriptionKey\s*=\s*\'(\w+)\';",
            response.xpath('//*[contains(text(),"intAPISubscriptionKey ")]/text()').get(),
        ).group(1)
        yield JsonRequest(
            "https://apim-anpost-apwebapis.anpost.com/apweb-intservicesapi/v1/StoreLocator/Search",
            headers={"Ocp-Apim-Subscription-Key": subscription_key},
            callback=self.parse_details,
        )

    def parse_details(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = None
            item["addr_full"] = merge_address_lines(
                [
                    location["Address1"],
                    location["Address2"],
                    location["Address3"],
                    location["Address4"],
                    location["Address5"],
                    location["Address6"],
                ]
            )
            item["postcode"] = location["EirCode"]
            item["country"] = "IE"
            item["website"] = urljoin("https://www.anpost.com/Store-Locator/", location["NameURL"])
            item["extras"]["collection_times"] = location["LastTimeOfPosting"]

            if cat := self.cats.get(location["Type"]):
                apply_category(cat, item)
                set_operator(self.AN_POST, item)
            elif location["Type"].upper() == "POSTPOINT":
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            else:
                item["extras"]["type"] = location["Type"]
                self.logger.error("Unexpected type: {}".format(location["Type"]))

            yield item
