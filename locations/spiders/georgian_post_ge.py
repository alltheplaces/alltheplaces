import json
import re
from typing import Any

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_GE, OpeningHours
from locations.items import Feature


class GeorgianPostGESpider(Spider):
    name = "georgian_post_ge"
    item_attributes = {"operator": "შპს საქართველოს ფოსტა", "operator_wikidata": "Q12869041"}
    allowed_domains = ["gpost.ge"]
    # The page lists Tbilisi; the rest of the country comes from the same search form with the "region" option.
    start_urls = ["https://gpost.ge/help/offices"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield from self.parse_offices(response)
        yield FormRequest.from_response(
            response,
            formid="FindOfficesForm",
            formdata={"CityId": "", "SearchText": "", "isPostalBox": "False"},
            callback=self.parse_offices,
        )

    def parse_offices(self, response: Response, **kwargs: Any) -> Any:
        # The map markers are embedded as a JSON string literal: var pointarray = JSON.parse("[{\\"id\\":39,...}]");
        points = json.loads(
            json.loads('"{}"'.format(re.search(r'pointarray = JSON\.parse\("(.+?)"\);', response.text)[1]))
        )
        for point in points:
            info = response.xpath(f'//div[@class="com-mod-scenters-map-infolist"]/div[@id="{point["id"]}"]')
            fields = {
                row.xpath("normalize-space(td[1])").get().rstrip(":"): row.xpath("td[2]") for row in info.xpath(".//tr")
            }
            item = Feature()
            item["ref"] = str(point["id"])
            item["lat"], item["lon"] = point["lat"].strip(), point["lon"].strip()
            # e.g. "0200 აბაშის საფოსტო სერვის ცენტრი" (Abasha postal service centre), "80114 თბილისის კონტრაქტორი ოფისი"
            item["branch"] = re.sub(r"^\d+\s+", "", point["title"].strip())
            if index := fields.get("ინდექსი"):
                item["postcode"] = index.xpath("normalize-space()").get()
            if address := fields.get("მისამართი"):
                item["addr_full"] = address.xpath("normalize-space()").get()
            if hours := fields.get("სამუშაო საათები"):
                item["opening_hours"] = self.parse_hours(hours.xpath("span/text()").getall())
            # "კონტრაქტორი ოფისი": a Georgian Post-branded office run by an unnamed contractor
            if "external-offices" in point["url"]:
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            else:
                apply_category(Categories.POST_OFFICE, item)
            yield item

    def parse_hours(self, lines: list[str]) -> OpeningHours:
        # e.g. "ორშაბათი - პარასკევი : 09:00 - 19:00", "შაბათი : 10:00 - 16:00", "კვირა: დასვენების დღე" (day off)
        oh = OpeningHours()
        oh.add_ranges_from_string("; ".join(lines), days=DAYS_GE, closed=["დასვენების"])
        return oh
