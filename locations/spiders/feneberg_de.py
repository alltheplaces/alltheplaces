import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature

# Matches each entry of the "const locations = [...]" JS array embedded in
# the store finder page: [lon, lat, name, id, google_maps_dir_url, street,
# housenumber, postcode, city, phone, detail_url]
LOCATION_ENTRY_RE = re.compile(
    r"\[\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*(\d+),\s*'[^']*',"
    r"\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\s*\]"
)


class FenebergDESpider(scrapy.Spider):
    name = "feneberg_de"
    item_attributes = {"brand": "Feneberg", "brand_wikidata": "Q5345378"}
    start_urls = ["https://www.feneberg.de/maerkte-service/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for script in response.xpath('//script[contains(text(), "const locations")]/text()').getall():
            for (
                lon,
                lat,
                name,
                ref,
                street,
                housenumber,
                postcode,
                city,
                phone,
                detail_url,
            ) in LOCATION_ENTRY_RE.findall(script):
                yield scrapy.Request(
                    response.urljoin(detail_url),
                    callback=self.parse_store,
                    cb_kwargs={
                        "ref": ref,
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "street": street,
                        "housenumber": housenumber,
                        "postcode": postcode,
                        "city": city,
                        "phone": phone,
                    },
                )

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = kwargs["ref"]
        item["name"] = kwargs["name"]
        item["lat"] = kwargs["lat"]
        item["lon"] = kwargs["lon"]
        item["street"] = kwargs["street"]
        item["housenumber"] = kwargs["housenumber"]
        item["postcode"] = kwargs["postcode"]
        item["city"] = kwargs["city"]
        item["phone"] = kwargs["phone"]
        item["website"] = response.url
        item["country"] = "DE"

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        for row in response.xpath('//div[@class="area-item-2"]//table//tr'):
            day = row.xpath("./td[1]/text()").get("").strip().rstrip(":")
            hours = row.xpath("./td[2]/text()").get("").strip()
            if not day or not hours or hours == "-" or "-" not in hours:
                continue

            day_code = DAYS_DE.get(day)
            if not day_code:
                continue

            open_time, close_time = hours.split("-", 1)
            oh.add_range(day_code, open_time.strip(), close_time.strip())

        return oh
