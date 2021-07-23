# -*- coding: utf-8 -*-
import json
import csv
import scrapy
import re

from locations.items import GeojsonPointItem

COOKIES = {
    "bm_sz": "04B124C1C96D68082A9F61BAAAF0B6D5~YAAQdjsvF22E8Xl6AQAACr1VfAxPEt+enarZyrOZrBaNvyuX71lK5QPuDR/FgDEWBZVMRhjiIf000W7Z1PiAjxobrz2Y5LcYMH3CvUNvpdS3MjVLUMGwMEBCf9L5nD5Gs9ho2YL8T7Tz7lYvpolvaOlJnKrHyhCFxxk/uyBZ2G/0QrGKLwSaCQShDsz7ink=",
    "_abck": "440E40C406E69413DCCC08ABAA3E9022~-1~YAAQdjsvF26E8Xl6AQAACr1VfAYznoJdJhX7TNIZW1Rfh6qRhzquXg+L1TWoaL7nZUjXlNls2iPIKFQrCdrWqY/CNXW+mHyXibInMflIXJi5VVB/Swq53kABYJDuXYSlCunYvJAzMSr1q12NOYswz134Y8HRNzVWhkb2jMS5whmHxS/v0vniIvS1TQtKjEQlMGzQYmN41CmLX0JobipQhDtUB4VyNwztb2DCAZiqDX8BLwWg7h/DtPd4158qU69hNhayFTgWmD76/MiR8/T536tMmcoRyWLl4fEtP/XUmKOcksuZO7dbfNxXBffTxIXPYwf1eO77LNuZTCQq5kfsGZLJX8ODju2KSjnIF1vdnyHAe98FDIm+hw==~-1~-1~-1"
}

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'cache-control': 'max-age=0',
    'referer': 'https://www.aldi.co.uk/store-finder',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
}

class AldiUKSpider(scrapy.Spider):
    name = "aldi_uk"
    item_attributes = {'brand': "Aldi"}
    allowed_domains = ['aldi.co.uk']
    download_delay = 0.5
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
    }

    def start_requests(self):
        url = 'https://www.aldi.co.uk/sitemap/store-en_gb-gbp'
        
        yield scrapy.http.FormRequest(
            url=url,
            method='GET',
            dont_filter=True,
            cookies=COOKIES,
            headers=HEADERS,
            callback=self.parse
        )
        
    def parse(self, response):
        response.selector.remove_namespaces()
        store_urls = response.xpath('//url/loc/text()').extract()
        
        for store_url in store_urls:

            yield scrapy.http.FormRequest(
                url=store_url,
                method='GET',
                dont_filter=True,
                cookies=COOKIES,
                headers=HEADERS,
                callback=self.parse_store
            )
        
    def parse_store(self, response):
        
        store_js = response.xpath('//script[@type="text/javascript"]/text()').extract_first()
        json_data = re.search('gtmData =(.+?);', store_js).group(1)
        data = json.loads(json_data)
        
        geojson_data = response.xpath('//script[@class="js-store-finder-initial-state"][@type="application/json"]/text()').extract_first()
        geodata = json.loads(geojson_data)

        properties = {
            'name': data['seoData']['name'],
            'ref': data['seoData']['name'],
            'addr_full': data['seoData']['address']['streetAddress'],
            'city': data['seoData']['address']['addressLocality'],
            'postcode': data['seoData']['address']['postalCode'],
            'country': data['seoData']['address']['addressCountry'],
            'website': response.request.url,
            'opening_hours': str(data['seoData']['openingHours']).replace('[','').replace(']','').replace("'",''),
            'lat': geodata['store']['latlng']['lat'],
            'lon': geodata['store']['latlng']['lng'],
        }

        yield GeojsonPointItem(**properties)
