## Matching to Name Suggestion Index

We attempt to match scraped `Items` against the Name Suggestion Index ([NSI](https://nsi.guide/)) project.
This is done automatically in the `ApplyNSICategoriesPipeline`.
Please don't manually set `nsi_id` as they are not stable and will change over time.

When we successfully match, the pipeline code applies the `nsi_id` and other NSI attributes to the `Item`, not overriding the attributes set by the `Spider` code.
This allows us to get multilingual `brand` tags, default attributes such as `takeaway`, and in some cases override categories.

### Categories

We prefer to get category information from Name Suggestion Index to make maintenance easier.
Brands may occasionally get moved between categories, e.g. [Guzman y Gomez](https://github.com/osmlab/name-suggestion-index/pull/9160) moved from `amenity=restaurant` to `amenity=fast_food`.
Getting the category automatically means we don't have to keep up with this, e.g. [Kokoro](https://github.com/alltheplaces/alltheplaces/pull/7569).

When there are multiple entries in NSI for a given brand, we have to apply a category in spider.
This is typically an issue with fuel stations/advertising totems and banks/ATMs, however it is also an issue for bigger brands that have POIs across multiple categories.

The helper function `apply_category` should be used when possible, along with a category from the `Categories` enum.

### NSI ID

There are times when NSI may be wrong or missing a specific brand or brand/category combination.
Where possible please try to edit NSI, taking note of [their requirements](https://github.com/osmlab/name-suggestion-index/wiki) and Wikidata notability requirements.

When we need to disable NSI matching, it can be done per POI with `nsi_id = "N/A"` or on the whole spider with:

```python
custom_settings = {
    "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None}
}
```
