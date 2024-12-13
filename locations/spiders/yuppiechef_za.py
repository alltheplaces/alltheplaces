from scrapy import Spider
from scrapy.http import Request

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS


class YuppiechefZASpider(Spider):
    name = "yuppiechef_za"
    item_attributes = {"brand": "Yuppiechef", "brand_wikidata": "Q24234053"}
    start_urls = ["https://www.yuppiechef.com/store-directory.htm"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS
    no_refs = True

    def start_requests(self):
        yield Request(
            url=self.start_urls[0],
            meta={"playwright": True, "playwright_include_page": True},
        )

    async def parse(self, response):
        items = {}
        for location in response.xpath('.//article[contains(@class, "store-loc-card")]'):
            item = Feature()
            name = location.xpath(".//h2/text()").get()
            item["branch"] = location.xpath(".//h2/text()").get().replace("Yuppiechef", "").strip()
            item["city"] = location.xpath('.//span[contains(@class, "text-pill")]/text()').get()
            item["phone"] = location.xpath('.//a[contains(@href, "tel:")]/@href').get()
            items[name] = item

        page = response.meta["playwright_page"]

        buttons = await page.locator('span:text("Store times and info")').all()
        for button in buttons:
            await button.click()
            name = await page.get_by_text("Address and").locator("../h2").inner_text()
            item = items[name]

            email = await page.get_by_role("link").filter(has_text="@yuppie").get_attribute("href")
            item["email"] = email

            address = await page.get_by_text("Address and").locator("../p[2]").inner_text()
            item["addr_full"] = clean_address(address)

            all_text = await page.get_by_text("Address and").locator("..").inner_text()
            hours_string = all_text.split("(next 7 days)")[1].split("Yuppiechef orders can be")[0]
            item["opening_hours"] = OpeningHours()
            for line in hours_string.split("\n"):
                if "day" in line:
                    item["opening_hours"].add_ranges_from_string(line.replace(line.split("\t")[1], ""))

            yield item

        await page.close()
