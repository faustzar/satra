import 'package:flutter/material.dart';
import '../../../core/constants/colors.dart';

class HealthInspectionScreen extends StatefulWidget {
  const HealthInspectionScreen({super.key});

  @override
  State<HealthInspectionScreen> createState() => _HealthInspectionScreenState();
}

class _HealthInspectionScreenState extends State<HealthInspectionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _massController = TextEditingController(text: "1450");
  final _sclController = TextEditingController(text: "215");
  
  int _bodyConditionScore = 3;
  bool _eggsPalpated = false;
  int _estimatedEggs = 0;
  bool _rnsSymptoms = false;
  bool _shellRot = false;
  String _inspectionType = "Scheduled";

  double? _calculateJacksonsRatio() {
    final mass = double.tryParse(_massController.text);
    final sclMm = double.tryParse(_sclController.text);
    if (mass != null && sclMm != null && sclMm > 0) {
      final sclCm = sclMm / 10.0;
      return mass / (sclCm * sclCm * sclCm);
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final ratio = _calculateJacksonsRatio();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Clinical Health Inspection"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Inspection Type Selector
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: "Intake", label: Text("Intake")),
                  ButtonSegment(value: "Scheduled", label: Text("Scheduled")),
                  ButtonSegment(value: "GravidCheck", label: Text("Gravid")),
                ],
                selected: {_inspectionType},
                onSelectionChanged: (newSelection) {
                  setState(() => _inspectionType = newSelection.first);
                },
              ),

              const SizedBox(height: 16),

              // Morphometrics Card
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Morphometrics & Weight",
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: _massController,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "Mass (g)",
                                suffixText: "grams",
                                border: OutlineInputBorder(),
                              ),
                              onChanged: (_) => setState(() {}),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: TextFormField(
                              controller: _sclController,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: "SCL max (mm)",
                                suffixText: "mm",
                                border: OutlineInputBorder(),
                              ),
                              onChanged: (_) => setState(() {}),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      
                      // Real-time Jackson's Ratio & BCS Badge
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.blueGrey[50],
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.blueGrey[200]!),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  "Jackson's Ratio (BCS Index):",
                                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                                ),
                                Text(
                                  ratio != null ? ratio.toStringAsFixed(4) : "N/A",
                                  style: const TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.primaryGreen,
                                  ),
                                ),
                              ],
                            ),
                            Chip(
                              label: Text("Score: $_bodyConditionScore / 5"),
                              backgroundColor: AppColors.accentGold.withOpacity(0.3),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Reproductive Palpation Check
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Reproductive Status (Gravidity)",
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text("Calcified Eggs Palpated in Inguinal Fossa"),
                        value: _eggsPalpated,
                        onChanged: (val) => setState(() => _eggsPalpated = val),
                      ),
                      if (_eggsPalpated)
                        Row(
                          children: [
                            const Text("Estimated Egg Count: "),
                            const SizedBox(width: 12),
                            DropdownButton<int>(
                              value: _estimatedEggs,
                              items: List.generate(12, (i) => DropdownMenuItem(value: i, child: Text("$i eggs"))),
                              onChanged: (val) {
                                if (val != null) setState(() => _estimatedEggs = val);
                              },
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Systemic Symptoms Toggles
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Systemic Symptoms & Clinical Flags",
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text("Runny Nose Syndrome (RNS) / Nares Discharge"),
                        value: _rnsSymptoms,
                        onChanged: (val) => setState(() => _rnsSymptoms = val ?? false),
                      ),
                      CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text("Shell Rot / Fissures / Burn Trauma"),
                        value: _shellRot,
                        onChanged: (val) => setState(() => _shellRot = val ?? false),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

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
                      content: Text("Health inspection recorded offline successfully."),
                      backgroundColor: AppColors.primaryGreen,
                    ),
                  );
                },
                child: const Text("Save Health Inspection", style: TextStyle(fontSize: 16)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
