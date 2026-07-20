import json
from datetime import datetime
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class RentACarFRSpider(SitemapSpider):
    name = "rent_a_car_fr"
    item_attributes = {"brand": "Rent A Car", "brand_wikidata": "Q3425574"}
    sitemap_urls = ["https://www.rentacar.fr/sitemap-agences.xml"]
    sitemap_rules = [(r"/agences/\d+-", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        agency = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"].get(
            "agency"
        )
        if not agency:
            return

        address = agency["addressDto"]
        contact = agency.get("communicationMeansDto") or {}

        item = Feature()
        item["ref"] = agency["id"]
        item["branch"] = agency["label"]
        item["street_address"] = address["street"]
        item["postcode"] = address["zipCode"]
        item["city"] = agency["city"]["name"]
        item["lat"] = address.get("latitude")
        item["lon"] = address.get("longitude")
        item["phone"] = contact.get("phone")
        item["email"] = contact.get("email")
        item["website"] = response.url

        item["opening_hours"] = OpeningHours()
        for schedule in agency["nextSchedules"]:
            day = DAYS[datetime.fromisoformat(schedule["day"]).weekday()]
            if schedule["slots"]:
                for slot in schedule["slots"]:
                    item["opening_hours"].add_range(day, slot["start"][:5], slot["end"][:5])
            else:
                item["opening_hours"].set_closed(day)

        apply_category(Categories.CAR_RENTAL, item)
        yield item
