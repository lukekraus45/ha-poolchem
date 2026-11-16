"""Constants for Pool Chemistry integration."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

DOMAIN: Final = "poolchem"
VERSION: Final = "0.2.0"

# Config entry keys - Pool configuration
CONF_POOL_NAME: Final = "pool_name"
CONF_VOLUME_GALLONS: Final = "volume_gallons"
CONF_POOL_TYPE: Final = "pool_type"
CONF_WATER_BODY_TYPE: Final = "water_body_type"
CONF_SURFACE_TYPE: Final = "surface_type"

# Config entry keys - Entity mapping
CONF_TEMP_ENTITY: Final = "temp_entity"
CONF_PH_ENTITY: Final = "ph_entity"
CONF_FC_ENTITY: Final = "fc_entity"
CONF_TA_ENTITY: Final = "ta_entity"
CONF_CH_ENTITY: Final = "ch_entity"
CONF_CYA_ENTITY: Final = "cya_entity"
CONF_SALT_ENTITY: Final = "salt_entity"
CONF_TDS_ENTITY: Final = "tds_entity"
CONF_BORATES_ENTITY: Final = "borates_entity"

# Config entry keys - Target overrides (options flow)
CONF_TARGET_PH: Final = "target_ph"
CONF_TARGET_FC: Final = "target_fc"
CONF_TARGET_TA: Final = "target_ta"
CONF_TARGET_CH: Final = "target_ch"
CONF_TARGET_CYA: Final = "target_cya"
CONF_TARGET_SALT: Final = "target_salt"
CONF_TARGET_BORATES: Final = "target_borates"

# Config entry keys - Chemical configuration (options flow)
CONF_ACID_TYPE: Final = "acid_type"
CONF_CHLORINE_TYPE: Final = "chlorine_type"
CONF_PH_UP_TYPE: Final = "ph_up_type"
CONF_PRODUCT_PROFILES: Final = "product_profiles_json"
CONF_PRODUCT_PRESET: Final = "product_preset"

# Config entry keys - Enabled dosing sensors (options flow)
CONF_ENABLE_DOSE_ACID: Final = "enable_dose_acid"
CONF_ENABLE_DOSE_CHLORINE: Final = "enable_dose_chlorine"
CONF_ENABLE_DOSE_ALKALINITY: Final = "enable_dose_alkalinity"
CONF_ENABLE_DOSE_CALCIUM: Final = "enable_dose_calcium"
CONF_ENABLE_DOSE_CYA: Final = "enable_dose_cya"
CONF_ENABLE_DOSE_SALT: Final = "enable_dose_salt"
CONF_ENABLE_DOSE_BORATES: Final = "enable_dose_borates"
CONF_ENABLE_DOSE_SHOCK: Final = "enable_dose_shock"
CONF_ENABLE_DOSE_PH_UP: Final = "enable_dose_ph_up"

# Required entity keys (for iteration)
REQUIRED_ENTITIES: Final = [
    CONF_TEMP_ENTITY,
    CONF_PH_ENTITY,
    CONF_FC_ENTITY,
    CONF_TA_ENTITY,
    CONF_CH_ENTITY,
]

# Optional entity keys (for iteration)
OPTIONAL_ENTITIES: Final = [
    CONF_CYA_ENTITY,
    CONF_SALT_ENTITY,
    CONF_TDS_ENTITY,
    CONF_BORATES_ENTITY,
]

# All entity keys
ALL_ENTITY_KEYS: Final = REQUIRED_ENTITIES + OPTIONAL_ENTITIES


class PoolType(StrEnum):
    """Pool sanitization types."""

    CHLORINE = "chlorine"
    SALTWATER = "saltwater"
    MINERAL = "mineral"


class WaterBodyType(StrEnum):
    """Water body being analyzed; distinct from its sanitizer system."""

    POOL = "pool"
    SPA = "spa"


class SurfaceType(StrEnum):
    """Pool surface types."""

    PLASTER = "plaster"
    PEBBLE = "pebble"
    VINYL = "vinyl"
    FIBERGLASS = "fiberglass"
    PAINTED = "painted"


class WaterBalanceState(StrEnum):
    """Water balance states based on CSI thresholds (TFP methodology)."""

    SEVERELY_CORROSIVE = "severely_corrosive"  # CSI < -0.6
    SLIGHTLY_CORROSIVE = "slightly_corrosive"  # -0.6 <= CSI < -0.3
    BALANCED = "balanced"  # -0.3 <= CSI <= +0.3
    SLIGHTLY_SCALING = "slightly_scaling"  # +0.3 < CSI <= +0.6
    SEVERELY_SCALING = "severely_scaling"  # CSI > +0.6
    UNKNOWN = "unknown"  # Insufficient data


# CSI thresholds for water balance state (TFP methodology)
CSI_SEVERELY_CORROSIVE: Final = -0.6
CSI_SLIGHTLY_CORROSIVE: Final = -0.3
CSI_BALANCED_LOW: Final = -0.3
CSI_BALANCED_HIGH: Final = 0.3
CSI_SLIGHTLY_SCALING: Final = 0.6

# Default target values (from pypoolchem traditional pool targets)
DEFAULT_TARGET_PH: Final = 7.5
DEFAULT_TARGET_FC: Final = 5.0
DEFAULT_TARGET_TA: Final = 80
DEFAULT_TARGET_CH: Final = 350
DEFAULT_TARGET_CYA: Final = 40
DEFAULT_TARGET_SALT: Final = 3200
DEFAULT_TARGET_BORATES: Final = 50  # 50ppm is a common target for borate users

# Default optional sensor values when not configured
DEFAULT_CYA: Final = 0
DEFAULT_SALT: Final = 0
DEFAULT_TDS: Final = 1000
DEFAULT_BORATES: Final = 0

# Sensor keys
SENSOR_CSI: Final = "csi"
SENSOR_LSI: Final = "lsi"
SENSOR_WATER_BALANCE: Final = "water_balance"
SENSOR_TARGET_CSI: Final = "target_csi"
SENSOR_TARGET_LSI: Final = "target_lsi"
SENSOR_TARGET_WATER_BALANCE: Final = "target_water_balance"
SENSOR_FC_CYA_RATIO: Final = "fc_cya_ratio"
SENSOR_DOSE_ACID: Final = "dose_acid"
SENSOR_DOSE_CHLORINE: Final = "dose_chlorine"
SENSOR_DOSE_ALKALINITY: Final = "dose_alkalinity"
SENSOR_DOSE_CALCIUM: Final = "dose_calcium"
SENSOR_DOSE_CYA: Final = "dose_cya"
SENSOR_DOSE_SALT: Final = "dose_salt"
SENSOR_DOSE_BORATES: Final = "dose_borates"
SENSOR_DOSE_SHOCK: Final = "dose_shock"
SENSOR_DOSE_PH_UP: Final = "dose_ph_up"

# Acid chemical types (mapped to pypoolchem ChemicalType)
ACID_MURIATIC_14_5: Final = "muriatic_14_5"
ACID_MURIATIC_20: Final = "muriatic_20"
ACID_MURIATIC_28_3: Final = "muriatic_28_3"
ACID_MURIATIC_31_45: Final = "muriatic_31_45"
ACID_MURIATIC_34_6: Final = "muriatic_34_6"
ACID_DRY_ACID: Final = "dry_acid"

DEFAULT_ACID_TYPE: Final = ACID_MURIATIC_31_45

ACID_TYPE_OPTIONS: Final = [
    ACID_MURIATIC_14_5,
    ACID_MURIATIC_20,
    ACID_MURIATIC_28_3,
    ACID_MURIATIC_31_45,
    ACID_MURIATIC_34_6,
    ACID_DRY_ACID,
]

# Chlorine chemical types (mapped to pypoolchem ChemicalType)
CHLORINE_BLEACH_6: Final = "bleach_6"
CHLORINE_BLEACH_8_25: Final = "bleach_8_25"
CHLORINE_BLEACH_10: Final = "bleach_10"
CHLORINE_BLEACH_12_5: Final = "bleach_12_5"
CHLORINE_CAL_HYPO_65: Final = "cal_hypo_65"
CHLORINE_CAL_HYPO_73: Final = "cal_hypo_73"
CHLORINE_DICHLOR: Final = "dichlor"
CHLORINE_TRICHLOR: Final = "trichlor"

DEFAULT_CHLORINE_TYPE: Final = CHLORINE_BLEACH_12_5

CHLORINE_TYPE_OPTIONS: Final = [
    CHLORINE_BLEACH_6,
    CHLORINE_BLEACH_8_25,
    CHLORINE_BLEACH_10,
    CHLORINE_BLEACH_12_5,
    CHLORINE_CAL_HYPO_65,
    CHLORINE_CAL_HYPO_73,
    CHLORINE_DICHLOR,
    CHLORINE_TRICHLOR,
]

# pH up chemical types
PH_UP_SODA_ASH: Final = "soda_ash"
PH_UP_BORAX: Final = "borax"

DEFAULT_PH_UP_TYPE: Final = PH_UP_SODA_ASH

PH_UP_TYPE_OPTIONS: Final = [
    PH_UP_SODA_ASH,
    PH_UP_BORAX,
]

PRODUCT_PRESET_NONE: Final = "none"
PRODUCT_PRESET_SPAGUARD_SPA: Final = "spaguard_spa"
PRODUCT_PRESET_OPTIONS: Final = [PRODUCT_PRESET_NONE, PRODUCT_PRESET_SPAGUARD_SPA]

# Default dosing sensor enablement
DEFAULT_ENABLE_DOSE_ACID: Final = True
DEFAULT_ENABLE_DOSE_CHLORINE: Final = True
DEFAULT_ENABLE_DOSE_ALKALINITY: Final = True
DEFAULT_ENABLE_DOSE_CALCIUM: Final = True
DEFAULT_ENABLE_DOSE_CYA: Final = True
DEFAULT_ENABLE_DOSE_SALT: Final = False  # Only for saltwater pools
DEFAULT_ENABLE_DOSE_BORATES: Final = False  # Not all pools use borates
DEFAULT_ENABLE_DOSE_SHOCK: Final = False  # Requires a label-backed product profile
DEFAULT_ENABLE_DOSE_PH_UP: Final = True


def default_dose_enabled(water_body_type: str, option: str) -> bool:
    """Return safe dosing defaults for a water body.

    Spa dose sensors require explicit opt-in because target and sanitizer
    assumptions differ from pool calculations.
    """
    if water_body_type == WaterBodyType.SPA:
        return False

    return {
        CONF_ENABLE_DOSE_ACID: DEFAULT_ENABLE_DOSE_ACID,
        CONF_ENABLE_DOSE_CHLORINE: DEFAULT_ENABLE_DOSE_CHLORINE,
        CONF_ENABLE_DOSE_ALKALINITY: DEFAULT_ENABLE_DOSE_ALKALINITY,
        CONF_ENABLE_DOSE_CALCIUM: DEFAULT_ENABLE_DOSE_CALCIUM,
        CONF_ENABLE_DOSE_CYA: DEFAULT_ENABLE_DOSE_CYA,
        CONF_ENABLE_DOSE_SALT: DEFAULT_ENABLE_DOSE_SALT,
        CONF_ENABLE_DOSE_BORATES: DEFAULT_ENABLE_DOSE_BORATES,
        CONF_ENABLE_DOSE_SHOCK: DEFAULT_ENABLE_DOSE_SHOCK,
        CONF_ENABLE_DOSE_PH_UP: DEFAULT_ENABLE_DOSE_PH_UP,
    }[option]
