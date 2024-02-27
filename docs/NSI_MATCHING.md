## NSI Matching

We attempt to match Items against [NSI](https://nsi.guide/).
This is done automatically in `ApplyNSICategoriesPipeline`, please don't manually set `nsi_id` as they aren't stable.

When we successfully match, we apply `nsi_id` and the NSI attributes to the Item, not overriding the Spider given attributes.
This allows us to get multilingual `brand` tags, default attributes such as `takeaway`, and in many cases categories.

### Categories

Getting categories from NSI has one main advantage, maintenance.
Brands may occasionally get moved between categories, e.g. [Guzman y Gomez](https://github.com/osmlab/name-suggestion-index/pull/9160) moved from `amenity=restaurant` to `amenity=fast_food`.
Getting the category automatically means we don't have to keep up with this, e.g. [Kokoro](https://github.com/alltheplaces/alltheplaces/pull/7569).

There are multiple entries in NSI for a given brand we have to apply a category in spider.
This is typically an issue with fuel stations/advertising totems and banks/ATMs, however it is also an issue for bigger
brands that have POIs across multiple categories.

`apply_category` should be used when possible, along with a category from the `Catrgories` enum.

### NSI ID

There are times when NSI may be wrong or missing a specific brand or brand/category combination.
Where possible please try to edit NSI, taking note of [their requirements](https://github.com/osmlab/name-suggestion-index/wiki) and Wikidata nobility requirements.

When we need to disable NSI matching, it can be done per POI with `nsi_id = "N/A"` or on the whole spider with:

```python
custom_settings = {
    "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None}
}
```
