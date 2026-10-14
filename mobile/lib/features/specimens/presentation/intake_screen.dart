import 'package:flutter/material.dart';
import '../../../../core/constants/colors.dart';
import 'widgets/scute_notch_picker.dart';

class IntakeScreen extends StatefulWidget {
  const IntakeScreen({super.key});

  @override
  State<IntakeScreen> createState() => _IntakeScreenState();
}

class _IntakeScreenState extends State<IntakeScreen> {
  final _formKey = GlobalKey<FormState>();

  String _selectedSpecies = "Stigmochelys pardalis";
  String _commonName = "Leopard Tortoise";
  String _customId = "LEOP-2026-004";
  String _notchCode = "";
  final _pitTagController = TextEditingController(text: "982000365829108");
  String _sex = "Undetermined";
  String _status = "Intake";
  bool _isScanningPitTag = false;

  final Map<String, String> _speciesOptions = {
    "Stigmochelys pardalis": "Leopard Tortoise",
    "Chersina angulata": "Angulate Tortoise",
    "Psammobates geometricus": "Geometric Tortoise (CR)",
    "Psammobates tentorius": "Tent Tortoise",
    "Homopus areolatus": "Parrot-beaked Padloper",
    "Centrochelys sulcata": "African Spurred Tortoise",
  };

  void _generateCustomId(String species) {
    final prefix = species.substring(0, 4).toUpperCase();
    final year = DateTime.now().year;
    setState(() {
      _customId = "$prefix-$year-004";
    });
  }

  void _simulateBluetoothRfidScan() {
    setState(() => _isScanningPitTag = true);
    Future.delayed(const Duration(milliseconds: 1200), () {
      if (mounted) {
        setState(() {
          _isScanningPitTag = false;
          _pitTagController.text = "982000365829142";
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Bluetooth RFID Wand: Transponder Tag Read (FDX-B 15-digit)"),
            backgroundColor: AppColors.primaryGreen,
          ),
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Specimen Intake & Identification"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Species & Taxonomy Card
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Taxonomy & Classification",
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: _selectedSpecies,
                        decoration: const InputDecoration(
                          labelText: "Scientific Name",
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.nature),
                        ),
                        items: _speciesOptions.keys.map((s) {
                          return DropdownMenuItem(
                            value: s,
                            child: Text(s, style: const TextStyle(fontStyle: FontStyle.italic)),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() {
                              _selectedSpecies = val;
                              _commonName = _speciesOptions[val]!;
                              _generateCustomId(val);
                            });
                          }
                        },
                      ),
                      const SizedBox(height: 8),
                      Text("Common Name: $_commonName", style: const TextStyle(fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Unique Identity Card
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Unique Specimen Identifier",
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const SizedBox(height: 8),
                      TextFormField(
                        initialValue: _customId,
                        decoration: const InputDecoration(
                          labelText: "Configured ID Pattern",
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.badge),
                          helperText: "Generated via template: {SPECIES}-{YEAR}-{SEQ}",
                        ),
                        onChanged: (val) => _customId = val,
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              value: _sex,
                              decoration: const InputDecoration(labelText: "Sex", border: OutlineInputBorder()),
                              items: ["Female", "Male", "Juvenile", "Undetermined"]
                                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                                  .toList(),
                              onChanged: (val) => setState(() => _sex = val!),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              value: _status,
                              decoration: const InputDecoration(labelText: "Status", border: OutlineInputBorder()),
                              items: ["Intake", "InRehab", "Wild", "Breeding"]
                                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                                  .toList(),
                              onChanged: (val) => setState(() => _status = val!),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // PIT Tag / Microchip Card (with Bluetooth Wand Integration)
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
                              Icon(Icons.nfc, color: AppColors.primaryGreen),
                              SizedBox(width: 8),
                              Text("PIT Tag (Microchip)", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                            ],
                          ),
                          ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.earthBrown,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                            ),
                            onPressed: _isScanningPitTag ? null : _simulateBluetoothRfidScan,
                            icon: _isScanningPitTag
                                ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                : const Icon(Icons.bluetooth_searching, size: 16),
                            label: const Text("Scan Wand", style: TextStyle(fontSize: 12)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _pitTagController,
                        decoration: const InputDecoration(
                          labelText: "15-Digit FDX-B RFID Microchip",
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.qr_code),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Interactive 2D Marginal Scute Notch Picker Widget
              ScuteNotchPicker(
                initialCode: _notchCode,
                onNotchCodeChanged: (code) {
                  setState(() => _notchCode = code);
                },
              ),

              const SizedBox(height: 24),

              // Save Button
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryGreen,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text("Specimen '$_customId' saved offline with notch code: ${_notchCode.isEmpty ? 'None' : _notchCode}"),
                      backgroundColor: AppColors.primaryGreen,
                    ),
                  );
                  Navigator.pop(context);
                },
                child: const Text("Complete Intake & Save", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
