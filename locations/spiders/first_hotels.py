import json
import re
from typing import Any, Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature, SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider


class FirstHotelsSpider(JSONBlobSpider):
    name = "first_hotels"
    item_attributes = {"brand": "First Hotels", "brand_wikidata": "Q11969007"}
    start_urls = ["https://www.firsthotels.com/general-info/about-first-hotels/map-of-hotels/"]

    def extract_json(self, response: Response) -> list[dict]:
        stream = "".join(
            json.loads(chunk) for chunk in re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', response.text, re.S)
        )

        countries = {}
        for match in re.finditer(r'\{"id":\d+,"_order":', stream):
            city = chompjs.parse_js_object(stream[match.start() :])
            if city.get("countrySlug"):
                countries[city["id"]] = city["countrySlug"]

        locations = {}
        for match in re.finditer(r'"synxis_id":', stream):
            location = chompjs.parse_js_object(stream[stream.rfind("{", 0, match.start()) :])
            if "lat" not in location or location.get("hotelType") == "partner":
                continue
            location["country_slug"] = countries.get(location["city"])
            locations[location["id"]] = location
        return list(locations.values())

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)
        item["city"] = location.get("postalAddress")
        item["email"] = location.get("mail")
        if instagram := location.get("instagramUrl"):
            set_social_media(item, SocialMedia.INSTAGRAM, instagram)
        if location.get("country_slug"):
            item["website"] = "https://www.firsthotels.com/{}/{}".format(location["country_slug"], location["slug"])
        if images := location.get("images"):
            item["image"] = images[0].get("image", {}).get("external")

        apply_category(Categories.HOTEL, item)
        yield item
