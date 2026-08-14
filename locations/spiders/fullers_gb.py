from typing import AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

FEED_URL = "https://www.fullers.co.uk/api/main/pubs/feed"
INFORMATION_URL = "https://www.fullers.co.uk/api/main/pubs/information?pubId={}"


class FullersGBSpider(Spider):
    name = "fullers_gb"
    item_attributes = {"brand": "Fuller's", "brand_wikidata": "Q5253950"}
    allowed_domains = ["fullers.co.uk"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}

    def feed_request(self, page: int) -> FormRequest:
        return FormRequest(
            FEED_URL,
            formdata={"pageNumber": str(page), "latitude": "0", "longitude": "0", "area": ""},
            callback=self.parse_feed,
        )

    async def start(self) -> AsyncIterator[FormRequest]:
        # Page count is only known from a response, so start at the first page
        # and let parse_feed request the rest.
        yield self.feed_request(1)

    def parse_feed(self, response: Response) -> Iterable[Request]:
        feed = response.json()
        for pub in feed["items"]:
            # Coordinates and opening hours are only on the information endpoint.
            yield Request(INFORMATION_URL.format(pub["pubId"]), callback=self.parse_pub, cb_kwargs={"pub": pub})
        if feed["currentPage"] < feed["totalPages"]:
            yield self.feed_request(feed["currentPage"] + 1)

    def parse_pub(self, response: Response, pub: dict) -> Iterable[Feature]:
        information = response.json()

        item = Feature()
        item["ref"] = pub["pubId"]
        item["addr_full"] = pub["subTitle"]
        item["lat"] = information["googleMaps"]["coords"]["lat"]
        item["lon"] = information["googleMaps"]["coords"]["lng"]
        item["phone"] = information["socials"]["phoneNumber"]["value"]
        item["email"] = information["socials"]["email"]["value"]
        item["website"] = information["socials"]["website"]["link"]

        # Titles append the locality, eg "The Willow, Bourton-on-the-Water". Split from the
        # right as some pub names contain a comma, eg "The Lock, Stock & Barrel, Newbury".
        item["branch"] = pub["title"].rsplit(",", 1)[0]

        item["opening_hours"] = OpeningHours()
        for day in (information["timesData"] or {}).get("openingTimes", []):
            for times in day["values"]:
                if times == "Closed":
                    item["opening_hours"].set_closed(DAYS_EN[day["label"]])
                else:
                    item["opening_hours"].add_range(day["label"], *times.split("-"))

        apply_category(Categories.PUB, item)
        yield item
