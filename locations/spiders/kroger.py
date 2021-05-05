# -*- coding: utf-8 -*-
import json
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from scrapy.selector import Selector


DEFAULT_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/63.0.3239.84 Safari/537.36",
    'connection': 'keep-alive'}

BRANDS = [
    {
        'brand': "Baker's",
        'brand_wikidata': "Q4849080",
        'domain': "www.bakersplus.com"
    },
    {
        'brand': "City Market",
        'brand_wikidata': "Q5123299",
        'domain': "www.citymarket.com"
    },
    {
        'brand': "Dillons",
        'brand_wikidata': "Q5276954",
        'domain': "www.dillons.com"
    },
    {
        'brand': "Food 4 Less",
        'brand_wikidata': "Q5465282",
        'domain': "www.food4less.com"
    },
    {
        'brand': "Foods Co",
        # This is an alt name used by Food 4 Less in N. California; same wikidata
        'brand_wikidata': "Q5465282",
        'domain': "www.foodsco.net"
    },
    {
        'brand': "Fred Meyer",
        'brand_wikidata': "Q5495932",
        'domain': "www.fredmeyer.com"
    },
    {
        'brand': "Fry's Food Stores",
        'brand_wikidata': "Q5506547",
        'domain': "www.frysfood.com"
    },
    {
        'brand': "Gerbes",
        # This is a subbrand of Dillons; same wikidata
        'brand_wikidata': "Q5276954",
        'domain': "www.gerbes.com"
    },
    {
        'brand': "JayC",
        'brand_wikidata': "Q6166302",
        'domain': "www.jaycfoods.com"
    },
    {
        'brand': "King Soopers",
        'brand_wikidata': "Q6412065",
        'domain': "www.kingsoopers.com"
    },
    {
        'brand': "Kroger",
        'brand_wikidata': "Q153417",
        'domain': "www.kroger.com"
    },
    {
        'brand': "Mariano's Fresh Market",
        'brand_wikidata': "Q55622168",
        'domain': "www.marianos.com"
    },
    {
        'brand': "Metro Market",
        # This is a subbrand of Roundy's; same wikidata
        'brand_wikidata': "Q7371288",
        'domain': "www.metromarket.net"
    },
    {
        'brand': "Pay Less",
        'brand_wikidata': "Q7156587",
        'domain': "www.pay-less.com"
    },
    {
        'brand': "Owen's",
        'brand_wikidata': "Q7114367",
        'domain': "www.owensmarket.com"
    },
    {
        'brand': "Pick 'n Save",
        # This is a subbrand of Roundy's; same wikidata
        'brand_wikidata': "Q7371288",
        'domain': "www.picknsave.com"
    },
    {
        'brand': "QFC",
        'brand_wikidata': "Q7265425",
        'domain': "www.qfc.com"
    },
    {
        'brand': "Ralphs",
        'brand_wikidata': "Q3929820",
        'domain': "www.ralphs.com"
    },
    {
        'brand': "Smith's",
        'brand_wikidata': "Q7544856",
        'domain': "www.smithsfoodanddrug.com"
    }
]


class KrogerSpider(scrapy.Spider):
    name = "kroger"
    item_attributes = {'brand': "Kroger", 'brand_wikidata': "Q153417"}
    download_delay = 0.2
    allowed_domains = [b['domain'] for b in BRANDS]

    def start_requests(self):
        for brand in BRANDS:
            yield scrapy.Request(url=f"https://{brand['domain']}/storelocator-sitemap.xml",
                                 headers=DEFAULT_HEADERS,
                                 meta={'brand': brand})

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath('//loc/text()').extract()
        for url in urls:
            yield scrapy.Request(url,
                                 callback=self.parse_store,
                                 headers=DEFAULT_HEADERS,
                                 meta=response.meta)

    def parse_store(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json"]/text()').extract_first()
        if data:
            data = json.loads(data)
            services = response.css(
                '.StoreServices-departmentsItem::text').getall()
            services = [s.lower() for s in services]
        else:
            return

        properties = {
            'ref': '/'.join(response.url.split('/')[-2:]),
            'name': f"{data['name']} {response.meta['brand']['brand']}",
            'addr_full': data["address"]["streetAddress"].strip(),
            'city': data["address"]["addressLocality"].strip(),
            'state': data["address"]["addressRegion"],
            'postcode': data["address"]["postalCode"],
            'country': data["address"].get("addressCountry"),
            'phone': data.get("telephone"),
            'lat': float(data["geo"]["latitude"]),
            'lon': float(data["geo"]["longitude"]),
            'opening_hours': '; '.join(data['openingHours']),
            'website': data.get("url") or response.url,
            'brand': response.meta['brand']['brand'],
            'brand_wikidata': response.meta['brand']['brand_wikidata'],
            'extras': {
                'shop': 'supermarket',
                'amenity:fuel': 'gas station' in services,
                'amenity:pharmacy': 'pharmacy' in services,
                'atm': 'atm' in services
            }
        }

        yield GeojsonPointItem(**properties)
