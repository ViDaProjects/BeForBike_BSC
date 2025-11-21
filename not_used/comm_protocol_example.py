from comm_protocol import GpsData, CrankData, PacketInfo, TelemetryMsg, RideDataMsg

# ============================================================
#  EXAMPLE OF USAGE BETWEEN THREADS
# ============================================================

# Create sample ride message
gps = GpsData("2025-10-22T19:00:00Z", -23.56, -46.63, 730.0, 12.5, 180.0, 9, 1)
crank = CrankData(180.0, 90.0, 200.0, 50.0, 3.4, 12.0, 120.0)
packet = PacketInfo("2025-10-22", "19:00:00")
telemetry = [TelemetryMsg(packet, gps, crank) for _ in range(5)]
ride = RideDataMsg("Ride_2025_10_22.bin", telemetry)

# --- Serialize to BLE packets ---
ble_packets = ride.to_ble_packets(msg_id=1)
print(f"Created {len(ble_packets)} BLE packets")

# --- Simulate BLE transmission/reception ---
received = ble_packets.copy()
decoded_ride = RideDataMsg.from_ble_packets(received)
print(f"Decoded ride file name: {decoded_ride.file_name}")
print(f"Telemetry count: {len(decoded_ride.telemetry_log)}")
