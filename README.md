# WMS Mobile Racking TCP-IP Communication

Een Python Streamlit applicatie voor TCP-IP communicatie met Mobile Racking systemen. Deze applicatie biedt een gebruiksvriendelijke interface voor het communiceren met WMS (Warehouse Management System) via TCP-IP protocol.

## Functionaliteiten

- 🔌 TCP-IP communicatie op poort 2000
- 📊 Real-time status monitoring van Mobile Racking systeem
- 🎛️ Interactieve Streamlit interface
- 📈 Data visualisatie van systeem parameters
- 🔄 Command verzending naar Mobile Racking controller
- 📋 Status logging en historie

## TCP-IP Protocol Details

- **IP Adres**: 1.1.1.2 (standaard, configureerbaar)
- **Poort**: 2000 (standaard) - **⚠️ Zie troubleshooting sectie**
- **Request grootte**: 2 bytes
- **Response grootte**: 20 bytes
- **Data structuur**: Volgens WMS-Data specificatie

## Troubleshooting

### Veelvoorkomende verbindingsproblemen:

#### ❌ "Connection refused" op poort 2000
**Oorzaak:** Mobile Racking TCP-IP service draait niet op de PLC  
**Oplossing:**
1. Neem contact op met PLC technicus
2. Controleer of Mobile Racking software actief is
3. Activeer TCP-IP communicatie module
4. Verificeer poort configuratie

#### ✅ Alternatieve poorten gevonden
Als scan poorten 102, 2001, of 4840 toont:
- **Poort 102**: Siemens S7 PLC communicatie
- **Poort 2001**: Mogelijk alternatieve service
- **Poort 4840**: OPC UA server

#### 🔍 Diagnose tools beschikbaar:
```bash
# Volledige diagnose
python diagnose_plc.py

# Port scanning  
python port_scanner.py

# Basis connectiviteit test
python test_connection.py
```

## Installatie

### Vereisten
- Python 3.8 of hoger
- Streamlit
- Pandas

### Setup

1. Clone de repository:
```bash
git clone https://github.com/COVDB/WMS-Node.JS.git
cd WMS-Node.JS
```

2. Installeer vereiste packages:
```bash
pip install -r requirements.txt
```

3. Start de applicatie:
```bash
streamlit run app.py
```

## Gebruik

1. **Configuratie**: Stel IP adres en poort in via de sidebar
2. **Verbinden**: Klik op "Connect" om verbinding te maken
3. **Commands**: Gebruik de interface om commands te verzenden
4. **Monitoring**: Bekijk real-time status updates

## Project Structuur

```
WMS-Node.JS/
├── app.py                 # Hoofdapplicatie
├── tcp_client.py          # TCP-IP communicatie module
├── wms_protocol.py        # WMS protocol definitie
├── utils/
│   ├── __init__.py
│   ├── data_parser.py     # Data parsing utilities
│   └── logger.py          # Logging utilities
├── requirements.txt       # Python dependencies
├── README.md             # Dit bestand
└── LICENSE               # MIT License
```

## WMS Data Structuur

Het systeem gebruikt een gedefinieerde data structuur voor communicatie:

- **Command Request**: 2-byte commands
- **Status Response**: 20-byte status informatie
- **Data Types**: Bool, Byte, DWord volgens specificatie

## Ontwikkeling

### Lokale ontwikkeling

```bash
# Start development server
streamlit run app.py

# Run met debug mode
streamlit run app.py --logger.level=debug
```

### Testing

```bash
# Run tests (wanneer beschikbaar)
python -m pytest tests/
```

## Licentie

Dit project valt onder de MIT License - zie het [LICENSE](LICENSE) bestand voor details.

## Bijdragen

1. Fork het project
2. Maak een feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit je wijzigingen (`git commit -m 'Add some AmazingFeature'`)
4. Push naar de branch (`git push origin feature/AmazingFeature`)
5. Open een Pull Request

## Support

Voor vragen en support, maak een issue aan op GitHub of neem contact op via [support@covdb.com](mailto:support@covdb.com).

## Changelog

### [1.0.0] - 2025-07-29
- Initiële release
- TCP-IP communicatie implementatie
- Streamlit interface
- WMS protocol support
