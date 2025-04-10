#!/usr/bin/env python3

import argparse
import json
from lib import pzem016
from lib.pzem016 import registers as reg

def main():
    parser = argparse.ArgumentParser(
        description=
            """
            CLI nástroj pro čtení a konfiguraci PZEM-016 RS-485 měřiče.
            Default UART port je COM3 a baudrate 9600
            Pokud není port a baudrate zadán, použije se výchozí nastavení
            """
    )
    
    parser.add_argument("-p", "--port", type=str, help="Název sériového portu (např. COM3 nebo /dev/ttyUSB0)")
    parser.add_argument("-b", "--baud", type=int, help="Baud rate (např. 9600)")
    parser.add_argument("--debug", action="store_true", help="Zapnout debug výstup")

    subparsers = parser.add_subparsers(dest="command", help="Příkazy")

    subparsers.add_parser("getAddr", help="Získat adresu zařízení přes general address")

    setaddr = subparsers.add_parser("setAddr", help="Nastavit novou adresu zařízení")
    setaddr.add_argument("address", type=int, help="Nová Modbus adresa (1–247)")

    getdata = subparsers.add_parser("getData", help="Získat všechna data jako JSON")
    getdata.add_argument("address", nargs="?", type=int, help="Volitelná adresa zařízení")

    args = parser.parse_args()

    # Debug mód
    if args.debug:
        pzem016.debug = True

    # Přepsání portu a baudrate, pokud jsou předány
    if args.port:
        pzem016.port = args.port
    if args.baud:
        pzem016.baudRate = args.baud

    # Vytvoření instance měřiče
    meter = pzem016.masterData()

    # Vyhodnocení příkazu
    if args.command == "getAddr":
        addr = meter.getModbusAddr(None)
        print(f"Adresa nalezena: {addr}" if addr is not None else "Adresa nebyla zjištěna.")

    elif args.command == "setAddr":
        try:
            ok = meter.setModBusAddr(newAddr=args.address)
            print("Adresa úspěšně nastavena." if ok else "Selhalo nastavení adresy.")
        except ValueError as e:
            print("Chyba:", e)

    elif args.command == "getData":
        adr = args.address if args.address else None
        if meter.requestData(addr=adr):
            print(json.dumps(meter.json(), indent=2))
        else:
            print("Selhalo čtení dat.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
