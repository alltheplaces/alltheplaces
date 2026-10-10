import html
import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The theme's Google Maps element writes one JS assignment per marker field, e.g.
#   av_google_map['av_gmap_0']['marker']['3']['lat'] = 36.146716;
MARKER_FIELD_RE = re.compile(r"av_google_map\['\w+'\]\['marker'\]\['(\d+)'\]\['(\w+)'\] = (.*?);\n")


class RoyalGibraltarPostOfficeGiSpider(Spider):
    name = "royal_gibraltar_post_office_gi"
    item_attributes = {"operator": "Royal Gibraltar Post Office", "operator_wikidata": "Q32784"}
    allowed_domains = ["post.gi"]
    start_urls = [
        "https://post.gi/4814-2/",  # "Pillar Box Locations"
        "https://post.gi/building-locations/",  # General Post Office and Parcel Office
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        markers = {}
        for index, field, value in MARKER_FIELD_RE.findall(response.text):
            markers.setdefault(index, {})[field] = value.strip()

        is_pillar_box_page = "4814-2" in response.url
        for marker in markers.values():
            if not marker.get("lat") or not marker.get("long"):
                continue
            address = json.loads(marker.get("address", '""')).strip()
            content_lines = [
                " ".join(html.unescape(re.sub(r"<[^>]+>", " ", line)).split())
                for line in re.split(r"<br\s*/?>|\n", json.loads(marker.get("content", '""')))
            ]
            content_lines = [line for line in content_lines if line]
            label = " ".join(content_lines)

            item = Feature()
            item["ref"] = json.loads(marker["av_uid"])
            item["lat"] = float(marker["lat"])
            item["lon"] = float(marker["long"])

            if is_pillar_box_page:
                # "address" is a short street/landmark; "content" is the descriptive location text.
                item["addr_full"] = address
                if label and label != address:
                    item["extras"]["description"] = label
                apply_category(Categories.POST_BOX, item)
            else:
                # content is "<name><br>\n<street address>", e.g. "Parcel Office" / "Unit E, 7 Rooke Road"
                item["name"] = content_lines[0] if content_lines else None
                item["street_address"] = address.removesuffix(", Gibraltar")
                apply_category(Categories.POST_OFFICE, item)
            yield item
