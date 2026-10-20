import importlib.util
import asyncio
from pathlib import Path
import unittest
from unittest.mock import AsyncMock

P=Path(__file__).resolve().parents[1]/'custom_components/heatzy_local/transactions.py'

class TestTransactions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        s=importlib.util.spec_from_file_location('transactions_test',P)
        self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m)

    async def test_backup_then_write_then_delay_then_readback(self):
        events=[];data={'on_off':True,'mode':'cft','x':1}
        class Device:
            async def lire(self):events.append('read');return dict(data)
            async def ecrire(self,values,sequence=1):events.append(('write',values));data.update(values)
        async def backup(before,values):events.append('backup')
        async def sleep(seconds):events.append(('sleep',seconds))
        t=self.m.Transaction(Device(),backup,sleep)
        result=await t.ecrire({'mode':'eco'})
        self.assertEqual(events,['read','backup',('write',{'mode':'eco','on_off':True}),('sleep',12),'read'])
        self.assertEqual(result['mode'],'eco')

    async def test_ignored_ack_is_failure(self):
        device=type('Device',(),{})();device.lire=AsyncMock(return_value={'x':1});device.ecrire=AsyncMock()
        t=self.m.Transaction(device,AsyncMock(),AsyncMock())
        with self.assertRaisesRegex(ValueError,'non confirmée'):await t.ecrire({'x':2})

    async def test_backup_failure_prevents_write(self):
        device=type('Device',(),{})();device.lire=AsyncMock(return_value={'x':1});device.ecrire=AsyncMock()
        t=self.m.Transaction(device,AsyncMock(side_effect=OSError('disk full')),AsyncMock())
        with self.assertRaises(OSError):await t.ecrire({'x':2})
        device.ecrire.assert_not_awaited()

    async def test_cancelled_caller_does_not_release_device_during_cooldown(self):
        entered = asyncio.Event()
        release = asyncio.Event()
        data = {"x": 1}
        device = type("Device", (), {})()
        device.lire = AsyncMock(side_effect=lambda: dict(data))
        async def write(values, sequence=1): data.update(values)
        device.ecrire = AsyncMock(side_effect=write)
        async def sleep(_):
            entered.set()
            await release.wait()
        t = self.m.Transaction(device, AsyncMock(), sleep)
        caller = asyncio.create_task(t.ecrire({"x": 2}))
        await entered.wait()
        caller.cancel()
        poll = asyncio.create_task(t.lire())
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertFalse(poll.done())
        release.set()
        with self.assertRaises(asyncio.CancelledError): await caller
        self.assertEqual(await poll, {"x": 2})
        self.assertEqual(device.lire.await_count, 3)

    async def test_transport_error_after_send_still_waits_and_reads(self):
        data = {"x": 1}
        device = type("Device", (), {})()
        device.lire = AsyncMock(side_effect=lambda: dict(data))
        async def write(values, sequence=1):
            data.update(values)
            raise OSError("reply lost")
        device.ecrire = AsyncMock(side_effect=write)
        sleep = AsyncMock()
        t = self.m.Transaction(device, AsyncMock(), sleep)
        self.assertEqual(await t.ecrire({"x": 2}), {"x": 2})
        sleep.assert_awaited_once_with(12)
        self.assertEqual(device.lire.await_count, 2)

if __name__=='__main__':unittest.main()
