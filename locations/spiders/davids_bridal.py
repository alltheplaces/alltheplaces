import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DavidsBridalSpider(scrapy.Spider):
    name = "davids_bridal"
    item_attributes = {"brand": "Davids Bridal", "brand_wikidata": "Q5230388"}
    allowed_domains = ["www.davidsbridal.com"]
    start_urls = [
        "https://www.davidsbridal.com/graphql?query={storeLocationList{active+name+phone+storeId+timezone+location{postalCode+state+city+country+countryCode+latitude+longitude+address1+address2+building+__typename}hours{regular{close+day+open+__typename}override{date+end+name+start+timeType+__typename}__typename}__typename}}"
    ]
    requires_proxy = True

    def parse(self, response):
        for data in response.json().get("data", {}).get("storeLocationList"):
            item = DictParser.parse(data)
            item["postcode"] = data.get("location", {}).get("postalCode")
            item["state"] = data.get("location", {}).get("state")
            item["city"] = data.get("location", {}).get("city")
            item["street_address"] = data.get("location", {}).get("address1")
            item["website"] = (
                f'https://www.davidsbridal.com/stores/{item["city"].lower()}-{item["state"].lower()}-{item["postcode"].replace("-", "")}-{item["ref"]}'
                if item["state"]
                else None
            )
            oh = OpeningHours()
            if data.get("hours", {}):
                for day in data.get("hours", {}).get("regular"):
                    oh.add_range(day=day.get("day"), open_time=day.get("open")[:5], close_time=day.get("close")[:5])

            item["opening_hours"] = oh.as_opening_hours()
            yield item
