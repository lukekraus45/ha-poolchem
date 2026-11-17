# Product label profiles

Pool Chem's built-in calculator models generic chemicals. A household label can
instead be entered in **Settings → Devices & Services → Pool Chemistry → Configure
→ Product label profiles (JSON)**. The profile is saved with that Pool Chem entry,
so the pool and spa can use different products and label rules. Dose sensors remain
off by default for spas; opt in only for a product profile whose label has been
checked.

The profile JSON supports these label rules:

- `acid` and `ph_up`: `label_table`, a pH-band amount scaled by `per_gallons`
  or interpolated between printed label volume rows.
  Add `minimum_total_alkalinity` when the product label has that prerequisite.
  A row may instead use `ph_value` for an exact pH chart entry; unmatched values
  produce no dose rather than interpolating between unsupported pH instructions.
- `alkalinity`: `label_linear`, with `amount` per `per_gallons` gallons for each
  `raises_ppm` increase.
- `chlorine`, `calcium`, `cya`, `salt`, and `borates`: `label_linear` with the same
  amount/per-volume/effect fields, using that product's label rate.
- `shock`: `label_fixed`, the printed amount per `per_gallons` gallons. This is a
  separate oxidizer dose, not a free-chlorine target dose.

An optional `chemical_type` selects the underlying Pool Chem ingredient type;
`strength_percent`, `active_ingredient`, and `label_source` retain the selected
product evidence for readback. `unit` is the label's measuring unit. `wait_minutes`
is retained in the dose note. Table rows use inclusive pH endpoints and are checked
in listed order, so keep them ordered from low to high. A table can intentionally
have adjacent endpoints; the earlier row wins on the shared boundary.
`round_to` rounds the result to a practical measuring increment. `max_amount` plus
`max_per_gallons` caps a single addition at a label's volume-scaled limit.

## Current SpaGuard product labels

This example encodes the current Coast spa stock from the supplied label data. The
SpaGuard pH Decreaser chart requires total alkalinity at least 125 ppm and calls for
30 minutes of circulation before retesting. SpaGuard pH Increaser has an exact
pH chart; printed gallon rows are interpolated only between 100 and 400 gallons,
and values not listed by the label do not get an automatic dose. Enhanced Shock's dose is 3
tablespoons per 500 gallons; at 335 gallons it rounds to 2 tablespoons. Label
notes and the supplied product identity are shown with calculated results.

```json
{
  "acid": {
    "product_name": "SpaGuard pH Decreaser",
    "active_ingredient": "Sodium bisulfate",
    "strength_percent": 93.2,
    "chemical_type": "dry_acid",
    "method": "label_table",
    "unit": "tsp",
    "round_to": 0.25,
    "per_gallons": 200,
    "minimum_total_alkalinity": 125,
    "wait_minutes": 30,
    "label_source": "SpaGuard package directions",
    "dose_table": [
      {"ph_min": 7.6, "ph_max": 7.8, "amount": 0.5},
      {"ph_min": 7.8, "ph_max": 8.0, "amount": 0.75},
      {"ph_min": 8.0, "ph_max": 8.4, "amount": 1.5},
      {"ph_min": 8.4, "ph_max": 14.0, "amount": 2.0}
    ]
  },
  "ph_up": {
    "product_name": "SpaGuard pH Increaser",
    "active_ingredient": "Sodium carbonate",
    "strength_percent": 100,
    "chemical_type": "soda_ash",
    "method": "label_table",
    "unit": "tsp",
    "round_to": 0.25,
    "wait_minutes": 30,
    "label_source": "SpaGuard bottle back-label image, SKU 42632BIO",
    "dose_table": [
      {"ph_min": 0, "ph_max": 7.1999, "volume_table": [
        {"gallons": 100, "amount": 2}, {"gallons": 200, "amount": 3},
        {"gallons": 300, "amount": 4}, {"gallons": 400, "amount": 6}
      ]},
      {"ph_value": 7.2, "volume_table": [
        {"gallons": 100, "amount": 1}, {"gallons": 200, "amount": 2},
        {"gallons": 300, "amount": 3}, {"gallons": 400, "amount": 4}
      ]},
      {"ph_value": 7.3, "volume_table": [
        {"gallons": 100, "amount": 0.5}, {"gallons": 200, "amount": 1},
        {"gallons": 300, "amount": 1.5}, {"gallons": 400, "amount": 2}
      ]}
    ]
  },
  "alkalinity": {
    "product_name": "SpaGuard Total Alkalinity Increaser",
    "active_ingredient": "Sodium bicarbonate",
    "strength_percent": 100,
    "chemical_type": "baking_soda",
    "method": "label_linear",
    "amount": 3,
    "unit": "tsp",
    "round_to": 0.25,
    "per_gallons": 100,
    "raises_ppm": 25,
    "label_source": "SpaGuard package directions"
  },
  "shock": {
    "product_name": "SpaGuard Enhanced Shock",
    "active_ingredient": "Dichlor",
    "strength_percent": 58.2,
    "chemical_type": "dichlor",
    "method": "label_fixed",
    "amount": 3,
    "unit": "tbsp",
    "round_to": 0.25,
    "per_gallons": 500,
    "wait_minutes": 30,
    "label_source": "SpaGuard package directions"
  }
}
```

Product label references: [SpaGuard pH Decreaser](https://www.hottubthings.com/products/spaguard-ph-decreaser-22-oz-42634bio), [SpaGuard pH Increaser back-label image (SKU 42632BIO)](https://www.hottubthings.com/cdn/shop/files/42632BIO2.jpg?v=1761688675&width=1946), and [SpaGuard Total Alkalinity Increaser](https://leisuretimeinc.com/products/spaguard-total-alkalinity-increaser). Enhanced Shock's 3-tablespoon rate comes from the back-label image Luke supplied; use the household container's current label if its formulation or directions differ.

The SpaGuard pH Increaser back-label image for SKU 42632BIO includes a discrete
table: at 100/200/300/400 gallons, the dose below pH 7.2 is 2/3/4/6 tsp; at pH
7.2 it is 1/2/3/4 tsp; at pH 7.3 it is 0.5/1/1.5/2 tsp; pH 7.4 or above has
no dose. At 335 gallons, interpolation between the printed 300 and 400 gallon
rows yields 4.7, 3.35, and 1.675 tsp, rounded to 4.75, 3.25, and 1.75 tsp.
The label calls for high-speed pump circulation for 30 minutes, a pH retest, and
periodic acid/alkali-demand testing. The preset returns no dose for unlisted pH
values or volumes outside 100–400 gallons. One dealer transcription of older product directions
conflicts with this photographed chart, so the SpaGuard preset uses the pictured
SKU-matched label. The 20% muriatic acid selector is available for products with
that stated concentration; the product label and supplied concentration still
need to match before that selector is used.

## Safety and limits

- A product profile contains a dosing rule; it is not a pump/dispensing command.
- Current formula numeric examples in `pypoolchem` are still under investigation.
  Label-table/linear/fixed profiles bypass that formula only for the explicitly
  configured dose categories.
- The product label's test prerequisites, max-per-addition caps, mixing warnings,
  and re-entry instructions remain authoritative. A timer is not a water test.
- Keep pools and spas as separate integration entries and maintain a separate
  profile for each actual product. Do not copy a spa rule to a pool product.
