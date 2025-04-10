# PZEM-016 CLI Tool

Nástroj pro čtení a konfiguraci RS-485 elektroměru **PZEM-016** pomocí Pythonu přes Modbus RTU.

Umožňuje:

- číst všechna měřená data z elektroměru,
- resetovat energii,
- měnit Modbus adresu,
- zjistit aktuální Modbus adresu (včetně použití „general address“),
- zobrazit hodnoty v JSON formátu,
- volit port (`COMx` nebo `/dev/ttyUSBx`) a rychlost (`baudrate`).

## ✅ Požadavky

- Python 3.6+
- Knihovny: `pyserial`

Instalace závislostí:

```bash
pip install pyserial
```

## 🧩 Použití CLI

```bash
python cli.py [volby] <příkaz> [parametry]
```

### ⚙️ Volby

| Přepínač | Význam |
|---------|--------|
| `-p`, `--port` | Port (např. `COM3` nebo `/dev/ttyUSB0`) |
| `-b`, `--baud` | Baudrate (výchozí: 9600) |
| `--debug` | Zapne ladicí výpis |

### 📘 Příkazy

#### `getData [adresa]`

Načte a zobrazí všechna dostupná měřená data v JSON formátu.

#### `getAddr`

Získá aktuální Modbus adresu zařízení přes „general address“ (`0xF8`).

#### `setAddr <nová_adresa>`

Nastaví novou Modbus adresu zařízení.

### 🧪 Příklady

```bash
# Načtení dat ze zařízení na COM3
python cli.py -p COM3 getData

# Načtení dat z adresy 4
python cli.py -p COM3 getData 4

# Změna adresy zařízení z výchozí (0xF8) na 4
python cli.py -p COM3 setAddr 4

# Zjištění aktuální adresy zařízení (musí být pouze jedno zařízení na sběrnici)
python cli.py -p COM3 getAddr
```

## 🛠️ Licencování

Tento projekt je dostupný pod licencí **MIT**.

### MIT License (zkráceně)

- ✅ Můžeš používat, kopírovat, upravovat a šířit.
- ✅ Můžeš integrovat do komerčních projektů.
- ❗ Musíš zachovat původní licenci a copyright.

## 🧑‍💻 Autor

**Jan Zedník**  
[@dvestezar](mailto:dvestezar@gmail.com)

## 📌 Poznámky

- Měřiče musí být správně připojené přes RS-485 (a galvanicky oddělené, pokud je to potřeba).
- Pro komunikaci je potřeba koncový odpor (120Ω) na sběrnici.
- Pokud používáš USB-RS485 převodník, ujisti se, že používá správné řízení RE/DE (např. přes auto-flow).
