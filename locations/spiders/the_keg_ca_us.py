import re
from typing import AsyncIterator

from scrapy import Selector
from scrapy.http import Request

from locations.categories import Extras, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS


class TheKegCAUSSpider(PlaywrightSpider):
    name = "the_keg_ca_us"
    item_attributes = {"brand": "The Keg", "brand_wikidata": "Q7744066"}
    allowed_domains = ["thekeg.com"]
    start_urls = ["https://thekeg.com/en/locations"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url=self.start_urls[0],
            callback=self.parse_locations_list,
            meta={"playwright": True, "playwright_include_page": True},
        )

    async def parse_locations_list(self, response):
        playwright_page = response.meta["playwright_page"]
        view_all_button = playwright_page.locator("css=div.view-all > button")
        await view_all_button.click()
        await playwright_page.wait_for_function('!document.querySelector("div.view-all")')
        html_content = await playwright_page.content()
        await playwright_page.close()
        locations = Selector(text=html_content)
        for location_url in locations.xpath(
            '//div[contains(@class, "LocationCard")]/a[contains(@class, "image-link")]/@href'
        ).getall():
            yield Request(
                url="https://thekeg.com" + location_url,
                callback=self.parse,
            )

    def parse(self, response):
        properties = {
            "ref": response.url.split("/")[-1],
            "website": response.url,
            "name": response.xpath('//section[@id="LocationDetail"]//h2/text()').get(),
            "addr_full": re.sub(
                r"\s+",
                " ",
                " ".join(
                    filter(
                        None,
                        response.xpath(
                            '//section[@id="LocationDetail"]//p[contains(@class, "address")]//text()'
                        ).getall(),
                    )
                ),
            ).strip(),
            "phone": response.xpath('//section[@id="LocationDetail"]//p[contains(@class, "phone")]/a/@href')
            .get("")
            .replace("tel:", ""),
        }
        hours_text = re.sub(
            r"\s+",
            " ",
            " ".join(filter(None, response.xpath('//div[contains(@class, "hours")]//table//text()').getall())),
        ).strip()
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_text)
        extract_google_position(properties, response)
        extra_features = map(
            str.upper,
            map(
                str.strip, filter(None, response.xpath('//div[contains(@class, "attributes")]/ul/li/p/text()').getall())
            ),
        )
        apply_yes_no(Extras.WIFI, properties, "FREE WI-FI" in extra_features, False)
        yield Feature(**properties)
