from json import loads
from typing import Iterable

from scrapy.http import Request, Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class Big4HolidayParksAUSpider(JSONBlobSpider):
    name = "big4_holiday_parks_au"
    item_attributes = {"brand": "BIG4 Holiday Parks", "brand_wikidata": "Q18636678"}
    allowed_domains = ["www.big4.com.au"]
    start_urls = ["https://www.big4.com.au/park-directory"]

    def start_requests(self) -> Iterable[Request]:
        headers = {
            "Content-Type": "text/plain;charset=UTF-8",
            "Next-Action": "7651f6930c5534ce73277e1932d402973523f326",
            "Next-Router-State-Tree": "%5B%22%22%2C%7B%22children%22%3A%5B%5B%22page%22%2C%22park-directory%22%2C%22c%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%3F%7B%5C%22regiontown%5C%22%3A%5C%22Illawarra%5C%22%7D%22%2C%7B%7D%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
        }
        yield Request(
            url=self.start_urls[0], method="POST", headers=headers, body='[{"key":"","value":""}]', callback=self.parse
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        locations = loads("[" + response.text.splitlines()[1].split(":[", 1)[1].removesuffix("}"))
        for location in locations:
            properties = {
                "ref": location["key"],
                "name": location["title"],
                "lat": location["coordinates"]["latitude"],
                "lon": location["coordinates"]["longitude"],
                "website": "https://{}{}".format(self.allowed_domains[0], location["link"]["href"]),
            }
            contact_url = properties["website"] + "/contact"
            yield Request(url=contact_url, meta={"feature": properties}, callback=self.parse_contact_information)

    def parse_contact_information(self, response: Response) -> Iterable[Feature]:
        properties = response.meta["feature"]
        properties["addr_full"] = merge_address_lines(response.xpath("//address//text()").getall())
        properties["phone"] = (
            response.xpath('//p[contains(@class, "SidebarInfoBlock_phone__")]/a[contains(@href, "tel:")]/@href')
            .get("")
            .replace("tel:", "")
        )
        # TODO: extract resort amenities from URL "/facilities-and-activities"
        # TODO: extract resort map image from URL "/facilities-and-activities"
        yield Feature(**properties)
