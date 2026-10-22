from json import loads
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_PL, OpeningHours, sanitise_day
from locations.items import Feature


class DealzPLSpider(Spider):
    name = "dealz_pl"
    item_attributes = {"brand": "Dealz", "brand_wikidata": "Q16942585"}
    allowed_domains = ["www.dealz.pl"]

    async def start(self) -> AsyncIterator[Request]:
        # Fifty closest shops are returned no matter their distance from the
        # supplied centroid. Small search radius (24km) required to find the
        # maximum number of features.
        for lat, lon in country_iseadgg_centroids(["PL"], 24):
            yield Request(url=f"https://www.dealz.pl/sklepy/?lat={lat}&lng={lon}")

    def parse(self, response: Response) -> Iterable[Feature]:
        features = loads(response.xpath("//div/@shops-map-markers").get())

        if len(features) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(features))

        for feature in features:
            properties = {
                "lat": feature["coordinates"]["lat"],
                "lon": feature["coordinates"]["lng"],
                "ref": feature["shop_id"],
            }

            shop_div = response.xpath(f'//div[@shops-map-marker-html={feature["shop_id"]}]')
            if not shop_div:
                continue
            address = shop_div.xpath("div/div[contains(@class, 'leaflet-popup__data')]/text()").get()
            address = address.strip()
            address_parts = list(map(str.strip, address.split(",")))
            properties["street_address"] = address_parts[0]
            post_code_city = address_parts[-1]
            properties["postcode"] = post_code_city.split(" ")[0]
            properties["city"] = " ".join(post_code_city.split(" ")[1:])

            shop_box = response.xpath(f'//div[@shops-map-marker-anchor={feature["shop_id"]}]')
            properties["website"] = shop_box.xpath('.//a[@class="find-shop-box__link"]/@href').get()

            properties["opening_hours"] = OpeningHours()
            for row in shop_box.xpath(".//table[contains(@class, 'find-shop-box__content__table--hours')]//tr"):
                day = sanitise_day(row.xpath("normalize-space(td[1])").get(), DAYS_PL)
                hours = row.xpath("normalize-space(td[2])").get()
                if hours == "Zamknięte":
                    properties["opening_hours"].set_closed(day)
                else:
                    open_time, close_time = hours.split(" - ")
                    properties["opening_hours"].add_range(day, open_time, close_time)

            item = Feature(**properties)
            apply_category(Categories.SHOP_VARIETY_STORE, item)
            yield item
