# Product label profiles

Pool Chem's built-in calculator models generic chemicals. A household label can
instead be entered in **Settings → Devices & Services → Pool Chemistry → Configure
→ Product label profiles (JSON)**. The profile is saved with that Pool Chem entry,
so the pool and spa can use different products and label rules. Dose sensors remain
off by default for spas; opt in only for a product profile whose label has been
checked.

The profile JSON supports three label rules:

- `acid` and `ph_up`: `label_table`, a pH-band amount scaled by `per_gallons`.
  Add `minimum_total_alkalinity` when the product label has that prerequisite.
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
30 minutes of circulation before retesting. Enhanced Shock's dose is 3 tablespoons
per 500 gallons; at 335 gallons it rounds to 2 tablespoons. Label notes and
the supplied product identity are shown with calculated results.

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

Product label references: [SpaGuard pH Decreaser](https://www.thepoolandspahouse.com/shop/Brands/SpaGuard/PH-DECREASER), [SpaGuard Total Alkalinity Increaser](https://www.thepoolandspahouse.com/shop/Public/Spa-Supplies/SpaGuard/TOTAL-ALKALINITY-INCREASER), and [SpaGuard pH Increaser](https://www.thepoolandspahouse.com/shop/Public/Spa-Supplies/SpaGuard/PH-INCREASER). Enhanced Shock's 3-tablespoon rate comes from the back-label image Luke supplied; use the household container's current label if its formulation or directions differ.

SpaGuard pH Increaser's direction is to use an alkali-demand test and not exceed
1 ounce per 500 gallons in one addition; it does not provide the fixed pH-band
table needed for automatic calculation. Do not add a `ph_up` table unless the
chosen product's label actually provides that table. The generic calculator path
is separate and must not be described as label-backed. The 20% muriatic acid
selector is available for products with that stated concentration; the product
label and supplied concentration still need to match before that selector is used.

## Safety and limits

- A product profile contains a dosing rule; it is not a pump/dispensing command.
- Current formula numeric examples in `pypoolchem` are still under investigation.
  Label-table/linear/fixed profiles bypass that formula only for the explicitly
  configured dose categories.
- The product label's test prerequisites, max-per-addition caps, mixing warnings,
  and re-entry instructions remain authoritative. A timer is not a water test.
- Keep pools and spas as separate integration entries and maintain a separate
  profile for each actual product. Do not copy a spa rule to a pool product.
