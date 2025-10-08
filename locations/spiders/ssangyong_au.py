from typing import Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.ssangyong_kr import SSANGYONG_SHARED_ATTRIBUTES


class SsangyongAUSpider(Spider):
    name = "ssangyong_au"
    item_attributes = SSANGYONG_SHARED_ATTRIBUTES
    allowed_domains = ["kgm.com.au"]
    start_urls = ["https://kgm.com.au/dealers"]

    def parse(self, response: Response) -> Iterable[Request]:
        for external_script in response.xpath('//script[contains(@src, "/_next/static/chunks/")]/@src').getall():
            yield Request(
                url="https://{}{}".format(self.allowed_domains[0], external_script), callback=self.parse_js_file
            )

    def parse_js_file(self, response: Response) -> Iterable[Feature]:
        if '=JSON.parse(\'[{"ID":' in response.text:
            js_blob = response.text.split("=JSON.parse('", 1)[1].split("')}", 1)[0]
            features = parse_js_object(js_blob)
            for feature in features:
                properties = {
                    "branch": feature.get("Dealership"),
                    "lat": feature.get("DealerLatitude"),
                    "lon": feature.get("DealerLongitude"),
                    "addr_full": feature.get("DealerAddress"),
                    "state": feature.get("DealerState"),
                    "postcode": str(feature.get("DealerPostcode")),
                    "website": feature.get("DealerWebsite"),
                }
                if properties["website"] and not properties["website"].startswith("http"):
                    properties["website"] = "https://" + properties["website"]
                if feature.get("IsSalesStore"):
                    sales_item = Feature(**properties)
                    sales_item["ref"] = str(feature["DealerCode"]) + "_Sales"
                    sales_item["phone"] = feature.get("DealerTelephone")
                    sales_item["email"] = feature.get("DealerEmail")
                    sales_item["opening_hours"] = OpeningHours()
                    sales_item["opening_hours"].add_ranges_from_string(
                        "Mon-Fri: {}, Sat: {}, Sun: {}".format(
                            feature.get("DealerOpenMonFri") or "closed",
                            feature.get("DealerOpenSaturday") or "closed",
                            feature.get("DealerOpenSunday") or "closed",
                        )
                    )
                    apply_category(Categories.SHOP_CAR, sales_item)
                    yield sales_item
                if feature.get("IsServiceStore"):
                    service_item = Feature(**properties)
                    service_item["ref"] = str(feature["DealerCode"]) + "_Service"
                    service_item["phone"] = feature.get("ServiceTelephone")
                    service_item["email"] = feature.get("ServiceEmail")
                    service_item["opening_hours"] = OpeningHours()
                    service_item["opening_hours"].add_ranges_from_string(
                        "Mon-Fri: {}, Sat: {}, Sun: {}".format(
                            feature.get("ServiceOpenMonFri") or "closed",
                            feature.get("ServiceOpenSaturday") or "closed",
                            feature.get("ServiceOpenSunday") or "closed",
                        )
                    )
                    apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                    yield service_item
                if feature.get("IsPartsStore"):
                    parts_item = Feature(**properties)
                    parts_item["ref"] = str(feature["DealerCode"]) + "_Parts"
                    parts_item["phone"] = feature.get("PartsTelephone")
                    parts_item["email"] = feature.get("PartsEmail")
                    parts_item["opening_hours"] = OpeningHours()
                    parts_item["opening_hours"].add_ranges_from_string(
                        "Mon-Fri: {}, Sat: {}, Sun: {}".format(
                            feature.get("PartsOpenMonFri") or "closed",
                            feature.get("PartsOpenSaturday") or "closed",
                            feature.get("PartsOpenSunday") or "closed",
                        )
                    )
                    apply_category(Categories.SHOP_CAR_PARTS, parts_item)
                    yield parts_item
