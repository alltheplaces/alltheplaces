import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# Office codes look like "10003AA1": the five-digit postcode of the office followed by a suffix.
OFFICE_CODE_RE = re.compile(r"^(\d{5})[A-Z]{2}\d+$")


class IraqiPostIqSpider(Spider):
    name = "iraqi_post_iq"
    item_attributes = {"operator": "البريد العراقي", "operator_wikidata": "Q12184443"}
    allowed_domains = ["post.iq"]
    # "المواقع البريدية" (postal locations): one static page with a table of offices per governorate
    # (federal Iraq only; the Kurdistan Region's offices are not listed).
    start_urls = ["https://post.iq/?page=17"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for table in response.xpath("//table"):
            rows = table.xpath(".//tr")
            # First row is the caption "الترميز البريدي لمحافظة <governorate>", second the column headers
            # (serial, office, latitude, longitude, postal code).
            governorate = re.sub(r"^الترميز البريدي لمحافظة\s*", "", self.clean(rows[0].xpath("string()").get()))
            for row in rows[2:]:
                cells = [self.clean(cell.xpath("string()").get()) for cell in row.xpath("./td")]
                if len(cells) != 5 or not cells[4]:
                    continue
                _, office, lat, lon, code = cells
                item = Feature()
                item["ref"] = code
                item["branch"] = office
                item["lat"] = lat
                item["lon"] = lon
                if match := OFFICE_CODE_RE.match(code):
                    item["postcode"] = match.group(1)
                item["state"] = governorate or None
                item["extras"] = {"operator:en": "Iraqi Post"}
                apply_category(Categories.POST_OFFICE, item)
                yield item

    @staticmethod
    def clean(text: str | None) -> str:
        return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()
