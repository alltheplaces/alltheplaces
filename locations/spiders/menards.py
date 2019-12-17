import scrapy
from locations.items import GeojsonPointItem
import re

regex_id_name = r"\"\d{4}\",\s\"\w+.?&?\s?\w{0,10}\s?\w{0,10}\s?\w{0,10}\""

regex_street_city = r"\d+\s\w+.?-?\s?\w+.?\s?\w{0,12}.?\s?\d{0,2}\s?\w{0,12}" \
                    r"\",\s\"\w+\s?\w{0,12}\s?\w{0,12}"

regex_state_zip = r"\"\w{2}\",\s\"\d+"

regex_lat_lon = r"-\d+\.\d+\",\s\"\d+.\d+"


class MenardsSpider(scrapy.Spider):
    name = 'menards'
    brand = "Menards"
    allowed_domains = ['216.222.184.133']
    start_urls = ['https://216.222.184.133/main/storeLocator.html']

    def parse(self, response):
        script = response.xpath(
            '//script[contains(., "new store")]')[0].extract()
        lat_lon = re.findall(regex_lat_lon, script)
        lons = [x.split('"')[0] for x in lat_lon]
        lats = [x.split('"')[2] for x in lat_lon]

        id_name = re.findall(regex_id_name, script)
        store_ids = [x.split(',')[0].strip('"') for x in id_name]
        names = [x.split(', "')[1].strip('"') for x in id_name]

        strt_cty = re.findall(regex_street_city, script)
        streets = [x.split('",')[0] for x in strt_cty]
        cities = [x.split(', "')[1] for x in strt_cty]

        state_zip = re.findall(regex_state_zip, script)
        states = [x.split('",')[0].strip('"') for x in state_zip]
        postcodes = [x.split(', "')[1] for x in state_zip]

        for i in range(0, len(store_ids)):
            yield GeojsonPointItem(
                ref=store_ids[i],
                name=names[i],
                street=streets[i],
                city=cities[i],
                state=states[i],
                postcode=postcodes[i],
                lat=lats[i],
                lon=lons[i],
                addr_full="{} {}, {} {}".format(streets[i], cities[i],
                                                states[i], postcodes[i])
            )
