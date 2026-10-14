import 'package:flutter/material.dart';
import '../../../core/constants/colors.dart';
import '../models/specimen.dart';
import 'intake_screen.dart';

class SpecimenListScreen extends StatefulWidget {
  const SpecimenListScreen({super.key});

  @override
  State<SpecimenListScreen> createState() => _SpecimenListScreenState();
}

class _SpecimenListScreenState extends State<SpecimenListScreen> {
  final List<Specimen> _specimens = [
    Specimen(
      id: "1",
      customIdentifier: "LEOP-2026-001",
      species: "Stigmochelys pardalis",
      commonName: "Leopard Tortoise",
      pitTagNumber: "982000365829104",
      notchCode: "L1-R4",
      sex: "Female",
      status: "InRehab",
      createdAt: DateTime.now().subtract(const Duration(days: 14)),
      isSynced: true,
    ),
    Specimen(
      id: "2",
      customIdentifier: "ANGU-2026-014",
      species: "Chersina angulata",
      commonName: "Angulate Tortoise",
      pitTagNumber: "982000365829105",
      notchCode: "L2-R2",
      sex: "Male",
      status: "Wild",
      createdAt: DateTime.now().subtract(const Duration(days: 30)),
      isSynced: true,
    ),
    Specimen(
      id: "3",
      customIdentifier: "GEOM-2026-003",
      species: "Psammobates geometricus",
      commonName: "Geometric Tortoise (CR)",
      notchCode: "L3-R1",
      sex: "Female",
      status: "Wild",
      createdAt: DateTime.now().subtract(const Duration(days: 4)),
      isSynced: false,
    ),
  ];

  Color _getStatusColor(String status) {
    switch (status) {
      case "Wild":
        return AppColors.statusWild;
      case "InRehab":
        return AppColors.statusInRehab;
      case "Released":
        return AppColors.statusReleased;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("SATRA Tortoises"),
        actions: [
          IconButton(
            icon: const Icon(Icons.sync),
            tooltip: "Sync with Cloud",
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("Syncing offline queue with Render backend...")),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Search & Filter Bar
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: TextField(
              decoration: InputDecoration(
                hintText: "Search ID, species, microchip, or notch code...",
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                filled: true,
                fillColor: Colors.grey[100],
              ),
            ),
          ),

          // Specimen List
          Expanded(
            child: ListView.builder(
              itemCount: _specimens.length,
              itemBuilder: (context, index) {
                final sp = _specimens[index];
                return Card(
                  margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    leading: CircleAvatar(
                      backgroundColor: AppColors.primaryGreen.withOpacity(0.15),
                      child: const Icon(Icons.cruelty_free, color: AppColors.primaryGreen),
                    ),
                    title: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          sp.customIdentifier,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: _getStatusColor(sp.status).withOpacity(0.15),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            sp.status,
                            style: TextStyle(
                              color: _getStatusColor(sp.status),
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text(
                          sp.species,
                          style: const TextStyle(fontStyle: FontStyle.italic, fontWeight: FontWeight.w500),
                        ),
                        Text(
                          "Sex: ${sp.sex} • Notch: ${sp.notchCode ?? 'None'}",
                          style: TextStyle(color: Colors.grey[600], fontSize: 13),
                        ),
                      ],
                    ),
                    trailing: Icon(
                      sp.isSynced ? Icons.cloud_done : Icons.cloud_queue,
                      color: sp.isSynced ? Colors.green : Colors.orange,
                      size: 20,
                    ),
                    onTap: () {
                      // Navigate to detail
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.primaryGreen,
        foregroundColor: Colors.white,
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const IntakeScreen()),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text("New Intake"),
      ),
    );
  }
}
