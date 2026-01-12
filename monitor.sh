#!/bin/bash
clear
echo "================================================"
echo "🔍 Vetaris - CANLI LOG İZLEME ARACI"
echo "================================================"
echo "Sadece logları izliyorsunuz. Çıkmak için CTRL+C yapın."
echo "Bekleniyor..."
echo ""

# Son 50 satırı göster ve canlı takip et
sudo journalctl -u vetaris.service -f -n 50
