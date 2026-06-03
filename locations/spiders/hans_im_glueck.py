from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HansImGlueckSpider(JSONBlobSpider):
    name = "hans_im_glueck"
    item_attributes = {"brand": "Hans im Glück", "brand_wikidata": "Q22569868"}
    start_urls = ["https://hansimglueck-burgergrill.de/typo3conf/ext/hig_site/Yext/locations.js"]

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(response.text)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item.get("name"):
            if item["name"].startswith("HANS IM GLÜCK - "):
                item["branch"] = item["name"].removeprefix("HANS IM GLÜCK - ").title()
        else:
            item["branch"] = feature["c_website_hig_name"]
        item["name"] = "Hans im Glück"
        item["ref"] = feature["meta"]["id"]
        item["extras"]["ref:google"] = feature.get("googlePlaceId")
        item["website"] = feature["c_baseURL"]
        if "emails" in feature:
            item["email"] = feature["emails"][0]
        if "c_website_standortfotos" in feature:
            item["image"] = response.urljoin(feature["c_website_standortfotos"][0]["url"])

        if "c_websiteÖffnungszeiten" in feature:
            oh = OpeningHours()
            for day in map(str.lower, DAYS_FULL):
                rule = feature["c_websiteÖffnungszeiten"]
                if rule.get("isClosed") is True:
                    oh.set_closed(day)
                    continue
                for interval in rule.get("openIntervals", []):
                    oh.add_range(day, interval["start"], interval["end"])
            item["opening_hours"] = oh

        yield item
