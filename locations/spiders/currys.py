from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


def playwright_should_abort_request(request) -> bool:
    # By default, Playwright also downloads the images and scripts. We don't need them.
    return not (request.resource_type == "document" and (request.url.endswith(".html") or request.url.endswith(".xml")))


class CurrysSpider(SitemapSpider, StructuredDataSpider):
    name = "currys"
    item_attributes = {"brand": "currys", "brand_wikidata": "Q3246464"}
    sitemap_urls = ["https://www.currys.co.uk/sitemap-stores-curryspcworlduk.xml"]
    custom_settings = {
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30 * 1000,
        "PLAYWRIGHT_ABORT_REQUEST": playwright_should_abort_request,
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {"https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"},
    }

    def start_requests(self):
        for request in super().start_requests():
            request.meta["playwright"] = True
            yield request

    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            request.meta["playwright"] = True
            yield request

    def pre_process_data(self, ld_data, **kwargs):
        if isinstance(ld_data["openingHoursSpecification"], dict):
            ld_data["openingHoursSpecification"] = [ld_data["openingHoursSpecification"]]
        for rule in ld_data["openingHoursSpecification"]:
            rule["opens"] = rule["opens"].strip()
            rule["closes"] = rule["closes"].strip()

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath('//input[@class="storeDetailLat"]/@value').get()
        item["lon"] = response.xpath('//input[@class="storeDetailLong"]/@value').get()
        item["name"] = response.xpath('//h1[@class="store-information-page-title"]/text()').get().strip()
        yield item
