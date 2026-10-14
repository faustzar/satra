import 'package:flutter/material.dart';
import '../../../core/constants/colors.dart';

class BreedingScreen extends StatefulWidget {
  const BreedingScreen({super.key});

  @override
  State<BreedingScreen> createState() => _BreedingScreenState();
}

class _BreedingScreenState extends State<BreedingScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  double _incubationTemp = 31.8;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  String _getPredictedSex(double temp) {
    if (temp >= 31.5) return "Predominantly Female (TSD Pattern Ia)";
    if (temp <= 30.0) return "Predominantly Male (TSD Pattern Ia)";
    return "Mixed Sex Ratio (Near Pivotal Temp ~30.8°C)";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Breeding & Incubation"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.favorite), text: "Pairings"),
            Tab(icon: Icon(Icons.egg), text: "Clutches & Eggs"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Pairings Tab
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            "Pairing: PAIR-2026-004",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.green[100],
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Text("Copulation Confirmed", style: TextStyle(color: Colors.green, fontSize: 12, fontWeight: FontWeight.bold)),
                          )
                        ],
                      ),
                      const Divider(),
                      const Text("Dam (Female): LEOP-2026-001 (Stigmochelys pardalis)"),
                      const Text("Sire (Male): LEOP-2025-089"),
                      const Text("Location: Breeding Enclosure Alpha"),
                      const SizedBox(height: 8),
                      Text("Observed Behavior: Ramming, head bobbing, vocalization", style: TextStyle(color: Colors.grey[700], fontStyle: FontStyle.italic)),
                    ],
                  ),
                ),
              ),
            ],
          ),

          // Clutches & Incubation Tab
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // TSD Incubation Controller Card
              Card(
                elevation: 2,
                color: const Color(0xFFFFF8E1),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: const BorderSide(color: AppColors.accentGold),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.thermostat, color: AppColors.earthBrown),
                          SizedBox(width: 8),
                          Text(
                            "TSD (Sex Determination) Incubator",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.earthBrown),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text("Target Temp: ${_incubationTemp.toStringAsFixed(1)}°C"),
                      Slider(
                        value: _incubationTemp,
                        min: 28.0,
                        max: 33.5,
                        divisions: 55,
                        activeColor: AppColors.earthBrown,
                        onChanged: (val) => setState(() => _incubationTemp = val),
                      ),
                      Text(
                        _getPredictedSex(_incubationTemp),
                        style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primaryGreen),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Active Clutch Card
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text("Clutch: CLUTCH-2026-012", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          Chip(label: Text("Day 45 / ~120")),
                        ],
                      ),
                      const Divider(),
                      const Text("Species: Stigmochelys pardalis"),
                      const Text("Total Eggs: 11 (9 Fertile, 1 Chalking Band, 1 Infertile)"),
                      const Text("Incubator: Unit B, Tray 2 (Vermiculite 1:1)"),
                      const SizedBox(height: 12),
                      LinearProgressIndicator(
                        value: 45 / 120,
                        backgroundColor: Colors.grey[200],
                        color: AppColors.primaryGreen,
                        minHeight: 8,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
