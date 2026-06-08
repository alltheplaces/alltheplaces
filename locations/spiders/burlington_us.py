from typing import Any, Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc


class BurlingtonUSSpider(SitemapSpider):
    name = "burlington_us"
    item_attributes = {
        "brand": "Burlington",
        "brand_wikidata": "Q4999220",
    }
    sitemap_urls = ["https://www.burlington.com/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.burlington\.com/stores/[a-z]{2}/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for _, s in (chompjs.parse_js_object(s) for s in scripts) if isinstance(s, str)).encode()
        data = dict(parse_rsc(rsc))

        for store in DictParser.get_nested_key(data, "locations") or []:
            location = store["storeLocation"]
            item = DictParser.parse(location)
            item["ref"] = location["storeNumber"]
            item["branch"] = location["projectName"].split(" (#")[0]
            item["website"] = response.urljoin(store["storeDetailsHref"])

            item["opening_hours"] = OpeningHours()
            for rule in store.get("standardHours", []):
                if " - " not in rule["hours"]:
                    continue
                open_time, close_time = rule["hours"].split(" - ")
                item["opening_hours"].add_range(DAYS_EN[rule["label"]], open_time, close_time, time_format="%I:%M %p")

            if (start_date := location.get("grandOpeningDate")) and not start_date.startswith("$"):
                item["extras"]["start_date"] = start_date

            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item
