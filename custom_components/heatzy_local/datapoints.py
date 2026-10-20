"""Conversions sans I/O : schéma produit et programme 2 bits vérifié sur Onyx."""
from decimal import Decimal, InvalidOperation

MODES = ("cft", "eco", "fro", "stop")


def attributs(definition: dict) -> dict:
    return {a["name"]: a for e in definition["entities"] for a in e["attrs"]}


def bornes_consigne(definition: dict, base: str) -> tuple[float, float, float]:
    attrs = attributs(definition)
    lo, hi = (attrs[base + suffix]["uint_spec"] for suffix in ("L", "H"))
    # Les deux champs stockent les octets, ratio 1/addition 0 dans le schéma
    # Onyx. Ne pas appliquer ici une limite physique absente du descripteur.
    if any(s.get("ratio", 1) != 1 or s.get("addition", 0) != 0 for s in (lo, hi)):
        raise ValueError("schéma de consigne non pris en charge")
    return ((hi["min"] * 256 + lo["min"]) / 10,
            (hi["max"] * 256 + lo["max"]) / 10, 0.1)


def valeurs_consigne(definition: dict, base: str, valeur: float) -> dict:
    minimum, maximum, _ = bornes_consigne(definition, base)
    try:
        v = Decimal(str(valeur))
        if not v.is_finite() or not Decimal(str(minimum)) <= v <= Decimal(str(maximum)):
            raise ValueError("consigne hors bornes du schéma")
        brut = v * 10
        if brut != brut.to_integral_value():
            raise ValueError("consigne au dixième de degré requis")
    except InvalidOperation as err:
        raise ValueError("consigne invalide") from err
    entier = int(brut)
    values = {base + "L": entier & 255, base + "H": entier >> 8}
    attrs = attributs(definition)
    for nom, value in values.items():
        spec = attrs[nom]["uint_spec"]
        if not spec["min"] <= value <= spec["max"]:
            raise ValueError("octet hors bornes du schéma")
    return values


def programmes(etat: dict) -> dict:
    """Clés de jours 1..7 brutes ; None pour tout jour incomplet."""
    out = {}
    for jour in range(1, 8):
        valeurs = [etat.get(f"p{jour}_data{k}") for k in range(1, 13)]
        out[str(jour)] = ([MODES[(v >> (2 * b)) & 3]
                          for v in valeurs for b in range(4)]
                         if all(isinstance(v, int) and 0 <= v <= 255 for v in valeurs)
                         else None)
    return out


def valeurs_programme(jour: int, ordres: list[str]) -> dict:
    """jour=0 pour les sept jours ; indices 1..7 du schéma sinon."""
    if type(jour) is not int or not 0 <= jour <= 7:
        raise ValueError("jour attendu : 0 (tous) ou 1..7")
    if not isinstance(ordres, list) or len(ordres) != 48 or any(x not in MODES for x in ordres):
        raise ValueError("48 ordres requis parmi cft, eco, fro, stop")
    octets = [sum(MODES.index(ordres[i + b]) << (2 * b) for b in range(4))
              for i in range(0, 48, 4)]
    return {f"p{j}_data{k+1}": value for j in (range(1, 8) if jour == 0 else [jour])
            for k, value in enumerate(octets)}


def valeurs_horloge(date) -> dict:
    """Convention Onyx prouvée par APK setTimingData : lundi=1, dimanche=7."""
    return {"week": date.isoweekday(), "hour": date.hour, "minute": date.minute}


def horloge_confirmee(etat: dict, demande: dict) -> bool:
    def minute_semaine(d):
        w, h, m = (d.get(k) for k in ("week", "hour", "minute"))
        if not all(type(v) is int for v in (w, h, m)):
            return None
        if not (1 <= w <= 7 and 0 <= h <= 23 and 0 <= m <= 59):
            return None
        return (w - 1) * 1440 + h * 60 + m
    actuel, cible = minute_semaine(etat), minute_semaine(demande)
    return actuel is not None and cible is not None and (actuel - cible) % 10080 in (0, 1)
