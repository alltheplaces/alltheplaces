from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.react_server_components import parse_rsc


class LeadersRomansGroupGBSpider(Spider):
    name = "leaders_romans_group_gb"
    BRANDS = {
        "leaders": {"brand": "Leaders", "brand_wikidata": "Q111522674"},
        "romans": {"brand": "Romans", "brand_wikidata": "Q113562519"},
    }
    start_urls = [
        "https://www.leaders.co.uk/our-offices/",
        "https://www.romans.co.uk/our-offices/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        brand_key = response.url.split(".")[1]
        if brand_key not in self.BRANDS:
            self.crawler.stats.inc_value("atp/leaders_romans/unknown_brand/%s" % brand_key)
        brand = self.BRANDS.get(brand_key, {})
        base_url = response.url.rsplit("/", 2)[0]

        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        for office in self.find_offices_data(data):
            slug = office.pop("slug", None)
            item = DictParser.parse(office)
            item["ref"] = f"{brand_key}-{office['id']}"
            item["branch"] = item.pop("name")
            item["website"] = f"{base_url}/{slug}/" if slug else None
            item.update(brand)
            apply_category(Categories.OFFICE_ESTATE_AGENT, item)
            yield item

    def find_offices_data(self, data: dict) -> list:
        for value in DictParser.iter_matching_keys(data, "data"):
            if isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict) and "latitude" in value[0] and "postcode" in value[0]:
                    return value
        return []
