"""Régressions réseau hors ligne : aucun radiateur n'est contacté."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]/'custom_components/heatzy_local'
PKG='heatzy_transport_tests'
package=types.ModuleType(PKG);package.__path__=[str(ROOT)];sys.modules[PKG]=package
for name in ('const','gizwits'):
 spec=importlib.util.spec_from_file_location(PKG+'.'+name,ROOT/(name+'.py'))
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
g=sys.modules[PKG+'.gizwits']

class Writer:
 def __init__(self,reader,fragmented=False,notification=False,silent=False):
  self.reader=reader;self.fragmented=fragmented;self.notification=notification;self.silent=silent;self.closed=False
 def write(self,data):
  cmd,payload=next(g._depiler(data))
  if self.silent:return
  if cmd==g.CMD_PASSCODE:
   response=g._trame(7,b'\x00\x04test')
   if self.fragmented:
    self.reader.feed_data(response[:4]);asyncio.get_running_loop().call_later(.001,self.reader.feed_data,response[4:]);return
  elif cmd==g.CMD_LOGIN:
   response=g._trame(9,b'\x00' if payload==b'\x00\x04test' else b'\x01')
   if self.notification:response+=g._trame(0x93,b'notification\xff')
  else:return
  self.reader.feed_data(response)
 async def drain(self):pass
 def close(self):self.closed=True
 async def wait_closed(self):pass

class TransportTests(unittest.IsolatedAsyncioTestCase):
 async def session(self,**opts):
  reader=asyncio.StreamReader();writer=Writer(reader,**opts)
  async def connect(*args):return reader,writer
  device=g.Appareil('test.invalid',{})
  with patch.object(g.asyncio,'open_connection',connect),patch.object(g,'DELAI_RESEAU',.03):
   result=await device._session()
  return result,writer
 async def test_fragmented_passcode_is_read_as_complete_frame(self):
  (_,writer),_=await self.session(fragmented=True);writer.close()
 async def test_notification_after_login_does_not_corrupt_login_result(self):
  (_,writer),_=await self.session(notification=True);writer.close()
 async def test_timeout_during_handshake_closes_socket_and_normalizes_error(self):
  reader=asyncio.StreamReader();writer=Writer(reader,silent=True)
  async def connect(*args):return reader,writer
  device=g.Appareil('test.invalid',{})
  with patch.object(g.asyncio,'open_connection',connect),patch.object(g,'DELAI_RESEAU',.01):
   try:
    with self.assertRaises(g.ErreurHeatzy):await device._session()
   finally:self.assertTrue(writer.closed,'socket laissée ouverte après échec authentification')
 async def test_refused_login_cannot_be_hidden_by_notification_ending_zero(self):
  reader=asyncio.StreamReader();writer=Writer(reader)
  original=writer.write
  def write(data):
   cmd,_=next(g._depiler(data))
   if cmd==g.CMD_LOGIN:reader.feed_data(g._trame(9,b'\x01')+g._trame(0x93,b'notification\x00'))
   else:original(data)
  writer.write=write
  async def connect(*args):return reader,writer
  with patch.object(g.asyncio,'open_connection',connect):
   with self.assertRaises(g.ErreurHeatzy):await g.Appareil('test.invalid',{})._session()
  self.assertTrue(writer.closed)
 async def test_cancellation_during_handshake_closes_socket(self):
  reader=asyncio.StreamReader();writer=Writer(reader,silent=True);entered=asyncio.Event()
  async def connect(*args):entered.set();return reader,writer
  with patch.object(g.asyncio,'open_connection',connect):
   task=asyncio.create_task(g.Appareil('test.invalid',{})._session())
   await entered.wait();await asyncio.sleep(0);task.cancel()
   with self.assertRaises(asyncio.CancelledError):await task
  self.assertTrue(writer.closed)
 async def test_read_reset_is_normalized_and_closed(self):
  reader=asyncio.StreamReader();writer=Writer(reader);original=writer.write
  def write(data):
   cmd,_=next(g._depiler(data))
   if cmd==g.CMD_LECTURE:reader.set_exception(ConnectionResetError('peer reset'))
   else:original(data)
  writer.write=write
  async def connect(*args):return reader,writer
  with patch.object(g.asyncio,'open_connection',connect):
   with self.assertRaises(g.ErreurHeatzy):await g.Appareil('test.invalid',{}).lire()
  self.assertTrue(writer.closed)
 async def test_connection_refused_is_normalized(self):
  async def connect(*args):raise ConnectionRefusedError('offline')
  with patch.object(g.asyncio,'open_connection',connect):
   with self.assertRaises(g.ErreurHeatzy):await g.Appareil('test.invalid',{})._session()

if __name__=='__main__':unittest.main()
