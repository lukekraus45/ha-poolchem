"""DataUpdateCoordinator for Pool Chemistry integration.

This coordinator is event-driven - it recalculates chemistry when source
sensor entities change, rather than polling on a fixed interval.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from pypoolchem import (
    ChemicalType,
    WaterChemistry,
    calculate_alkalinity_dose,
    calculate_borate_dose,
    calculate_calcium_dose,
    calculate_chlorine_dose,
    calculate_csi,
    calculate_cya_dose,
    calculate_lsi,
    calculate_ph_dose,
    calculate_salt_dose,
)
from pypoolchem.dosing.calculator import DosingResult

from .const import (
    ACID_DRY_ACID,
    ACID_MURIATIC_14_5,
    ACID_MURIATIC_20,
    ACID_MURIATIC_28_3,
    ACID_MURIATIC_31_45,
    ACID_MURIATIC_34_6,
    ALL_ENTITY_KEYS,
    CHLORINE_BLEACH_6,
    CHLORINE_BLEACH_8_25,
    CHLORINE_BLEACH_10,
    CHLORINE_BLEACH_12_5,
    CHLORINE_CAL_HYPO_65,
    CHLORINE_CAL_HYPO_73,
    CHLORINE_DICHLOR,
    CHLORINE_TRICHLOR,
    CONF_ACID_TYPE,
    CONF_BORATES_ENTITY,
    CONF_CH_ENTITY,
    CONF_CHLORINE_TYPE,
    CONF_CYA_ENTITY,
    CONF_ENABLE_DOSE_ACID,
    CONF_ENABLE_DOSE_ALKALINITY,
    CONF_ENABLE_DOSE_BORATES,
    CONF_ENABLE_DOSE_CALCIUM,
    CONF_ENABLE_DOSE_CHLORINE,
    CONF_ENABLE_DOSE_CYA,
    CONF_ENABLE_DOSE_PH_UP,
    CONF_ENABLE_DOSE_SALT,
    CONF_ENABLE_DOSE_SHOCK,
    CONF_FC_ENTITY,
    CONF_PH_ENTITY,
    CONF_PH_UP_TYPE,
    CONF_POOL_NAME,
    CONF_POOL_TYPE,
    CONF_PRODUCT_PRESET,
    CONF_PRODUCT_PROFILES,
    CONF_SALT_ENTITY,
    CONF_TA_ENTITY,
    CONF_TARGET_BORATES,
    CONF_TARGET_CH,
    CONF_TARGET_CYA,
    CONF_TARGET_FC,
    CONF_TARGET_PH,
    CONF_TARGET_SALT,
    CONF_TARGET_TA,
    CONF_TDS_ENTITY,
    CONF_TEMP_ENTITY,
    CONF_VOLUME_GALLONS,
    CONF_WATER_BODY_TYPE,
    CSI_BALANCED_HIGH,
    CSI_BALANCED_LOW,
    CSI_SEVERELY_CORROSIVE,
    CSI_SLIGHTLY_SCALING,
    DEFAULT_ACID_TYPE,
    DEFAULT_BORATES,
    DEFAULT_CHLORINE_TYPE,
    DEFAULT_CYA,
    DEFAULT_ENABLE_DOSE_ACID,
    DEFAULT_ENABLE_DOSE_ALKALINITY,
    DEFAULT_ENABLE_DOSE_BORATES,
    DEFAULT_ENABLE_DOSE_CALCIUM,
    DEFAULT_ENABLE_DOSE_CHLORINE,
    DEFAULT_ENABLE_DOSE_CYA,
    DEFAULT_ENABLE_DOSE_PH_UP,
    DEFAULT_ENABLE_DOSE_SALT,
    DEFAULT_ENABLE_DOSE_SHOCK,
    DEFAULT_PH_UP_TYPE,
    DEFAULT_SALT,
    DEFAULT_TARGET_BORATES,
    DEFAULT_TARGET_CH,
    DEFAULT_TARGET_CYA,
    DEFAULT_TARGET_FC,
    DEFAULT_TARGET_PH,
    DEFAULT_TARGET_SALT,
    DEFAULT_TARGET_TA,
    DEFAULT_TDS,
    DOMAIN,
    PH_UP_BORAX,
    PH_UP_SODA_ASH,
    PoolType,
    WaterBalanceState,
    WaterBodyType,
)
from .product_profiles import (
    label_fixed_dose,
    label_linear_dose,
    label_table_dose,
    load_product_profiles,
    profile_chemical_type,
)

_LOGGER = logging.getLogger(__name__)

# Mapping from const acid types to pypoolchem ChemicalType
ACID_TYPE_MAP: dict[str, ChemicalType] = {
    ACID_MURIATIC_14_5: ChemicalType.MURIATIC_ACID_14_5,
    ACID_MURIATIC_20: ChemicalType.MURIATIC_ACID_20,
    ACID_MURIATIC_28_3: ChemicalType.MURIATIC_ACID_28_3,
    ACID_MURIATIC_31_45: ChemicalType.MURIATIC_ACID_31_45,
    ACID_MURIATIC_34_6: ChemicalType.MURIATIC_ACID_34_6,
    ACID_DRY_ACID: ChemicalType.DRY_ACID,
}

PH_UP_TYPE_MAP: dict[str, ChemicalType] = {
    PH_UP_SODA_ASH: ChemicalType.SODA_ASH,
    PH_UP_BORAX: ChemicalType.BORAX,
}

# Mapping from const chlorine types to pypoolchem ChemicalType
CHLORINE_TYPE_MAP: dict[str, ChemicalType] = {
    CHLORINE_BLEACH_6: ChemicalType.BLEACH_6,
    CHLORINE_BLEACH_8_25: ChemicalType.BLEACH_8_25,
    CHLORINE_BLEACH_10: ChemicalType.BLEACH_10,
    CHLORINE_BLEACH_12_5: ChemicalType.BLEACH_12_5,
    CHLORINE_CAL_HYPO_65: ChemicalType.CAL_HYPO_65,
    CHLORINE_CAL_HYPO_73: ChemicalType.CAL_HYPO_73,
    CHLORINE_DICHLOR: ChemicalType.DICHLOR,
    CHLORINE_TRICHLOR: ChemicalType.TRICHLOR,
}


@dataclass
class PoolChemData:
    """Container for calculated pool chemistry data."""

    # Water chemistry snapshot
    water: WaterChemistry | None = None

    # Water balance indices
    csi: float | None = None
    lsi: float | None = None
    balance_state: WaterBalanceState = WaterBalanceState.UNKNOWN

    # Target water balance indices (what CSI/LSI would be if targets achieved)
    target_csi: float | None = None
    target_lsi: float | None = None
    target_balance_state: WaterBalanceState = WaterBalanceState.UNKNOWN

    # FC/CYA relationship
    fc_cya_ratio: float | None = None
    fc_is_adequate: bool | None = None

    # Dosing recommendations
    dose_acid: DosingResult | None = None
    dose_ph_up: DosingResult | None = None
    dose_chlorine: DosingResult | None = None
    dose_alkalinity: DosingResult | None = None
    dose_calcium: DosingResult | None = None
    dose_cya: DosingResult | None = None
    dose_salt: DosingResult | None = None
    dose_borates: DosingResult | None = None
    dose_shock: DosingResult | None = None

    # Metadata
    last_updated: datetime | None = None
    errors: list[str] | None = None


class PoolChemCoordinator(DataUpdateCoordinator[PoolChemData]):
    """Coordinator for pool chemistry calculations.

    This coordinator listens to state changes from source sensor entities
    and recalculates chemistry values when they change.
    """

    config_entry: ConfigEntry
    _unsubscribe: Callable[[], None] | None = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            entry: Config entry for this integration instance.
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=None,  # Event-driven only
        )
        self.config_entry = entry
        self.product_profiles = load_product_profiles(
            entry.options.get(CONF_PRODUCT_PRESET),
            entry.options.get(CONF_PRODUCT_PROFILES),
        )
        self._entity_map: dict[str, str | None] = self._build_entity_map()

    def _build_entity_map(self) -> dict[str, str | None]:
        """Build mapping of config keys to entity IDs."""
        data = self.config_entry.data
        return {key: data.get(key) for key in ALL_ENTITY_KEYS}

    @property
    def pool_name(self) -> str:
        """Return the pool name."""
        return str(self.config_entry.data.get(CONF_POOL_NAME, "Pool"))

    @property
    def pool_volume(self) -> int:
        """Return the pool volume in gallons."""
        return int(self.config_entry.data.get(CONF_VOLUME_GALLONS, 15000))

    @property
    def pool_type(self) -> PoolType:
        """Return the pool type."""
        return PoolType(self.config_entry.data.get(CONF_POOL_TYPE, PoolType.CHLORINE))

    @property
    def is_saltwater(self) -> bool:
        """Return True if this is a saltwater pool."""
        return self.pool_type == PoolType.SALTWATER

    @property
    def is_spa(self) -> bool:
        """Return True when this entry represents a spa/hot tub."""
        return (
            self.config_entry.data.get(CONF_WATER_BODY_TYPE, WaterBodyType.POOL)
            == WaterBodyType.SPA
        )

    def _get_option(self, key: str, default: Any) -> Any:
        """Get option value from options, falling back to default.

        Options contain targets, chemical types, and dosing toggles.
        These are set during initial config flow and editable via options flow.
        """
        return self.config_entry.options.get(key, default)

    def _get_target(self, key: str, default: float) -> float:
        """Get target value from options."""
        return float(self._get_option(key, default))

    @property
    def target_ph(self) -> float:
        """Return target pH."""
        return self._get_target(CONF_TARGET_PH, DEFAULT_TARGET_PH)

    @property
    def target_fc(self) -> float:
        """Return target free chlorine."""
        return self._get_target(CONF_TARGET_FC, DEFAULT_TARGET_FC)

    @property
    def target_ta(self) -> float:
        """Return target total alkalinity."""
        return self._get_target(CONF_TARGET_TA, DEFAULT_TARGET_TA)

    @property
    def target_ch(self) -> float:
        """Return target calcium hardness."""
        return self._get_target(CONF_TARGET_CH, DEFAULT_TARGET_CH)

    @property
    def target_cya(self) -> float:
        """Return target cyanuric acid."""
        return self._get_target(CONF_TARGET_CYA, DEFAULT_TARGET_CYA)

    @property
    def target_salt(self) -> float:
        """Return target salt level."""
        return self._get_target(CONF_TARGET_SALT, DEFAULT_TARGET_SALT)

    @property
    def target_borates(self) -> float:
        """Return target borates level."""
        return self._get_target(CONF_TARGET_BORATES, DEFAULT_TARGET_BORATES)

    def _get_acid_chemical_type(self) -> ChemicalType:
        """Get the configured acid chemical type."""
        acid_type = self._get_option(CONF_ACID_TYPE, DEFAULT_ACID_TYPE)
        return ACID_TYPE_MAP.get(acid_type, ChemicalType.MURIATIC_ACID_31_45)

    def _get_ph_up_chemical_type(self) -> ChemicalType:
        """Get the configured pH-raising chemical type."""
        ph_up_type = self._get_option(CONF_PH_UP_TYPE, DEFAULT_PH_UP_TYPE)
        return PH_UP_TYPE_MAP.get(ph_up_type, ChemicalType.SODA_ASH)

    def _get_chlorine_chemical_type(self) -> ChemicalType:
        """Get the configured chlorine chemical type."""
        chlorine_type = self._get_option(CONF_CHLORINE_TYPE, DEFAULT_CHLORINE_TYPE)
        return CHLORINE_TYPE_MAP.get(chlorine_type, ChemicalType.BLEACH_12_5)

    def _is_dose_enabled(self, key: str, default: bool) -> bool:
        """Check if a dosing sensor is enabled."""
        return bool(self._get_option(key, default))

    async def async_setup(self) -> None:
        """Set up event listeners for source entities."""
        entity_ids = [eid for eid in self._entity_map.values() if eid is not None]

        if not entity_ids:
            _LOGGER.warning("No source entities configured")
            return

        # Register state change listener and store unsubscribe callback
        self._unsubscribe = async_track_state_change_event(
            self.hass,
            entity_ids,
            self._handle_state_change,
        )

        # Initial data fetch
        await self.async_config_entry_first_refresh()

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and clean up listeners."""
        if hasattr(self, "_unsubscribe") and self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None
        await super().async_shutdown()

    @callback
    def _handle_state_change(self, event: Event[EventStateChangedData]) -> None:
        """Handle source entity state change."""
        entity_id = event.data["entity_id"]
        new_state = event.data["new_state"]

        _LOGGER.debug(
            "Source entity changed: %s -> %s",
            entity_id,
            new_state.state if new_state else "None",
        )

        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> PoolChemData:
        """Calculate pool chemistry from current entity states."""
        errors: list[str] = []
        data = PoolChemData(last_updated=dt_util.utcnow())

        # Get required values
        temp_f = self._get_temperature()
        ph = self._get_numeric(CONF_PH_ENTITY)
        fc = self._get_numeric(CONF_FC_ENTITY)
        ta = self._get_numeric(CONF_TA_ENTITY)
        ch = self._get_numeric(CONF_CH_ENTITY)

        # Get optional values with defaults
        cya = self._get_numeric(CONF_CYA_ENTITY) or DEFAULT_CYA
        salt = self._get_numeric(CONF_SALT_ENTITY) or DEFAULT_SALT
        tds = self._get_numeric(CONF_TDS_ENTITY) or DEFAULT_TDS
        borates = self._get_numeric(CONF_BORATES_ENTITY) or DEFAULT_BORATES

        # Check if we have enough data for water balance calculations
        can_calculate_balance = all(v is not None for v in [temp_f, ph, ta, ch])

        if can_calculate_balance:
            try:
                # We've verified these are not None in can_calculate_balance
                assert ph is not None
                assert temp_f is not None
                assert ta is not None
                assert ch is not None
                water = WaterChemistry(
                    ph=ph,
                    temperature_f=temp_f,
                    free_chlorine=fc or 0,
                    total_alkalinity=ta,
                    calcium_hardness=ch,
                    cyanuric_acid=cya,
                    salt=salt,
                    tds=tds,
                    borates=borates,
                )
                data.water = water

                # Calculate water balance indices
                data.csi = calculate_csi(water)
                data.lsi = calculate_lsi(water)
                data.balance_state = self._determine_balance_state(data.csi)

                # Calculate target water balance (what CSI/LSI would be with targets)
                target_water = WaterChemistry(
                    ph=self.target_ph,
                    temperature_f=temp_f,
                    free_chlorine=self.target_fc,
                    total_alkalinity=self.target_ta,
                    calcium_hardness=self.target_ch,
                    cyanuric_acid=self.target_cya,
                    salt=self.target_salt if self.is_saltwater else salt,
                    tds=tds,
                    borates=self.target_borates,
                )
                data.target_csi = calculate_csi(target_water)
                data.target_lsi = calculate_lsi(target_water)
                data.target_balance_state = self._determine_balance_state(
                    data.target_csi
                )

            except Exception as err:
                errors.append(f"Water balance calculation failed: {err}")
                _LOGGER.exception("Failed to calculate water balance")
        else:
            missing = []
            if temp_f is None:
                missing.append("temperature")
            if ph is None:
                missing.append("pH")
            if ta is None:
                missing.append("TA")
            if ch is None:
                missing.append("CH")
            errors.append(f"Missing required sensors: {', '.join(missing)}")

        # Calculate FC/CYA ratio if we have FC
        if not self.is_spa and fc is not None and cya > 0:
            data.fc_cya_ratio = (fc / cya) * 100
            # TFP recommends minimum FC/CYA ratio of 7.5% for traditional pools
            # and lower for SWG pools
            min_ratio = 5.0 if self.is_saltwater else 7.5
            data.fc_is_adequate = data.fc_cya_ratio >= min_ratio
        elif not self.is_spa and fc is not None and cya == 0:
            # No CYA means any FC is "adequate" but ratio is undefined
            data.fc_cya_ratio = None
            data.fc_is_adequate = fc > 0

        # Calculate dosing recommendations
        self._calculate_doses(data, temp_f, ph, fc, ta, ch, cya, salt, borates)

        data.errors = errors if errors else None
        return data

    def _get_temperature(self) -> float | None:
        """Get temperature in Fahrenheit, auto-converting from Celsius if needed."""
        entity_id = self._entity_map.get(CONF_TEMP_ENTITY)
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None

        try:
            value = float(state.state)
        except (ValueError, TypeError):
            return None

        # Check unit of measurement and convert if necessary
        unit = state.attributes.get("unit_of_measurement")
        if unit == UnitOfTemperature.CELSIUS:
            # Convert Celsius to Fahrenheit
            value = (value * 9 / 5) + 32

        return value

    def _get_numeric(self, key: str) -> float | None:
        """Get numeric value from entity state."""
        entity_id = self._entity_map.get(key)
        if not entity_id:
            return None

        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _determine_balance_state(self, csi: float) -> WaterBalanceState:
        """Determine water balance state from CSI using TFP thresholds."""
        if csi < CSI_SEVERELY_CORROSIVE:
            return WaterBalanceState.SEVERELY_CORROSIVE
        if csi < CSI_BALANCED_LOW:
            return WaterBalanceState.SLIGHTLY_CORROSIVE
        if csi <= CSI_BALANCED_HIGH:
            return WaterBalanceState.BALANCED
        if csi <= CSI_SLIGHTLY_SCALING:
            return WaterBalanceState.SLIGHTLY_SCALING
        return WaterBalanceState.SEVERELY_SCALING

    def _calculate_doses(
        self,
        data: PoolChemData,
        temp_f: float | None,
        ph: float | None,
        fc: float | None,
        ta: float | None,
        ch: float | None,
        cya: float,
        salt: float,
        borates: float,
    ) -> None:
        """Calculate dosing recommendations."""
        volume = self.pool_volume

        # pH/Acid dose
        if (
            self._is_dose_enabled(CONF_ENABLE_DOSE_ACID, DEFAULT_ENABLE_DOSE_ACID)
            and ph is not None
            and ta is not None
            and ph > self.target_ph
        ):
            try:
                temp = temp_f or 80  # Default temp if not available
                acid_profile = self.product_profiles.get("acid", {})
                if acid_profile.get("method") == "label_table":
                    data.dose_acid = label_table_dose(
                        acid_profile,
                        current_ph=ph,
                        total_alkalinity=ta,
                        volume_gallons=volume,
                        chemical_type=profile_chemical_type(
                            acid_profile, self._get_acid_chemical_type()
                        ),
                    )
                elif not self.is_spa:
                    data.dose_acid = calculate_ph_dose(
                        current_ph=ph,
                        target_ph=self.target_ph,
                        pool_gallons=volume,
                        total_alkalinity=ta,
                        temperature_f=temp,
                        borates=borates,
                        chemical_type=self._get_acid_chemical_type(),
                    )
            except Exception as err:
                _LOGGER.debug("pH dose calculation failed: %s", err)

        # Raising and lowering pH use different products and separate sensors.
        if (
            self._is_dose_enabled(CONF_ENABLE_DOSE_PH_UP, DEFAULT_ENABLE_DOSE_PH_UP)
            and ph is not None
            and ta is not None
            and ph < self.target_ph
        ):
            try:
                ph_up_profile = self.product_profiles.get("ph_up", {})
                if ph_up_profile.get("method") == "label_table":
                    data.dose_ph_up = label_table_dose(
                        ph_up_profile,
                        current_ph=ph,
                        total_alkalinity=ta,
                        volume_gallons=volume,
                        chemical_type=profile_chemical_type(
                            ph_up_profile, self._get_ph_up_chemical_type()
                        ),
                    )
                elif not self.is_spa:
                    data.dose_ph_up = calculate_ph_dose(
                        current_ph=ph,
                        target_ph=self.target_ph,
                        pool_gallons=volume,
                        total_alkalinity=ta,
                        temperature_f=temp_f or 80,
                        borates=borates,
                        chemical_type=self._get_ph_up_chemical_type(),
                    )
            except Exception as err:
                _LOGGER.debug("pH increaser dose calculation failed: %s", err)

        # Chlorine dose
        if (
            self._is_dose_enabled(
                CONF_ENABLE_DOSE_CHLORINE, DEFAULT_ENABLE_DOSE_CHLORINE
            )
            and fc is not None
        ):
            try:
                profile = self.product_profiles.get("chlorine", {})
                if profile.get("method") == "label_linear":
                    data.dose_chlorine = label_linear_dose(
                        profile,
                        current=fc,
                        target=self.target_fc,
                        volume_gallons=volume,
                        chemical_type=profile_chemical_type(
                            profile, self._get_chlorine_chemical_type()
                        ),
                    )
                else:
                    data.dose_chlorine = calculate_chlorine_dose(
                        current_fc=fc,
                        target_fc=self.target_fc,
                        pool_gallons=volume,
                        chemical_type=self._get_chlorine_chemical_type(),
                    )
            except Exception as err:
                _LOGGER.debug("Chlorine dose calculation failed: %s", err)

        # Alkalinity dose
        if (
            self._is_dose_enabled(
                CONF_ENABLE_DOSE_ALKALINITY, DEFAULT_ENABLE_DOSE_ALKALINITY
            )
            and ta is not None
        ):
            try:
                alkalinity_profile = self.product_profiles.get("alkalinity", {})
                if alkalinity_profile.get("method") == "label_linear":
                    data.dose_alkalinity = label_linear_dose(
                        alkalinity_profile,
                        current=ta,
                        target=self.target_ta,
                        volume_gallons=volume,
                        chemical_type=profile_chemical_type(
                            alkalinity_profile, ChemicalType.BAKING_SODA
                        ),
                    )
                else:
                    data.dose_alkalinity = calculate_alkalinity_dose(
                        current_ta=ta,
                        target_ta=self.target_ta,
                        pool_gallons=volume,
                    )
            except Exception as err:
                _LOGGER.debug("Alkalinity dose calculation failed: %s", err)

        # Calcium dose
        if (
            self._is_dose_enabled(CONF_ENABLE_DOSE_CALCIUM, DEFAULT_ENABLE_DOSE_CALCIUM)
            and ch is not None
        ):
            try:
                profile = self.product_profiles.get("calcium", {})
                if profile.get("method") == "label_linear":
                    data.dose_calcium = label_linear_dose(
                        profile,
                        current=ch,
                        target=self.target_ch,
                        volume_gallons=volume,
                        chemical_type=profile_chemical_type(
                            profile, ChemicalType.CALCIUM_CHLORIDE_DIHYDRATE
                        ),
                    )
                else:
                    data.dose_calcium = calculate_calcium_dose(
                        current_ch=ch,
                        target_ch=self.target_ch,
                        pool_gallons=volume,
                    )
            except Exception as err:
                _LOGGER.debug("Calcium dose calculation failed: %s", err)

        # CYA dose
        if self._is_dose_enabled(CONF_ENABLE_DOSE_CYA, DEFAULT_ENABLE_DOSE_CYA):
            try:
                profile = self.product_profiles.get("cya", {})
                if profile.get("method") == "label_linear":
                    data.dose_cya = label_linear_dose(
                        profile,
                        current=cya,
                        target=self.target_cya,
                        volume_gallons=volume,
                        chemical_type=profile_chemical_type(
                            profile, ChemicalType.CYA_GRANULAR
                        ),
                    )
                else:
                    data.dose_cya = calculate_cya_dose(
                        current_cya=cya,
                        target_cya=self.target_cya,
                        pool_gallons=volume,
                    )
            except Exception as err:
                _LOGGER.debug("CYA dose calculation failed: %s", err)

        # Salt dose (only for saltwater pools)
        if (
            self._is_dose_enabled(CONF_ENABLE_DOSE_SALT, DEFAULT_ENABLE_DOSE_SALT)
            and self.is_saltwater
        ):
            try:
                profile = self.product_profiles.get("salt", {})
                if profile.get("method") == "label_linear":
                    data.dose_salt = label_linear_dose(
                        profile,
                        current=salt,
                        target=self.target_salt,
                        volume_gallons=volume,
                        chemical_type=profile_chemical_type(
                            profile, ChemicalType.POOL_SALT
                        ),
                    )
                else:
                    data.dose_salt = calculate_salt_dose(
                        current_salt=salt,
                        target_salt=self.target_salt,
                        pool_gallons=volume,
                    )
            except Exception as err:
                _LOGGER.debug("Salt dose calculation failed: %s", err)

        # Borates dose
        if self._is_dose_enabled(CONF_ENABLE_DOSE_BORATES, DEFAULT_ENABLE_DOSE_BORATES):
            try:
                profile = self.product_profiles.get("borates", {})
                if profile.get("method") == "label_linear":
                    data.dose_borates = label_linear_dose(
                        profile,
                        current=borates,
                        target=self.target_borates,
                        volume_gallons=volume,
                        chemical_type=profile_chemical_type(
                            profile, ChemicalType.BORAX_BORATE
                        ),
                    )
                else:
                    data.dose_borates = calculate_borate_dose(
                        current_borates=borates,
                        target_borates=self.target_borates,
                        pool_gallons=volume,
                    )
            except Exception as err:
                _LOGGER.debug("Borates dose calculation failed: %s", err)

        # Shock is a separate oxidizer regimen, not a sanitizer residual target.
        shock_profile = self.product_profiles.get("shock", {})
        if (
            self._is_dose_enabled(CONF_ENABLE_DOSE_SHOCK, DEFAULT_ENABLE_DOSE_SHOCK)
            and shock_profile.get("method") == "label_fixed"
        ):
            try:
                data.dose_shock = label_fixed_dose(
                    shock_profile,
                    volume_gallons=volume,
                    chemical_type=profile_chemical_type(
                        shock_profile, ChemicalType.DICHLOR
                    ),
                )
            except Exception as err:
                _LOGGER.debug("Shock label dose calculation failed: %s", err)
