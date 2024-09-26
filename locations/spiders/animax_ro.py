from locations.storefinders.elfsight import ElfsightSpider


class AnimaxROSpider(ElfsightSpider):
    name = "animax_ro"
    item_attributes = {"brand": "Animax", "brand_wikidata": "Q119440709"}
    host = "shy.elfsight.com"
    shop = "animaxro.myshopify.com"
    api_key = "73d5edfc-9672-4567-b102-02ef8265ef7e"
    no_refs = True

    def post_process_item(self, item, response, location):
        item["street_address"] = location.pop("position")
        # TODO: Parse hours from:
        #  'infoDescription': 'Drumul Ciorogârla 295-291&nbsp;Jud. Ilfov\nPetshop &amp; punct farmaceutic<div><br></div><div>☎&nbsp;0725.888.814</div><div>✉ chiajna@animax.ro </div><div><br></div><div>Luni 09:00 AM - 09:00 PM</div><div>Marti 09:00 AM - 
        #  09:00 PM</div><div>Miercuri 09:00 AM - 09:00 PM</div><div>Joi 09:00 AM - 09:00 PM</div>
        #  <div>Vineri 09:00 AM - 09:00 PM</div><div>Sambata 09:00 AM - 09:00 PM</div><div>Duminica 09:00 AM - 07:00 PM</div>', 
        yield item
         
