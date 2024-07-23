import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.user_agents import BROWSER_DEFAULT


class GucciSpider(scrapy.spiders.SitemapSpider):
    name = "gucci"
    item_attributes = {"brand": "Gucci", "brand_wikidata": "Q178516"}
    allowed_domains = ["www.gucci.com"]
    download_delay = 2.0
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    sites = [
        # See https://www.gucci.com/sitemap.xml!
        "https://www.gucci.com/ae/en_gb/",
        "https://www.gucci.com/at/de/",
        "https://www.gucci.com/au/en_au/",
        "https://www.gucci.com/be/en_gb/",
        "https://www.gucci.com/bg/en_gb/",
        "https://www.gucci.com/ca/en/",
        "https://www.gucci.com/ch/fr/",
        "https://www.gucci.com/cz/en_gb/",
        "https://www.gucci.com/de/de/",
        "https://www.gucci.com/dk/en_gb/",
        "https://www.gucci.com/es/es/",
        "https://www.gucci.com/fi/en_gb/",
        "https://www.gucci.com/fr/fr/",
        "https://www.gucci.com/hk/en_gb/",
        "https://www.gucci.com/hu/en_gb/",
        "https://www.gucci.com/ie/en_gb/",
        "https://www.gucci.com/it/it/",
        "https://www.gucci.com/jp/ja/",
        "https://www.gucci.com/kr/ko/",
        "https://www.gucci.com/kw/en_gb/",
        "https://www.gucci.com/nl/en_gb/",
        "https://www.gucci.com/no/en_gb/",
        "https://www.gucci.com/nz/en_au/",
        "https://www.gucci.com/pl/en_gb/",
        "https://www.gucci.com/pt/en_gb/",
        "https://www.gucci.com/qa/en_gb/",
        "https://www.gucci.com/ro/en_gb/",
        "https://www.gucci.com/sa/en_gb/",
        "https://www.gucci.com/se/en_gb/",
        "https://www.gucci.com/sg/en_gb/",
        "https://www.gucci.com/si/en_gb/",
        "https://www.gucci.com/tr/en_gb/",
        "https://www.gucci.com/uk/en_gb/",
        "https://www.gucci.com/us/en/",
    ]

    def start_requests(self):
        for url in self.sites:
            locale = url.split("/")[-2]
            sitemap_url = url + "sitemap/STORE-{}.xml".format(locale)
            yield scrapy.Request(sitemap_url, self._parse_sitemap)

    def parse(self, response):
        if item := LinkedDataParser.parse(response, "Store"):
            item["lat"] = response.xpath("//@data-latitude").get()
            item["lon"] = response.xpath("//@data-longitude").get()
            yield item
