import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class McCoysSpider(scrapy.Spider):
    name = "mccoys"
    item_attributes = {"brand": "McCoy's Building Supply"}
    allowed_domains = ["www.mccoys.com"]
    download_delay = 0.5
    start_urls = ("https://www.mccoys.com/stores",)

    def parse_hours(self, hours):

        opening_hours = OpeningHours()
        for i in range(0, len(hours), 2):
            day = hours[i]
            open_time, close_time = hours[i + 1].split("-")
            opening_hours.add_range(
                day=day[:2],
                open_time=open_time.strip(),
                close_time=close_time.strip(),
                time_format="%I:%M %p",
            )
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        properties = response.meta["properties"]

        address1, address2 = response.xpath(
            '//a[contains(@href, "maps")]/text()'
        ).extract()
        city, state, zipcode = re.search(
            r"^(.*),\s+([a-z]{2})\s+([0-9]{5})$", address2.strip(), re.IGNORECASE
        ).groups()

        properties.update(
            {
                "addr_full": address1.strip(),
                "phone": response.xpath(
                    '//div[contains(text(), "Call")]/span/text()'
                ).extract_first(),
                "city": city,
                "state": state,
                "postcode": zipcode,
                "ref": re.search(r".*stores\/(.+)\?*.*", response.url).groups()[0],
                "website": response.url,
            }
        )

        hours = response.xpath(
            '//div[contains(text(), "Store Hours")]/following-sibling::table//td/text()'
        ).extract()
        opening_hours = self.parse_hours(hours)
        if hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        stores = response.xpath('//div[@id="mc-filtered-stores-container"]/div/div')

        for store in stores:
            properties = {
                "lat": float(store.xpath("./@data-lat").extract_first()),
                "lon": float(store.xpath("./@data-long").extract_first()),
                "name": store.xpath('.//div[@class="mc-bold-text"]/text()')
                .extract_first()
                .strip(),
            }
            url = store.xpath(
                './/a[contains(text(), "Store Information")]/@href'
            ).extract_first()

            yield scrapy.Request(
                response.urljoin(url),
                callback=self.parse_store,
                meta={"properties": properties},
            )
