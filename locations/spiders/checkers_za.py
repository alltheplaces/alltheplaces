from scrapy import Request, Selector

from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider

# Shoprite Holdings owns the Checkers brand, as well as another brand,
# Shoprite. Refer to shoprite_za for an almost identical spider
# addressing the Shoprite brand.


class CheckersZASpider(StructuredDataSpider):
    name = "checkers_za"
    start_urls = ["https://www.checkers.co.za/sitemap/medias/Store-checkersZA-0.xml"]
    sitemap_rules = [(r"s^http:\/\/www\.checkers\.co\.za\/store\/\d+$", "parse_sd")]
    # AWS WAF bot protection appears to be used but can be bypassed with Playwright.
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"CONCURRENT_REQUESTS": 1, "ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def start_requests(self):
        for sitemap_url in self.start_urls:
            yield Request(
                url=sitemap_url,
                meta={"playwright": True, "playwright_include_page": True},
                callback=self.parse_sitemap,
                errback=self.errback_close_page,
            )

    async def errback_close_page(self, failure):
        playwright_page = failure.request.meta["playwright_page"]
        await playwright_page.close()

    async def parse_sitemap(self, response):
        playwright_page = response.meta["playwright_page"]
        sitemap = await playwright_page.content()
        await playwright_page.close()
        sitemap_locations = Selector(text=sitemap).xpath("//loc/text()").getall()
        for sitemap_location in sitemap_locations:
            yield Request(url=sitemap_location.replace("http://", "https://").split("?", 1)[0], callback=self.parse_sd)

    def pre_process_data(self, ld_data):
        # One openingHourSpecification mixes hours for a
        # supermarket (first listed) and hours for any additional
        # stores-in-a-store (pharmacy, liquor shop, etc). Only the
        # first set of opening hours should be extracted.
        if ohspec := ld_data.get("openingHoursSpecification"):
            newohspec = {}
            for day_hours in ohspec:
                if day_hours["dayOfWeek"] in newohspec.keys():
                    break
                newohspec[day_hours["dayOfWeek"]] = day_hours
            ld_data["openingHoursSpecification"] = list(newohspec.values())

    def post_process_item(self, item, response, ld_data):
        if "Checkers Hyper " in item["name"]:
            item["brand"] = "Checkers Hyper"
            item["brand_wikidata"] = "Q116518886"
            item["name"] = item["name"].replace("Checkers Hyper ", "")
        elif "Checkers " in item["name"]:
            item["brand"] = "Checkers"
            item["brand_wikidata"] = "Q5089126"
            item["name"] = item["name"].replace("Checkers ", "")
        else:
            self.logger.warning("Unknown brand from store name: {}".format(item["name"]))
            return
        apply_category(Categories.SHOP_SUPERMARKET, item)
        item["ref"] = response.url.split("/")[-1]
        item["website"] = response.xpath('//link[@rel="canonical"]/@href').get()
        item.pop("facebook", None)
        item.pop("twitter", None)
        yield item
