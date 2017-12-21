import scrapy
from locations.items import GeojsonPointItem
import json
import re

regex_times = r"\d{1,2}:\d{1,2}\s?[Aa]?[Mm]?[Pp]?[Mm]?\s?-\s?\d{1,2}:\d{1,2}" \
              r"\s?[Pp]?[Mm]?[Aa]?[Mm]?"
regex_am = r"\s?[Aa][Mm]"
regex_pm = r"\s?[Pp][Mm]"

STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]


class RegisSpider(scrapy.Spider):
    name = 'regis'
    download_delay = 0
    allowed_domains = ['www.regissalons.com']
    start_urls = ['https://www.regissalons.com/wp-admin/admin-ajax.php?action=store_search&lat=36.778261&lng=-119.41793239999998&max_results=100&search_radius=500&search=Ca']

    def convert_hours(self, hours):
        if not hours:
            return ''
        for i in range(len(hours)):
            converted_times = ''
            if 'Closed' not in hours[i]:
                from_hr, to_hr = [hr.strip() for hr in hours[i].split('-')]
                if re.search(regex_am, from_hr):
                    from_hr = re.sub(regex_am, '', from_hr)
                    hour_min = from_hr.split(':')
                    if len(hour_min[0]) < 2:
                        hour_min[0] = hour_min[0].zfill(2)
                    converted_times += (":".join(hour_min)) + ' - '
                else:
                    from_hr = re.sub(regex_pm, '', from_hr)
                    hour_min = from_hr.split(':')
                    if int(hour_min[0]) < 12:
                        hour_min[0] = str(12 + int(hour_min[0]))
                    converted_times += (":".join(hour_min)) + ' - '

                if re.search(regex_am, to_hr):
                    to_hr = re.sub(regex_am, '', to_hr)
                    hour_min = to_hr.split(':')
                    if len(hour_min[0]) < 2:
                        hour_min[0] = hour_min[0].zfill(2)
                    if int(hour_min[0]) == 12:
                        hour_min[0] = '00'
                    converted_times += (":".join(hour_min))
                else:
                    to_hr = re.sub(regex_pm, '', to_hr)
                    hour_min = to_hr.split(':')
                    if int(hour_min[0]) < 12:
                        hour_min[0] = str(12 + int(hour_min[0]))
                    converted_times += (":".join(hour_min))
            else:
                converted_times += "off"
            hours[i] = converted_times

        days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        hours = ''.join(' {} {} '.format(*t) for t in zip(days, hours))
        return hours

    def parse_store(self, response):
        results = json.loads(response.body_as_unicode())
        for i in results:
            store_id = i['id']
            name = i['address']
            website = i['permalink'].replace('\\', '')
            street = i['address2']
            city = i['city']
            state = i['state']
            postcode = i['zip']
            addr_full = "{} {}, {} {}".format(street, city, state, postcode)
            country = i['country']
            lat = i['lat']
            lon = i['lng']
            hours = re.findall(regex_times, i['hours'])
            hours = self.convert_hours(hours)

            yield GeojsonPointItem(
                ref=store_id,
                name=name,
                website=website,
                street=street,
                city=city,
                state=state,
                postcode=postcode,
                country=country,
                addr_full=addr_full,
                lat=lat,
                lon=lon,
                opening_hours=hours
            )

    def parse(self, response):
        base_url = 'https://www.regissalons.com/wp-admin/admin-ajax.php?action=store_search&lat=36.778261&lng=-119.41793239999998&max_results=100&search_radius=500&search='
        for state in STATES:
            yield scrapy.Request(base_url + state, callback=self.parse_store)
