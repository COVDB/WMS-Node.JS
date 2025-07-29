#!/usr/bin/env python3
"""
Test Live Monitoring of Operating Mode Changes
Simulates the changes you would see when switching modes on the PLC HMI
"""

import time
import struct
from datetime import datetime

def simulate_hmi_operating_mode_changes():
    """
    Simulate what happens when you change operating mode on the PLC HMI
    """
    print("🎯 SIMULATING PLC HMI OPERATING MODE CHANGES")
    print("=" * 50)
    print("This simulates what happens when you switch modes on the PLC HMI")
    print("The Streamlit app should detect these changes automatically!\n")
    
    # Base response from your Node-RED success
    base_response = [0,0,2,5,2,2,0,0,223,27,0,0,0,0,0,0,0,14,0,0]
    
    # Different operating modes from real PLC systems
    operating_modes = [
        {"name": "Manual Mode", "code": 514, "description": "Operator control via HMI"},
        {"name": "Automatic Mode", "code": 1026, "description": "Fully automated operation"},
        {"name": "Maintenance Mode", "code": 258, "description": "Service and repair mode"},
        {"name": "Setup Mode", "code": 770, "description": "Configuration mode"},
        {"name": "Emergency Mode", "code": 1538, "description": "Safety shutdown mode"}
    ]
    
    print("🔄 Starting monitoring simulation...")
    print("   (Each mode change represents what you'd see on the PLC HMI)\n")
    
    for i, mode in enumerate(operating_modes):
        # Create modified response
        response = base_response.copy()
        response[4] = mode["code"] & 0xFF      # Low byte
        response[5] = (mode["code"] >> 8) & 0xFF  # High byte
        
        # Also modify system status to show activity
        response[2] = (1282 + i) & 0xFF
        response[3] = ((1282 + i) >> 8) & 0xFF
        
        # Convert to bytes and parse
        response_bytes = bytes(response)
        words = struct.unpack('<10H', response_bytes)
        
        print(f"🔧 HMI Mode Change #{i+1}: {mode['name']}")
        print(f"   📊 Operation Mode Word: {words[2]} ({mode['code']})")
        print(f"   📋 Description: {mode['description']}")
        print(f"   📡 Raw Response: {response}")
        print(f"   🔗 Hex Format: {response_bytes.hex().upper()}")
        print(f"   ⏰ Timestamp: {datetime.now().strftime('%H:%M:%S')}")
        
        # Show what the Streamlit app should detect
        if i > 0:
            prev_mode = operating_modes[i-1]
            print(f"   🎯 **CHANGE DETECTED:** {prev_mode['name']} → {mode['name']}")
            
        print(f"   ⏱️  Simulating mode active for 10 seconds...")
        print("-" * 60)
        
        if i < len(operating_modes) - 1:
            time.sleep(10)  # Wait 10 seconds before next mode change
    
    print("\n✅ **SIMULATION COMPLETE**")
    print("🎉 **This demonstrates exactly what happens when you:**")
    print("   1. Change operating mode on the PLC HMI")
    print("   2. The operation_mode word changes in the TCP response")
    print("   3. The Streamlit app should detect and display the change!")
    print("\n🔄 **With auto-refresh enabled, you'll see:**")
    print("   • Live mode changes as they happen")
    print("   • Change notifications in the interface")
    print("   • Updated status displays")
    print("   • History tracking of all changes")
    
    print("\n📋 **To test with real PLC:**")
    print("   1. Enable 'Real-time HMI monitoring' in Streamlit")
    print("   2. Set refresh interval to 1-3 seconds")
    print("   3. Change operating mode on PLC HMI")
    print("   4. Watch the Streamlit app update automatically!")

if __name__ == "__main__":
    simulate_hmi_operating_mode_changes()
