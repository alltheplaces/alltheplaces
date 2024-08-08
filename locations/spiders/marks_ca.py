from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response
from scrapy.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class MarksCASpider(Spider):
    name = "marks_ca"
    item_attributes = {"brand": "Mark's", "brand_wikidata": "Q6766373"}
    start_urls = ["https://www.marks.com/sitemap_Store-en_CA-CAD.xml"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in iterloc(Sitemap(response.body)):
            ref = url.removesuffix(".html").split("-")[-1]
            yield JsonRequest(
                url="https://apim.marks.com/v1/store/store/{}".format(ref),
                callback=self.parse_location,
                headers={"Ocp-Apim-Subscription-Key": "c01ef3612328420c9f5cd9277e815a0e", "baseSiteId": "MKS"},
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()
        item = Feature()
        item["ref"] = str(location["id"])
        item["lat"] = location["geoPoint"]["latitude"]
        item["lon"] = location["geoPoint"]["longitude"]
        item["branch"] = location["displayName"]
        item["city"] = location["address"]["city"]["name"]
        item["state"] = location["address"]["region"]["name"]
        item["country"] = location["address"]["country"]["isocode"]
        item["email"] = location["address"]["email"]
        item["phone"] = location["address"]["phone"]
        item["postcode"] = location["address"]["postalCode"]
        item["street_address"] = merge_address_lines([location["address"]["line1"], location["address"]["line2"]])

        item["opening_hours"] = OpeningHours()
        for rule in location["openingHours"]["weekDayOpeningList"]:
            if rule["closed"]:
                continue
            item["opening_hours"].add_range(
                rule["weekDay"],
                rule["openingTime"]["formattedHour"],
                rule["closingTime"]["formattedHour"],
                time_format="%I:%M %p",
            )

        for link in location["hreflangLinkData"]:
            if link["hreflang"] == "x-default":
                item["website"] = urljoin("https://www.marks.com", link["href"])
            elif link["hreflang"] == "en":
                item["extras"]["website:en"] = urljoin("https://www.marks.com", link["href"])
            elif link["hreflang"] == "fr":
                item["extras"]["website:fr"] = urljoin("https://www.lequipeur.com", link["href"])

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
