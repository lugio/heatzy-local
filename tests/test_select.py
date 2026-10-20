"""Mapping Onyx APK, distinct du Pilote Pro et du schéma générique."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
import unittest

class TestSelect(unittest.IsolatedAsyncioTestCase):
    def entity(self, code):
        path=Path(__file__).resolve().parents[1]/'custom_components/heatzy_local/select.py'
        tree=ast.parse(path.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));cls.bases=[]
        cls.body=[n for n in cls.body if getattr(n,'name',None)!='__init__']
        modes=next(n for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='MODES' for t in n.targets))
        scope={'EntityCategory':SimpleNamespace(CONFIG='config'),'HomeAssistantError':RuntimeError}
        exec(compile(ast.Module(body=[modes,cls],type_ignores=[]),str(path),'exec'),scope)
        e=scope['DerogationHeatzy']();e.coordinator=SimpleNamespace(data={'derog_mode':code},async_ecrire_verifiee=AsyncMock());return e

    async def test_actual_mapping_and_unknown_modes(self):
        for code,expected in [(0,'off'),(1,'programme'),(2,'vacances'),(3,'auto'),(4,None),(5,None)]:
            self.assertEqual(self.entity(code).current_option,expected)

    async def test_auto_writes_real_code_and_does_not_claim_presence(self):
        e=self.entity(0);await e.async_select_option('auto')
        e.coordinator.async_ecrire_verifiee.assert_awaited_once_with({'derog_mode':3})
        self.assertNotIn('presence',e.extra_state_attributes)
        with self.assertRaises(RuntimeError):await e.async_select_option('unknown')

if __name__=='__main__':unittest.main()
