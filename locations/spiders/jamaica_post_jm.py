import re
from collections import Counter
from typing import Any

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class JamaicaPostJMSpider(Spider):
    name = "jamaica_post_jm"
    item_attributes = {"operator": "Jamaica Post", "operator_wikidata": "Q7233982"}
    allowed_domains = ["jamaicapost.gov.jm"]
    # The "Jamaica Post Location" page draws a Google map from an inline "markers" array: name and services
    # (Zip Mail, Fast Track...) in the info window. Only the larger offices are on it.
    start_urls = ["https://jamaicapost.gov.jm/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script = response.xpath('//script[contains(text(), "var markers")]/text()').get()
        # Part of the array is commented out (an older copy of some markers); drop comments before parsing.
        script = re.sub(r"/\*.*?\*/", "", script, flags=re.DOTALL)
        markers = parse_js_object(script[script.index("var markers") :])

        offices = []
        for marker in markers:
            name = re.split(r"<", re.sub(r"^\s*<h4>", "", marker["content"]))[0].strip()
            offices.append((name, marker["coords"]["lat"], marker["coords"]["lng"]))
        # Some markers are copies of a neighbour's point (Negril and Grange Hill, 15 km apart, share one):
        # such points are not trusted. A second "Santa Cruz" marker sits far from the town, so only the first
        # marker of a name is kept.
        shared = Counter((lat, lon) for _, lat, lon in offices)
        seen = set()
        for name, lat, lon in offices:
            if name in seen:
                continue
            seen.add(name)
            item = Feature()
            item["ref"] = re.sub(r"\W+", "-", name.lower()).strip("-")
            item["branch"] = re.sub(r"\s+(Post\s+)?Office$", "", name)
            if shared[(lat, lon)] == 1:
                item["lat"], item["lon"] = lat, lon
            item["country"] = "JM"
            apply_category(Categories.POST_OFFICE, item)
            yield item
