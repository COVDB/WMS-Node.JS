// WMS Mobile Racking Client - Generated with Streamlit App
// Language: Node.js
// Target: 1.1.1.2:2001
// Generated: 2025-07-29

const net = require('net');

class WMSClient {
    constructor(host, port) {
        this.host = host;
        this.port = port;
        this.client = new net.Socket();
        this.connected = false;
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        this.client.on('connect', () => {
            console.log(`Connected to WMS at ${this.host}:${this.port}`);
            this.connected = true;
        });
        
        this.client.on('error', (err) => {
            console.error('Connection error:', err.message);
            this.connected = false;
        });
        
        this.client.on('close', () => {
            console.log('Connection closed');
            this.connected = false;
        });
        
        this.client.on('data', (data) => {
            this.handleResponse(data);
        });
    }
    
    connect() {
        return new Promise((resolve, reject) => {
            this.client.connect(this.port, this.host, () => {
                resolve(true);
            });
            
            this.client.on('error', (err) => {
                reject(err);
            });
        });
    }
    
    sendCommand(command) {
        if (!this.connected) {
            throw new Error('Not connected');
        }
        
        const buffer = Buffer.allocUnsafe(2);
        buffer.writeUInt16LE(command, 0);
        
        return new Promise((resolve, reject) => {
            this.client.write(buffer, (err) => {
                if (err) {
                    reject(err);
                } else {
                    console.log(`Command ${command} sent`);
                    resolve(true);
                }
            });
        });
    }
    
    handleResponse(data) {
        console.log('Response received:', data.length, 'bytes');
        
        if (data.length === 20) {
            const status = this.parseStatus(data);
            console.log('Status:', JSON.stringify(status, null, 2));
            return status;
        }
    }
    
    parseStatus(data) {
        return {
            tcp_ip_connection: data.readUInt16LE(0) === 1,
            power_on: data.readUInt16LE(2) === 1,
            automatic_mode_on: data.readUInt16LE(4) === 1,
            manual_mode_on: data.readUInt16LE(6) === 1,
            emergency_stop: data.readUInt16LE(8) === 1,
            mobile_quantity: data.readUInt16LE(10),
            position_1: data.readUInt16LE(12) / 100.0,
            position_2: data.readUInt16LE(14) / 100.0,
            lighting_on: data.readUInt16LE(16) === 1,
            timestamp: new Date()
        };
    }
    
    disconnect() {
        if (this.connected) {
            this.client.end();
        }
    }
}

// Usage example
async function main() {
    const wms = new WMSClient('1.1.1.2', 2001);
    
    try {
        await wms.connect();
        
        // Send status request
        await wms.sendCommand(0);
        
        // Send other commands
        // await wms.sendCommand(1); // Start operation
        // await wms.sendCommand(3); // Set automatic mode
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Run the example
main();
