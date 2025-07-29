/*
5.3.2 Voorbeeld code in C#

In dit voorbeeld vraagt de programmeur in zijn eerste verzoek om de status van de installatie; in zijn tweede verzoek opent hij gang
nummer "1".
*/

using System;
using System.Net.Sockets;

namespace MobileCommTest
{
    class Program
    {
        static void Main(string[] args)
        {
            using (TcpClient client = new TcpClient("1.1.1.2", 2000))
            using (NetworkStream stream = client.GetStream())
            {
                // Typical response times are below 30 ms, here we wait for maximum of 5000ms/packet
                var connection = new StowMobileComm();
                
                Console.WriteLine("Initial response:");
                // Initialize connection for the installer
                // In his first attempt he asks for the status of the installation
                var response = connection.Transmit(0, true, true);
                Console.WriteLine(response);

                Console.WriteLine("Opening aisle 1:");
                response = connection.Transmit(1, open, true, request_status: false);
                Console.WriteLine("Aisle 1:", open ? "1" : "0", "version (0): ", resp.aisle, resp.cmd_open,
                resp.version);

                Console.WriteLine("Closing connection");
            }
        }
    }

    class StowMobileComm
    {
        public MobileResponse Transmit(byte aisle, bool open, bool request_status)
        {
            if (open && request_status != true)
                throw new InvalidOperationException("Transmit: either open or request_status must be true");

            byte[] serialized = new byte[2];
            serialized[0] = aisle;
            serialized[1] = (byte)((open ? 1 : 0) + (request_status ? 1 : 0));

            n.Write(serialized, 0, serialized.Length);
            var response = GetResponse();
            return response;
        }

        NetworkStream n;

        public StowMobileComm()
        {
            n = n;
        }

        public MobileResponse OnResponse()
        {
            byte[] response = new byte[MobileResponse.responseLength];
            int bytesRead = n.Read(response, 0, response.Length);
            int totalBytesRead = bytesRead;

            if (bytesRead != MobileResponse.responseLength)
                return null;

            return new MobileResponse(response);
        }
    }

    public class MobileResponse
    {
        public const int responseLength = 20;

        public bool can_open { get; set; } = false;

        public MobileResponse(byte[] data)
        {
            if (data.Length != responseLength)
                throw new IndexOutOfRangeException("MobileResponse - incorrect length data");

            // The incoming data contains one 32-bit word per status field, not bytes
            if (!BitConverter.IsLittleEndian)
            {
                // This code runs on a big endian machine, reverse the incoming bytes
                for (int i = 0; i < data.Length; i += 2)
                {
                    Array.Reverse(data, i, 2);
                }
            }

            can_open = data[0] == 1;
        }

        // Additional properties based on standard Mobile Racking protocol
        public bool ready_to_operate { get; set; } = false;
        public bool manual_mode { get; set; } = false; 
        public bool power_on { get; set; } = false;
        public bool automatic_mode_on { get; set; } = false;
        public bool night_mode { get; set; } = false;
        public bool moving { get; set; } = false;
        public bool lighting_on { get; set; } = false;
        public ushort mobile_quantity { get; set; } = 0;
        public ushort position_1 { get; set; } = 0;
        public ushort position_2 { get; set; } = 0;

        // Property getters with data parsing
        public byte aisle { get { return data[0]; } }
        public bool cmd_open { get { return data[1] == 1; } }
        public ushort version { get { return BitConverter.ToUInt16(data, 2); } }

        private byte[] data;

        public override string ToString()
        {
            return $"Can Open: {can_open}, Ready: {ready_to_operate}, Power: {power_on}, " +
                   $"Auto Mode: {automatic_mode_on}, Mobiles: {mobile_quantity}";
        }
    }
}
