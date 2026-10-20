"""Transactions LAN : aucun accusé n'est pris pour une confirmation d'état."""
import asyncio
import time


class EcritureNonConfirmee(ValueError):
    def __init__(self, etat):
        super().__init__("écriture non confirmée par la relecture")
        self.etat = etat


class Transaction:
    def __init__(self, appareil, sauvegarder, attendre=asyncio.sleep):
        self.appareil = appareil
        self.sauvegarder = sauvegarder
        self.attendre = attendre
        self.verrou = asyncio.Lock()

    async def lire(self):
        async with self.verrou:
            return await self.appareil.lire()

    async def ecrire(self, valeurs: dict, verifier=None):
        contexte = {"emission": False}
        task = asyncio.create_task(self._ecrire(valeurs, verifier, contexte))
        annule = False
        while True:
            try:
                etat = await asyncio.shield(task)
                break
            except asyncio.CancelledError:
                if task.cancelled():
                    raise
                if not contexte["emission"]:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    raise
                # Une commande est peut-être déjà sur le fil : conserver le
                # verrou et terminer délai + relecture, même si HA annule
                # l'appelant. Une seconde annulation ne tue pas cette tâche.
                annule = True
        if annule:
            raise asyncio.CancelledError
        return etat

    async def _ecrire(self, valeurs, verifier, contexte):
        async with self.verrou:
            avant = await self.appareil.lire()
            demande = dict(valeurs() if callable(valeurs) else valeurs)
            # Les deux champs partagent l'octet 0. Toujours écrire les deux.
            if "mode" in demande or "on_off" in demande:
                demande.setdefault("on_off", avant.get("on_off"))
                demande.setdefault("mode", avant.get("mode"))
                if demande["on_off"] is None or demande["mode"] is None:
                    raise ValueError("état préalable on_off/mode absent")
            await self.sauvegarder(avant, demande)
            contexte["emission"] = True
            erreur = None
            try:
                await self.appareil.ecrire(demande, sequence=int(time.time()) & 0xFFFF)
            except Exception as err:  # l'envoi peut avoir réussi sans réponse
                erreur = err
            await self.attendre(12)
            apres = await self.appareil.lire()
            ok = verifier(apres, demande) if verifier else all(apres.get(k) == v for k, v in demande.items())
            if not ok:
                raise EcritureNonConfirmee(apres) from erreur
            return apres
