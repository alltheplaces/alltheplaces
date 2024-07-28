import csv
import re
from urllib.parse import parse_qs, urlsplit

import chompjs
import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points


class MightyFlameSpider(scrapy.Spider):
    name = "mighty_flame"
    item_attributes = {"brand": "Mighty Flame", "extras": {"shop": "fuel", "fuel": "propane"}}
    allowed_domains = ["secure.gotwww.com"]

    def start_requests(self):
        for name in [
            "ca_centroids_100mile_radius.csv",
            "us_centroids_100mile_radius.csv",
        ]:
            with open_searchable_points(name) as points:
                for point in csv.DictReader(points):
                    yield scrapy.Request(
                        f'https://secure.gotwww.com/gotlocations.com/mightyflame/index.php?bypass=y&lat2={point["latitude"]}&lon2={point["longitude"]}'
                    )

    def parse(self, response):
        js = response.xpath('//script[contains(text(), "L.marker")]').get()
        for line in re.findall(r"^L\.marker.*", js, re.M):
            [lat, lon] = chompjs.parse_js_object(line)
            popup = re.search(r".bindPopup\((.*)\);", line)[1]

            # Evidently this is what happens when you use PHP to write JavaScript
            # Just remove the entire area with the syntax error since we don't need it
            popup = re.sub(r'google\.com/maps\?.*?"', "", popup)

            [popup] = chompjs.parse_js_object("[" + popup + "]")
            popup = scrapy.Selector(text=popup)

            [ref] = parse_qs(urlsplit(popup.css('a[href*="id="]').attrib["href"]).query)["id"]
            text = popup.xpath("//div/text()").getall()
            phone = next((s.removeprefix("phone: ") for s in text if s.startswith("phone:")), None)
            street_address = text[0]
            city_state_postcode = text[1]
            city, state_postcode = city_state_postcode.split(", ", 1)
            state, postcode = state_postcode.split(" ", 1)
            properties = {
                "ref": ref,
                "lon": lon,
                "lat": lat,
                "name": popup.css("strong::text").get(),
                "phone": phone,
                "street_address": street_address,
                "city": city,
                "state": state,
                "postcode": postcode,
            }
            yield Feature(**properties)
