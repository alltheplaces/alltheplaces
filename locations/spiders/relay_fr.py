import scrapy

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours


class RelayFrSpider(scrapy.Spider):
    name = "relay_fr"
    item_attributes = {"brand": "Relay", "brand_wikidata": "Q3424298"}
    allowed_domains = ["relay.com"]
    requires_proxy = "FR"

    def start_requests(self):
        point_files = "eu_centroids_120km_radius_country.csv"
        for lat, lon in point_locations(point_files, "FR"):
            url = f"https://www.relay.com/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results=1000&search_radius=140"
            yield scrapy.Request(url=url)

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)
            item["name"] = data.get("store")
            item["website"] = data.get("permalink")
            item["street_address"] = item.pop("addr_full", None)

            days = scrapy.Selector(text=data.get("hours"))
            oh = OpeningHours()
            for day in days.xpath("//tr"):
                if day.xpath("./td[2]/text()").get() == "Closed":
                    continue
                oh.add_range(
                    day=day.xpath("./td[1]/text()").get(),
                    open_time=day.xpath(".//time/text()").get().split(" - ")[0],
                    close_time=day.xpath(".//time/text()").get().split(" - ")[1],
                )

            item["opening_hours"] = oh.as_opening_hours()

            yield item
