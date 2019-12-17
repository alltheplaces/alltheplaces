import scrapy
from locations.items import GeojsonPointItem
import json
import re

regex_times = r"\d{1,2}:\d{1,2}\s?[Aa]?[Mm]?[Pp]?[Mm]?\s?-\s?\d{1,2}:\d{1,2}" \
              r"\s?[Pp]?[Mm]?[Aa]?[Mm]?"
regex_am = r"\s?[Aa][Mm]"
regex_pm = r"\s?[Pp][Mm]"

#  Covers United States, Canada, UK, Puerto Rico, Bahamas with 500 mile radius
lats = ['32.806671', '31.054487',  '39.059811', '46.921925', '45.694454',
        '38.039119', '44.045876', '32.593106', '33.596319', '47.398349',
        '24.44715', '18.229351', '19.725342', '64.014496', '51.563412',
        '52.48278', '55.27911529201562', '55.17886766328199',
        '63.15435519659188', '52.96187505907603']

lons = ['-86.791130', '-97.563461', '-105.311104', '-110.454353', '-93.900192',
        '-87.618638', '-72.710686', '-82.342529', '-113.334961', '-121.289062',
        '-78.00293', '-65.830078', '-155.610352', '-153.28125' '-86.923828',
        '-65.126953', '-103.974609375', '-120.76171875', '-136.142578125',
        '-0.17578125']


class RegisSpider(scrapy.Spider):
    name = 'regis'
    item_attributes = { 'brand': "Regis Salon" }
    download_delay = 0
    allowed_domains = ['www.regissalons.com']
    start_urls = ['https://www.regissalons.com']

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
        for x, y in zip(lats, lons):
            base_url = 'https://www.regissalons.com/wp-admin/admin-ajax.php?action=store_search&max_results=100&search_radius=500&'
            base_url += "lat={}&lng={}".format(x, y)
            yield scrapy.Request(base_url, callback=self.parse_store)
