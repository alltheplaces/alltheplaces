import json

from playwright.async_api import Page
from scrapy import Request, Selector
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


async def tick_turnstile(page: Page) -> None:
    # The checkbox is in a closed shadow root, out of reach of clicks: focus it with Tab, tick it with Space.
    await page.wait_for_timeout(20000)
    await page.keyboard.press("Tab")
    await page.keyboard.press("Space")
    await page.wait_for_function("document.title !== 'Just a moment...'", timeout=30000)


class PascalCosteFRSpider(CamoufoxSpider):
    name = "pascal_coste_fr"
    item_attributes = {"brand": "Pascal Coste", "brand_wikidata": "Q66555630"}
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    # Camoufox reports the status of the challenge page, not of the page behind it.
    handle_httpstatus_list = [403]

    async def start(self):
        yield Request(
            "https://www.pascalcoste.com/salons", meta={"camoufox_page_methods": [PageMethod(tick_turnstile)]}
        )

    def parse(self, response):
        coordinates = {
            Selector(text=marker["content"]).xpath("//a/@href").get(): (marker["lat"], marker["lng"])
            for marker in json.loads(response.xpath('//script[@type="widgetkit/map"]/text()').get())["markers"]
        }

        # Also lists People Coiffure salons and the head office, which have another or no data-salon.
        for card in response.xpath('//div[contains(@data-salon, "pascal-coste")]'):
            details = card.xpath('./div[@class="description-liste-salons"]')
            phone = details.xpath('normalize-space(./div[@class="tel-liste-salons"])').get()
            if "Prochainement" in phone:
                continue
            url = card.xpath("./h3/a/@href").get()
            item = Feature()
            item["ref"] = url.rsplit("/", 1)[1]
            item["website"] = response.urljoin(url)
            item["branch"] = card.xpath("./h3/a/@title").get()
            if "homme" in card.xpath("@data-salon").get():
                item["name"] = "Homme Pascal Coste"
            item["lat"], item["lon"] = coordinates[url]
            item["street_address"] = merge_address_lines(
                details.xpath('./div[contains(@class, "element-text")]/text()').getall()
            )
            item["postcode"], item["city"] = (
                details.xpath('normalize-space(./div[@class="ville-liste-salons"])').get().split(" ", 1)
            )
            item["phone"] = phone
            yield item
