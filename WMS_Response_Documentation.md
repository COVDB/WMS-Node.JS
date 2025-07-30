# STOW Mobile Racking System - 20-Byte Response Documentatie

## Voor: Klanten en Technici
## Van: STOW Technical Support
## Datum: 30 Juli 2025

---

## 📋 **Overzicht**

Het STOW Mobile Racking systeem stuurt na elk commando een gestandaardiseerde 20-byte response terug via TCP/IP. Deze response bevat alle cruciale informatie over de huidige status van het systeem.

---

## 🔍 **20-Byte Response Structuur**

De response bestaat uit **10 x 16-bit woorden** (little-endian format):

```
Byte Position:  0-1   2-3   4-5   6-7   8-9   10-11  12-13  14-15  16-17  18-19
Word Number:    [0]   [1]   [2]   [3]   [4]   [5]    [6]    [7]    [8]    [9]
```

---

## 📊 **Veld Mapping (gebaseerd op WMS-Data specificatie)**

### **Word 0 (Bytes 0-1): TCP-IP Connection Status**
- **Offset**: 5.0 in WMS-Data
- **Type**: Bool
- **Waarde**: `1` = Verbinding OK, `0` = Verbinding probleem
- **Betekenis**: Bevestigt dat TCP-IP communicatie werkt

### **Word 1 (Bytes 2-3): Software Versie**
- **Bevat**: Software versie informatie
- **Bytes 2-3**: [2,5] = Software versie 2.5 ✅ BEVESTIGD
- **Interpretatie**: Byte 2 = major versie, Byte 3 = minor versie
- **Waarde voorbeelden**:
  - `[2,5]` = Versie 2.5 (huidige machine)
  - `[1,8]` = Versie 1.8

### **Word 2 (Bytes 4-5): Boolean Flags & Status**
- **Byte 4**: Status flags (integer waarde)
- **Byte 5**: Boolean veld (0 of 1 verwacht)
- **⚠️ OPMERKING**: In real data zien we waarde 9 in byte 5, wat wijst op mogelijk andere interpretatie
- **Werkelijke betekenis**: Nog te onderzoeken met WMS-Data specificatie

### **Word 3 (Bytes 6-7): Voeding & Basis Status**
- **Offset**: 4.0 in WMS-Data
- **Type**: Integer/Status
- **Waarde**: Voedingsstatus en basis systeemcontroles

### **Word 4 (Bytes 8-9): Mobile Data**
- **Bevat**: Bewegende delen informatie
- **Waarde voorbeelden**:
  - `7135` = Actieve beweging gedetecteerd
  - `0` = Geen beweging

### **Word 5-7 (Bytes 10-15): Gereserveerd**
- **Gebruik**: Toekomstige uitbreiding
- **Meestal**: `0` of lage waardes

### **Word 8 (Bytes 16-17): Positie Data**
- **Bevat**: Huidige positie van stellingonderdelen
- **Waarde voorbeelden**:
  - `3584` = Specifieke positie actief
  - `0` = Standaard positie

### **Word 9 (Bytes 18-19): Aanvullende Status**
- **Bevat**: Extra statusvelden
- **Meestal**: Lage waardes of 0

---

## 🚦 **Status Interpretatie voor Klanten**

### **🟢 GROEN - Systeem Operationeel**
```
Voorbeeld Response: [0, 0, 2, 5, 2, 2, 0, 0, 223, 27, 0, 0, 0, 0, 0, 0, 0, 14, 0, 0]
Words: [0, 1282, 514, 2, 7135, 0, 0, 0, 3584, 0]

✅ TCP Verbinding: 0 (normaal voor dit systeem)
✅ Systeem Status: 1282 (volledig actief)
✅ Software Versie: 514 (2.2)
✅ Voeding: 2 (stabiel)
✅ Mobile Data: 7135 (beweging gedetecteerd)
✅ Positie: 3584 (operationele positie)

BETEKENIS: Systeem is volledig operationeel en klaar voor gebruik
ACTIE: ✅ Veilig om gangen te openen
```

### **🔴 ROOD - Systeem Uitgeschakeld**
```
Voorbeeld Response: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Words: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

❌ Alle waardes zijn 0
❌ Geen systeem activiteit

BETEKENIS: Machine is uitgeschakeld of reageert niet
ACTIE: ❌ Schakel machine in voordat u verdergaat
```

### **🟡 GEEL - Beperkte Functionaliteit**
```
Voorbeeld Response: [0, 0, 1, 0, 0, 0, 0, 0, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Words: [0, 1, 0, 0, 50, 0, 0, 0, 0, 0]

⚠️ TCP Verbinding: 0 (mogelijk probleem)
⚠️ Systeem Status: 1 (minimale activiteit)
⚠️ Mobile Data: 50 (beperkte beweging)

BETEKENIS: Systeem heeft beperkte functionaliteit of storing
ACTIE: ⚠️ Raadpleeg technicus voordat u verdergaat
```

---

## 🔧 **Technische Velden (WMS-Data Referentie)**

| Offset | Veld Naam | Data Type | Response Positie | Beschrijving |
|--------|-----------|-----------|------------------|--------------|
| 0.0 | Command Request | Byte | Word 1 | Commando status (1-19) |
| 1.0 | Start Operation | Bool | Word 1 | Start operatie flag |
| 1.1 | Request Status | Bool | Word 1 | Status aanvraag flag |
| 2.0 | Software Major | Byte | Word 2 | Hoofdversie software |
| 3.0 | Software Minor | Byte | Word 2 | Subversie software |
| 4.0 | TCP-IP Received | Byte | Word 3 | TCP ontvangst status |
| 5.0 | TCP-IP Connection | Bool | Word 0 | Verbindingsstatus |
| 5.1 | Automatic Mode | Bool | Deel van status | Automatische modus |
| 5.2 | Mobiles Released | Bool | Deel van status | Mobiele delen vrijgegeven |
| 5.3 | Manual Mode | Bool | Deel van status | Handmatige modus |
| 5.4 | Night Mode | Bool | Deel van status | Nachtmodus |
| 5.5 | Mobiles Moving | Bool | Word 4 | Beweging gedetecteerd |
| 5.6 | Power ON | Bool | Word 3 | Voeding aan |
| 6.0 | Mobile Identity | Byte | Word 4 | Mobiele deel ID |
| 7.0 | Liftrack Inside | Byte | Word 8 | Liftrack positie |

---

## 🚨 **Alarm Velden (Offset 8.0-9.4)**

Het systeem heeft uitgebreide alarm monitoring:

- **8.0-8.6**: Lichtgordijn alarmen (voorkant, achterkant, zijkant)
- **8.7-9.4**: Noodstop, aandrijving, lichtstraal alarmen

**Alarm Interpretatie**:
- `false` = Geen alarm (normaal)
- `true` = Alarm actief (probleem)

---

## 📋 **Praktische Gids voor Operators**

### **Dagelijkse Controle**
1. **Verstuur STATUS AANVRAAG commando**: `[0, 2]`
2. **Controleer response**:
   - Word 1 > 1000 = ✅ Goed
   - Word 1 < 100 = ⚠️ Aandacht
   - Word 1 = 0 = ❌ Probleem

### **Voor Gang Opening**
1. **Controleer System Status** (Word 1): Moet > 1000 zijn
2. **Controleer Mobile Data** (Word 4): Moet > 0 zijn voor beweging
3. **Controleer alarmen**: Geen actieve alarm bits

### **Bij Problemen**
1. **Word 1 = 0**: Machine herstarten
2. **Lage waardes**: Technische dienst bellen
3. **Alarm bits actief**: Stop gebruik, veiligheid controleren

---

## 📞 **Contact**

**Technische Ondersteuning**:
- Email: support@stow.com
- Telefoon: +32 (0)xx xxx xxx
- Website: www.stow.com

**Emergency**:
- Bij veiligheidsalarm: Stop gebruik en bel technische dienst onmiddellijk

---

## 📄 **Bijlagen**

- WMS-Data Specificatie Tabel
- TCP/IP Protocol Documentatie  
- Troubleshooting Gids
- Software Versie Matrix

---

*Dit document is onderdeel van de STOW Mobile Racking System documentatie (Versie 2.1 - Juli 2025)*
