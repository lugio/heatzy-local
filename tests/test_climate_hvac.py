"""Regression tests for HVAC command semantics, without a Home Assistant install.

The actual methods are loaded from the production AST. Network writes are
mocked; runtime integration is separately verified in Home Assistant.
"""
import ast
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock


class HVACMode(str, Enum):
    HEAT = "heat"
    OFF = "off"


def thermostat(data):
    source = Path(__file__).resolve().parents[1] / "custom_components/heatzy_local/climate.py"
    tree = ast.parse(source.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ThermostatHeatzy")
    wanted = {"_mode", "hvac_mode", "async_set_hvac_mode", "async_turn_on", "async_turn_off"}
    cls.body = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in wanted]
    cls.bases = []
    scope = {"HVACMode": HVACMode, "MODE_ARRET": "stop",
             "MODE_VERS_PRESET": {"cft": "comfort", "eco": "eco", "fro": "away"},
             "HomeAssistantError": RuntimeError}
    exec(compile(ast.Module(body=[cls], type_ignores=[]), str(source), "exec"), scope)
    entity = scope["ThermostatHeatzy"]()
    entity.coordinator = SimpleNamespace(data=data)
    entity._appliquer = AsyncMock()
    return entity


class TestHVAC(unittest.IsolatedAsyncioTestCase):
    async def test_heat_preserves_each_running_preset_without_write(self):
        for mode in ("cft", "eco", "fro"):
            with self.subTest(mode=mode):
                entity = thermostat({"on_off": True, "mode": mode})
                await entity.async_set_hvac_mode(HVACMode.HEAT)
                entity._appliquer.assert_not_awaited()

    async def test_heat_from_stop_uses_comfort(self):
        entity = thermostat({"on_off": True, "mode": "stop"})
        await entity.async_set_hvac_mode(HVACMode.HEAT)
        entity._appliquer.assert_awaited_once_with("cft")

    async def test_heat_when_powered_off_preserves_known_preset(self):
        entity = thermostat({"on_off": False, "mode": "eco"})
        await entity.async_set_hvac_mode(HVACMode.HEAT)
        entity._appliquer.assert_awaited_once_with("eco")

    async def test_turn_on_preserves_comfort(self):
        entity = thermostat({"on_off": True, "mode": "cft"})
        await entity.async_turn_on()
        entity._appliquer.assert_not_awaited()

    async def test_off_still_sends_stop(self):
        entity = thermostat({"on_off": True, "mode": "cft"})
        await entity.async_set_hvac_mode(HVACMode.OFF)
        entity._appliquer.assert_awaited_once_with("stop")


    async def test_power_flag_false_reports_off_even_with_saved_preset(self):
        entity = thermostat({"on_off": False, "mode": "cft"})
        self.assertEqual(entity.hvac_mode, HVACMode.OFF)

if __name__ == "__main__":
    unittest.main()
