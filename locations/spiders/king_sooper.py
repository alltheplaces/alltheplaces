# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class KingSooperSpider(scrapy.Spider):
    name = "king_sooper"
    allowed_domains = ["www.kingsoopers.com"]
    start_urls = (
        'https://www.kingsoopers.com/stores?address=37.7578595,-79.76804&includeThirdPartyFuel=true&maxResults=50&radius=3000&showAllStores=false&useLatLong=true',
    )

    download_delay = 3

    store_types = {
        '' : "unknown-blank",
        'C': "grocery",
        'F': "unknown-f",
        'G': "gas station",
        'I': "unknown-i",
        'J': "unknown-j",
        'M': "grocery",
        'Q': "unknown-q",
        'S': "grocery",
        'X': "unknown-x",
    }

    ll_requests = set()

    def start_requests(self):

        url = self.start_urls[0]

        headers = {
                   'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                   'accept-language': 'en-US,en;q=0.9',
                   'accept-encoding': 'gzip, deflate, br',
                   'cache-control': 'max-age=0',
                   'upgrade-insecure-requests': '1',
                   'cookie': 'sth_pid=9dcd67b4-01bf-423d-a5fc-8fc14d6aa139; pid=9dcd67b4-01bf-423d-a5fc-8fc14d6aa139; sid=6b021a26-e385-4a16-854d-86dc9c14ae7c; __VCAP_ID__=0ddde0be-67e6-404f-6064-ea3f; AMCVS_371C27E253DB0F910A490D4E%40AdobeOrg=1; AMCV_371C27E253DB0F910A490D4E%40AdobeOrg=-1891778711%7CMCIDTS%7C17515%7CMCMID%7C21069743295962380020454009139483608988%7CMCAAMLH-1513867542%7C7%7CMCAAMB-1513867545%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1513269942s%7CNONE%7CMCAID%7C2D19474F851D0937-60000103E00083E2%7CMCSYNCSOP%7C411-17522%7CvVersion%7C2.4.0; s_cc=true; dtSa=true%7CC%7C-1%7CShow%20stores%20with...%7C-%7C1513267454526%7C62737976_20%7Chttps%3A%2F%2Fwww.kingsoopers.com%2Fstores%2FstoreLocator%3Fhash%3DfindStoreLink%7CKing%20Soopers%20-%20Store%20Locator%7C1513267456147%7C; s_nr=1513267607021-Repeat; dtLatC=1; s_sq=krgrkingsoopersprod%252Ckrgrglobalprod%3D%2526c.%2526a.%2526activitymap.%2526page%253Dbn%25253Astores%25253Astorelocator%2526link%253DDepartments%2526region%253D--0%2526pageIDType%253D1%2526.activitymap%2526.a%2526.c%2526pid%253Dbn%25253Astores%25253Astorelocator%2526pidt%253D1%2526oid%253Dhttps%25253A%25252F%25252Fwww.kingsoopers.com%25252Fstores%25252FstoreLocator%25253Fhash%25253DfindStoreLink%252523%2526ot%253DA; dtPC=-; dtCookie=50678BDFC45A05C6A011A2DFEE5A5D24|QmFubmVyfDF8QWNjb3VudCtNYW5hZ2VtZW50fDE; AKA_A2=1; ak_bmsc=82ED7A3EE3023F524B9F4C2E75183A92685BA7563F750000FCB3325A0037C521~plH2XLCg/raSJx1IGMOfJgJ4NZy7WMZms+RaxvzkiYJO3n5TVJHZszOhG0meRUd7qw+51EKxo93+fEOMN+3om7Qi9H+++rIVkQ6U6uXDNFCZCo5PahrbTA4DFT8zfr6HneAYzrujkuRzwci+egjWhJ034H7GdIhnStykYx363Lcm6brlZkFBB6n7HRUBKzGz6Hn8iiD1CDIjXzX8b00tqd6vlN8EG7Ehq5TUYzEoGc8oM=',
                   'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                   }

        yield scrapy.Request(url=url, headers=headers, callback=self.parse)
        

    def store_hours(self, store_hours):
        if all([h == '' for h in store_hours.values()]):
            return None
        else:
            day_groups = []
            this_day_group = None
            for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
                day_open = store_hours[day + 'Open']
                day_close = store_hours[day + 'Close']
                hours = day_open + "-" + day_close
                day_short = day.title()[:2]

                if not this_day_group:
                    this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
                elif this_day_group['hours'] == hours:
                    this_day_group['to_day'] = day_short
                elif this_day_group['hours'] != hours:
                    day_groups.append(this_day_group)
                    this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            day_groups.append(this_day_group)

            if len(day_groups) == 1:
                opening_hours = day_groups[0]['hours']
                if opening_hours == '07:00-07:00':
                    opening_hours = '24/7'
            else:
                opening_hours = ''
                for day_group in day_groups:
                    if day_group['from_day'] == day_group['to_day']:
                        opening_hours += '{from_day} {hours}; '.format(**day_group)
                    else:
                        opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
                opening_hours = opening_hours[:-2]

            return opening_hours

    def phone_number(self, phone):
        return '{}-{}-{}'.format(phone[0:3], phone[3:6], phone[6:10])

    def address(self, address):
        if not address:
            return None

        (num, rest) = address['addressLineOne'].split(' ', 1)
        addr_tags = {
            "housenumber": num.strip(),
            "street": rest.strip(),
            "city": address['city'],
            "state": address['state'],
            "postcode": address['zipCode'],
        }

        return addr_tags

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        bounding_box = {
            'min_lat': 100,
            'max_lat': -100,
            'min_lon': 300,
            'max_lon': -300,
        }

        for store in data:
            store_information = store['storeInformation']
            store_hours = store['storeHours']

            properties = {
                "phone": self.phone_number(store_information['phoneNumber']),
                "ref": store_information['recordId'],
                "name": store_information['localName'],
                "type": self.store_types[store_information['storeType']],
                "opening_hours": self.store_hours(store_hours),
            }

            address = self.address(store_information['address'])
            if address:
                properties.update(address)

            lon_lat = [
                float(store_information['latLong']['longitude']),
                float(store_information['latLong']['latitude']),
            ]

            bounding_box['min_lat'] = min(bounding_box['min_lat'], lon_lat[1])
            bounding_box['max_lat'] = max(bounding_box['max_lat'], lon_lat[1])
            bounding_box['min_lon'] = min(bounding_box['min_lon'], lon_lat[0])
            bounding_box['max_lon'] = max(bounding_box['max_lon'], lon_lat[0])

            yield GeojsonPointItem(**properties)

        if data:
            box_corners = [
                '{},{}'.format(bounding_box['min_lat'], bounding_box['min_lon']),
                '{},{}'.format(bounding_box['max_lat'], bounding_box['min_lon']),
                '{},{}'.format(bounding_box['min_lat'], bounding_box['max_lon']),
                '{},{}'.format(bounding_box['max_lat'], bounding_box['max_lon']),
            ]

            for corner in box_corners:
                if corner in self.ll_requests:
                    self.logger.info("Skipping request for %s because we already did it", corner)
                else:
                    self.ll_requests.add(corner)
                    yield scrapy.Request(
                        'https://www.kingsoopers.com/stores?address={}&includeThirdPartyFuel=true&maxResults=50&radius=3000&showAllStores=false&useLatLong=true'.format(
                            corner
                        ),
                    )
        else:
            self.logger.info("No results")
