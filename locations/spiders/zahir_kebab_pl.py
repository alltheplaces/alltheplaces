import json

from scrapy import Request, Spider

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class ZahirKebabPLSpider(Spider):
    name = "zahir_kebab_pl"
    start_urls = ["https://zahirkebab.pl/lokale/"]
    item_attributes = {"brand": "Zahir Kebab", "brand_wikidata": "Q116148750"}

    def parse(self, response, **kwargs):
        map_data = json.loads(
            response.xpath("//script/text()[contains(., 'umsAllMapsInfo')]")
            .get()
            .split("umsAllMapsInfo = ")[1]
            .split("\n")[0][:-1]
        )[0]["markers"]
        for marker in map_data:
            url = marker["params"]["marker_link_src"]
            if "http" in url:
                properties = {
                    "ref": marker["id"],
                    "lat": marker["coord_x"],
                    "lon": marker["coord_y"],
                    "website": url,
                }
                yield Request(url=url, callback=self.parse_store, cb_kwargs=properties)

    def parse_store(self, response, **kwargs):
        info_div = response.xpath(
            "//div[@class='entry-content']/div[@class='wp-block-columns']/div[contains(@class, 'wp-block-column')]"
        )

        def text_in_optional_span(h4_index):
            if info_div.xpath(f"h4[{h4_index}]/span").get() is not None:
                return info_div.xpath(f"h4[{h4_index}]/span/text()").get().strip()
            return info_div.xpath(f"h4[{h4_index}]/text()").get().strip()

        opening_hours = OpeningHours()
        for row in info_div.xpath("div[contains(@class, 'ninja_table_wrapper')]/table/tbody/tr"):
            cells = row.xpath("td/text()").getall()
            if len(cells) < 3:
                continue
            day, open_time, close_time = cells[:3]
            if day and open_time and close_time:
                opening_hours.add_ranges_from_string(f"{day} {open_time}-{close_time}", days=DAYS_PL)
        post_code_city = text_in_optional_span("3")
        properties = {
            "phone": text_in_optional_span("1").removeprefix("tel: "),
            "street_address": text_in_optional_span("2"),
            "postcode": post_code_city.split(" ")[0],
            "city": " ".join(post_code_city.split(" ")[1:]),
            "opening_hours": opening_hours,
        }
        properties.update(kwargs)
        yield Feature(**properties)
