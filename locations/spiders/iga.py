import scrapy

from locations.items import GeojsonPointItem


class IgaSpider(scrapy.Spider):
    name = "iga"
    item_attributes = {"brand": "IGA", "brand_wikidata": "Q3146662"}
    allowed_domains = ["iga.com"]
    start_urls = ["https://www.iga.com/find-a-store"]

    def parse(self, response):
        next_page = response.xpath('//a[@class="blog-navigation-next"]/@href').get()

        stores = response.xpath('//div[@class="span6"]/div[@class="row-fluid-wrapper"]')
        for store in stores:
            addr_full = store.xpath(".//@data-address").get().strip()
            yield GeojsonPointItem(
                lat=store.xpath(".//@data-lat").get(),
                lon=store.xpath(".//@data-long").get(),
                phone=store.xpath("//strong/a/text()").get(),
                ref=store.xpath('.//div[@class="store-logo"]/img/@alt').get().replace("Logo", "").strip(),
                name=store.xpath('.//div[@class="store-logo"]/img/@alt').get().replace("Logo", "").strip(),
                website=store.xpath('.//a[@class="store-website-link"]/@href').get(),
                addr_full=addr_full,
                postcode=addr_full.split(",")[-1:][0].strip(),
                city=addr_full.split(",")[-3:][0].strip(),
                state=addr_full.split(",")[-2:][0].strip(),
                street_address=addr_full.split(",")[:1][0].strip(),
            )

        if next_page and stores:
            yield scrapy.Request(response.urljoin(next_page))
