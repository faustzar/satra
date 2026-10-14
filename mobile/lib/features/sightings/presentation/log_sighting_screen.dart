import 'package:flutter/material.dart';
import '../../../core/constants/colors.dart';

class LogSightingScreen extends StatefulWidget {
  const LogSightingScreen({super.key});

  @override
  State<LogSightingScreen> createState() => _LogSightingScreenState();
}

class _LogSightingScreenState extends State<LogSightingScreen> {
  double? _latitude = -33.9249;
  double? _longitude = 18.4241;
  double _gpsAccuracy = 3.2; // meters
  bool _isLocating = false;
  String _selectedHabitat = "Succulent Karoo";
  bool _matchFound = true;
  String _matchedId = "LEOP-2026-001 (94.2% match)";

  final List<String> _habitats = [
    "Succulent Karoo",
    "Fynbos",
    "Renosterveld",
    "Thicket / Bushveld",
    "Agricultural Border",
    "Roadside Verge",
    "Urban Garden"
  ];

  void _refreshGPS() {
    setState(() => _isLocating = true);
    Future.delayed(const Duration(milliseconds: 900), () {
      if (mounted) {
        setState(() {
          _isLocating = false;
          _gpsAccuracy = 2.4;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("GPS Fix refreshed: ±2.4m accuracy")),
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Field Sighting & Recognition"),
        actions: [
          IconButton(
            icon: const Icon(Icons.flash_auto),
            onPressed: () {},
            tooltip: "Flash mode",
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Guided Camera Viewfinder Card with Biometric Reticle
            Container(
              height: 240,
              decoration: BoxDecoration(
                color: Colors.black87,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.primaryGreen, width: 2),
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  const Icon(Icons.camera_alt, color: Colors.white24, size: 64),
                  
                  // Reticle Overlay (Oval Carapace alignment guide)
                  Container(
                    width: 170,
                    height: 190,
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: AppColors.fieldHighContrastYellow,
                        width: 2,
                        style: BorderStyle.solid,
                      ),
                      borderRadius: const BorderRadius.all(Radius.elliptical(170, 190)),
                    ),
                    child: const Center(
                      child: Text(
                        "Align Shell (90° Perpendicular)",
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: AppColors.fieldHighContrastYellow,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          backgroundColor: Colors.black54,
                        ),
                      ),
                    ),
                  ),

                  Positioned(
                    bottom: 12,
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.fieldHighContrastYellow,
                        foregroundColor: Colors.black,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                      ),
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text("Simulating Biometric Scute Analysis...")),
                        );
                      },
                      icon: const Icon(Icons.camera),
                      label: const Text("Snap & Match Shell"),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // AI Biometric Recognition Match Pill
            if (_matchFound)
              Card(
                color: const Color(0xFFE8F5E9),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: const BorderSide(color: AppColors.statusWild, width: 1.5),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Row(
                    children: [
                      const Icon(Icons.verified, color: AppColors.statusWild, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              "Biometric Shell Pattern Match",
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                            Text(
                              _matchedId,
                              style: const TextStyle(
                                color: AppColors.primaryGreen,
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                          ],
                        ),
                      ),
                      TextButton(
                        onPressed: () {},
                        child: const Text("View Profile"),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 16),

            // High Precision GPS Telemetry Card
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.gps_fixed, color: AppColors.primaryGreen),
                            SizedBox(width: 8),
                            Text(
                              "GPS Location (Encrypted)",
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                          ],
                        ),
                        IconButton(
                          icon: _isLocating
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.refresh),
                          onPressed: _refreshGPS,
                          tooltip: "Update coordinates",
                        ),
                      ],
                    ),
                    const Divider(),
                    Text("Latitude: ${_latitude?.toStringAsFixed(6)}"),
                    Text("Longitude: ${_longitude?.toStringAsFixed(6)}"),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          width: 10,
                          height: 10,
                          decoration: const BoxDecoration(
                            color: Colors.green,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          "Accuracy: ±${_gpsAccuracy}m (Anti-Poaching Protected)",
                          style: TextStyle(color: Colors.grey[700], fontSize: 13),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Micro-Habitat Selector
            DropdownButtonFormField<String>(
              value: _selectedHabitat,
              decoration: InputDecoration(
                labelText: "Micro-Habitat Type",
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                prefixIcon: const Icon(Icons.terrain),
              ),
              items: _habitats.map((h) => DropdownMenuItem(value: h, child: Text(h))).toList(),
              onChanged: (val) {
                if (val != null) setState(() => _selectedHabitat = val);
              },
            ),

            const SizedBox(height: 24),

            // Submit Button
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primaryGreen,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text("Sighting saved to local offline database and queued for sync."),
                    backgroundColor: AppColors.primaryGreen,
                  ),
                );
              },
              child: const Text(
                "Save Sighting (Offline Ready)",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
