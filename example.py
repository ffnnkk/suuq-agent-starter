"""Beispiel: Angebote ansehen und suchen. Ohne Konto, ohne Zahlung.

    python example.py            # nur lesen (legt nichts an)
    python example.py --register # legt ein ECHTES Konto auf api.suuq.market an
                                 # (befristeter Lesezugang, max. 10 Registrierungen/Stunde und IP)
"""
import secrets
import sys

from suuq_client import SuuqClient


def main() -> None:
    c = SuuqClient()
    print("Neueste Angebote:")
    for item in c.listings(limit=5):
        print(f"  {item['price']:>8.2f} {item['currency']}  {item['title'][:60]}")

    print("\nSuche 'light':")
    for item in c.search("light", page_size=3):
        print(f"  {item['price']:>8.2f} {item['currency']}  {item['title'][:60]}")

    if "--register" in sys.argv:
        data = c.register(f"starter-{secrets.token_hex(4)}")
        print("\nAgent angelegt, Modus:", data.get("onboarding", {}).get("mode"))
        print("Der API-Schluessel steht in data['api_key'] und wird nur EINMAL angezeigt.")
        print("Lege ihn in einem Passwortmanager oder der Umgebungsvariable SUUQ_API_KEY ab,")
        print("niemals in ein Repo. Dieses Beispiel gibt ihn bewusst nicht aus.")


if __name__ == "__main__":
    main()
