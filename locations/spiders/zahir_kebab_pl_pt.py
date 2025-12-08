from json import loads
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, DAYS_PL, DAYS_PT, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ZahirKebabPLPTSpider(Spider):
    name = "zahir_kebab_pl_pt"
    item_attributes = {"brand": "Zahir Kebab", "brand_wikidata": "Q116148750"}
    allowed_domains = ["zahirkebab.pl"]
    start_urls = ["https://zahirkebab.pl/lokale/"]

    def parse(self, response: Response) -> Iterable[Request]:
        map_data = loads(
            response.xpath("//script/text()[contains(., 'umsAllMapsInfo')]")
            .get()
            .split("umsAllMapsInfo = ")[1]
            .split("\n")[0][:-1]
        )[0]["markers"]
        for marker in map_data:
            url = marker["params"]["marker_link_src"]
            if url.startswith("http"):
                properties = {
                    "ref": marker["id"],
                    "lat": marker["coord_x"],
                    "lon": marker["coord_y"],
                }
                yield Request(url=url, meta={"properties": properties}, callback=self.parse_feature)

    def parse_feature(self, response: Response) -> Iterable[Feature]:
        properties = response.meta["properties"]
        properties["branch"] = response.xpath('//div[@class="entry-content"]/div[1]/div[1]/h3/strong/text()').get()
        properties["addr_full"] = merge_address_lines(
            response.xpath('//div[@class="entry-content"]/div[1]/div[1]/h4/text()').getall()
        )
        days = DAYS_PL
        if "/en/" in response.url:
            # All store pages redirected to their English langauge page are
            # observed to be located in Poland.
            properties["country"] = "PL"
            days = DAYS_EN
        elif "/pl/" in response.url:
            properties["country"] = "PL"
        elif "/pt/" in response.url:
            properties["country"] = "PT"
            days = DAYS_PT
        properties["phone"] = (
            response.xpath('//div[@class="entry-content"]/div[1]/div[1]/h4/span[contains(text(), "tel:")]/text()')
            .get("")
            .replace("tel:", "")
            .strip()
        )
        properties["website"] = response.url
        if not properties["phone"]:
            properties["phone"] = None
        hours_text = " ".join(
            response.xpath(
                '//div[@class="entry-content"]/div[1]/div[1]/div/table/tbody/tr/td[position() <= 3]/text()'
            ).getall()
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_text, days=days, delimiters=[" "])
        apply_category(Categories.FAST_FOOD, properties)
        yield Feature(**properties)
