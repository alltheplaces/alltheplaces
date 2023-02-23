import scrapy
from bs4 import BeautifulSoup

from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature


class ScapinoNLSpider(scrapy.Spider):
    name = "scapino_nl"
    item_attributes = {"brand": "Scapino", "brand_wikidata": "Q2298792"}
    # start_urls = ["https://www.scapino.nl/lookup/stores"]

    def start_requests(self):
        url = "https://www.scapino.nl/lookup/stores"
        # url = self.start_urls[0]

        headers = {
            "Referer": "https://www.scapino.nl/winkels",
            "x-requested-with": "XMLHttpRequest",
        }
        yield scrapy.Request(url=url, headers=headers, method="POST", callback=self.parse)

    def parse(self, response):
        for store in response.json().get("stores"):
            store_view = store.get("view")
            view_soup = BeautifulSoup(store_view, features="lxml")
            address_lines = [line.strip() for line in view_soup.find("address").text.strip().splitlines()]
            opening_hours_items = [item.text.strip() for item in view_soup.find("table").find_all("td")]
            oh = OpeningHours()
            days = opening_hours_items[::2]
            hours = opening_hours_items[1::2]
            for i in range(len(days)):
                if hours[i] != "Gesloten":
                    open_at = hours[i].split(" - ")[0]
                    close_at = hours[i].split(" - ")[1]
                    oh.add_range(day=DAYS_NL[days[i].capitalize()], open_time=open_at, close_time=close_at)

            properties = {
                "ref": store.get("store").get("name"),
                "addr_full": " ".join(address_lines),
                "street_address": address_lines[0],
                "postcode": address_lines[1].split(" ")[0],
                "city": address_lines[1].split(" ")[1],
                "website": f"https://www.scapino.nl{view_soup.find('a').get('href')}",
                "lat": store.get("location").get("latitude"),
                "lon": store.get("location").get("longitude"),
                "opening_hours": oh,
            }

            yield Feature(**properties)
