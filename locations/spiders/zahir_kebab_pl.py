import json

from scrapy import Request, Spider

from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class ZahirKebabPLSpider(Spider):
    name = "zahir_kebab_pl"
    start_urls = ["https://zahirkebab.pl/lokale/"]
    item_attributes = {"brand": "Zahir Kebab", "brand_wikidata": "Q116148750"}

    def parse(self, response, **kwargs):
        mapData = json.loads(
            response.xpath("//script/text()[contains(., 'umsAllMapsInfo')]")
            .get()
            .split("umsAllMapsInfo = ")[1]
            .split("\n")[0][:-1]
        )[0]["markers"]
        for marker in mapData:
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
        infoDiv = response.xpath(
            "//div[@class='entry-content']/div[@class='wp-block-columns']/div[contains(@class, 'wp-block-column')]"
        )

        def textInOptionalSpan(h4Index):
            if infoDiv.xpath(f"h4[{h4Index}]/span").get() is not None:
                return infoDiv.xpath(f"h4[{h4Index}]/span/text()").get().strip()
            return infoDiv.xpath(f"h4[{h4Index}]/text()").get().strip()

        openingHours = OpeningHours()
        for row in infoDiv.xpath("div[contains(@class, 'ninja_table_wrapper')]/table/tbody/tr"):
            cells = row.xpath("td/text()").getall()
            if len(cells) < 3:
                continue
            day, openTime, closeTime = cells[:3]
            if day and openTime and closeTime:
                openingHours.add_ranges_from_string(f"{day} {openTime}-{closeTime}", days=DAYS_PL)
        postCodeCity = textInOptionalSpan("3")
        properties = {
            "phone": textInOptionalSpan("1").removeprefix("tel: "),
            "street_address": textInOptionalSpan("2"),
            "postcode": postCodeCity.split(" ")[0],
            "city": " ".join(postCodeCity.split(" ")[1:]),
            "opening_hours": openingHours,
        }
        properties.update(kwargs)
        yield Feature(**properties)
