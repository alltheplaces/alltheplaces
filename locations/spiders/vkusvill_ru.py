from urllib.parse import urlparse
from locations.hours import DAYS_RU, OpeningHours
from locations.items import Feature
from scrapy.utils.sitemap import Sitemap
from scrapy.http import Request, FormRequest
from scrapy.spiders import Spider


class VkusvillRUSpider(Spider):
    name = "vkusvill_ru"
    allowed_domains = ["vkusvill.ru"]
    start_urls = ["https://vkusvill.ru/"]
    item_attributes = {"brand": "ВкусВилл", "brand_wikidata": "Q57271676"}
    custom_settings = {
        'ROBOTSTXT_OBEY': False
    }
    download_delay = 3
    shop_ids = []

    def parse(self, response):
        subdomains = response.xpath('//a[@class="Dropdown__listLink Dropdown__listLinkGeo js-geo-set-city"]/@data-subdomain').extract()
        self.logger.info(f"Found {len(subdomains)} subdomains")
        for subdomain in subdomains:
            # The first subdomain is empty, but it's actually for Moscow
            if subdomain == "":
                sitemap_url = f"https://vkusvill.ru/upload/sitemap/msk/sitemap_shops.xml"
            else:
                sitemap_url = f"https://{subdomain}.vkusvill.ru/upload/sitemap/{subdomain}/sitemap_shops.xml"
            yield Request(
                sitemap_url,
                callback=self.parse_sitemap,
            )
    
    def parse_sitemap(self, response):
        s = Sitemap(response.body)
        urls = [urlparse(p['loc']) for p in s]
        self.logger.info(f"Found {len(urls)} urls in sitemap {response.url}")
        for url in urls:
            if not url.query:
                continue
            shop_id = url.query.split('=')[1]

            # Don't go to the same shop twice
            if shop_id in self.shop_ids:
                continue
            self.shop_ids.append(shop_id)

            yield FormRequest(
                f"https://{response.url.split('/')[2]}/ajax/shops/detail.php",
                formdata={'id': shop_id, 'isSelfdeliverySection': 'false'},
                callback=self.parse_shop,
                meta={'shop_id': shop_id, 'url': str(url.geturl())}
            )
    
    def parse_shop(self, response, **kwargs):
        item = Feature()
        self.logger.info(f"Got response from {response.url}")
        self.logger.info(f"Shop id is {response.meta.get('shop_id')}")
        item['ref'] = response.meta.get('shop_id')
        item['website'] = response.meta.get('url')
        item['city'] = self.sanitize(response.xpath('//div[@class="VV21_MapPanelCard__Region"]/text()').extract_first())
        item['street_address'] = self.sanitize(response.xpath('//div[@class="VV21_MapPanelCard__BodyTitle"]/text()').extract_first())
        # Skip darkstores as they are closed for public
        if 'Даркстор' in item.get('street_address'):
            yield None
        hours = self.sanitize(response.xpath('//div[@class="VV21_MapPanelCard__WorkStatusTime"]/text()').extract_first())
        self.parse_hours(hours, item)
        item['phone'] = self.sanitize(response.xpath('//a[@class="VV21_MapPanelCard__PhoneLink"]/text()').extract_first())
        item['lat'] = self.sanitize(response.xpath('//div[@class="VV21_MapPanelCard__Route"]/a/@data-lat').extract_first())
        item['lon'] = self.sanitize(response.xpath('//div[@class="VV21_MapPanelCard__Route"]/a/@data-lon').extract_first())
        yield item

    def sanitize(self, value):
        if value:
            return value.strip()
        return value
    
    def parse_hours(self, hours, item):
        # Expected format is "Пн-Вс: 08:00-22:00"
        try:
            oh = OpeningHours()
            oh.add_ranges_from_string(hours, DAYS_RU)
            item['opening_hours'] = oh.as_opening_hours()
        except Exception:
            self.logger.warning(f"Parse hours failed: {hours}")
            self.crawler.stats.inc_value("atp/hours/failed")

        



        

