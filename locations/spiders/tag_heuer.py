from locations.storefinders.algolia import AlgoliaSpider


class TagHeuerSpider(AlgoliaSpider):
    name = "tag_heuer"
    item_attributes = {
        "brand_wikidata": "Q645984",
        "brand": "TAG Heuer",
    }
    api_key = "8cf40864df513111d39148923f754024"
    app_id = "6OBGA4VJKI"
    index_name = "stores"
    myfilter = "type:TAGSTORE"

    # {"params":"filters=products.mechanicalWatches:true AND country:GB&attributesToRetrieve=address,Latitude,zip,country,phone,type,id,image,address2,email,name,description,services,payments,city,openingHours,exceptionalHours,_geoloc,i18nAddress,image1,timezone,sfccUrl","aroundRadius":"15000","hitsPerPage":"1000","getRankingInfo":"1","attributesToRetrieve":"address,Latitude,zip,country,phone,type,id,image,address2,email,name,description,services,payments,city,openingHours,exceptionalHours,_geoloc,i18nAddress,image1,timezone,sfccUrl","attributesToHighlight":"name"}

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        item["ref"] = feature["objectID"]
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["image"] = feature["image"]
        slug = feature["sfccUrl"]
        item["website"] = f"https://www.tagheuer.com/{slug}"
        # if "boutique-tag-heuer" in slug:
        yield item
