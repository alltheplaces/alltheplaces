import json
import re
import scrapy
from locations.items import GeojsonPointItem

class JackInTheBoxSpider(scrapy.Spider):
    name = "jackinthebox"
    brand = "Jack In The Box"
    allowed_domains = ["jackinthebox.com"]
    start_urls = (
        "https://www.jackinthebox.com/api/locations",
    )
    dayMap = {
        'monday': 'Mo',
        'tuesday': 'Tu',
        'wednesday': 'We',
        'thursday': 'Th',
        'friday': 'Fr',
        'saturday': 'Sa',
        'sunday': 'Su'
    }
    def opening_hours(self, days_hours):
        day_groups = []
        this_day_group = None
        for day_hours in days_hours:
            day = day_hours[0]
            hours = day_hours[1]
            match = re.search(r'^(\d{1,2}):(\d{2})\w*(a|p)m-(\d{1,2}):(\d{2})\w*(a|p)m?$', hours)
            (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

            f_hr = int(f_hr)
            if f_ampm == 'p':
                f_hr += 12
            elif f_ampm == 'a' and f_hr == 12:
                f_hr = 0
            t_hr = int(t_hr)
            if t_ampm == 'p':
                t_hr += 12
            elif t_ampm == 'a' and t_hr == 12:
                t_hr = 0

            hours = '{:02d}:{}-{:02d}:{}'.format(
                f_hr,
                f_min,
                t_hr,
                t_min,
            )

            if not this_day_group:
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day

        day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]['hours'] in ('00:00-23:59', '00:00-00:00'):
            opening_hours = '24/7'
        else:
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                elif day_group['from_day'] == 'Su' and day_group['to_day'] == 'Sa':
                    opening_hours += '{hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        stores = json.loads(response.body_as_unicode())
        for store in stores:                                 
            properties = {                                   
                'ref': store['id'],                          
                'addr_full': store['address'],
                'city': store['city'],                       
                'state': store['state'],                     
                'postcode': store['postal'],                    
                'lat': store['lat'],                         
                'lon': store['lng'],                         
                'phone': store['phone'],
            }                                                
            
            if store['twentyfourhours']:
                properties['opening_hours'] = '24/7'
            elif 'hours' in store:
                hours = store['hours']
                if not all(hours[d] == '' for d in hours):
                    days_hours = []
                    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                        days_hours.append([
                            self.dayMap[day],
                            hours[day].lower().replace(' ', '')
                        ])
                    properties['opening_hours'] = self.opening_hours(days_hours)
                                                                 
            yield GeojsonPointItem(**properties)             


