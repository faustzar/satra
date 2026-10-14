import 'package:flutter/material.dart';
import '../../../../core/constants/colors.dart';
import '../models/specimen.dart';
import 'widgets/photo_comparison_slider.dart';
import 'widgets/scute_notch_picker.dart';

class SpecimenDetailScreen extends StatefulWidget {
  final Specimen specimen;

  const SpecimenDetailScreen({
    super.key,
    required this.specimen,
  });

  @override
  State<SpecimenDetailScreen> createState() => _SpecimenDetailScreenState();
}

class _SpecimenDetailScreenState extends State<SpecimenDetailScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  Widget build(BuildContext context) {
    final sp = widget.specimen;

    return Scaffold(
      appBar: AppBar(
        title: Text(sp.customIdentifier),
        actions: [
          IconButton(
            icon: const Icon(Icons.picture_as_pdf),
            tooltip: "Export PDF Health & Studbook Certificate",
            onPressed: () {
              showModalBottomSheet(
                context: context,
                shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
                ),
                builder: (context) => Padding(
                  padding: const EdgeInsets.all(20.0),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.picture_as_pdf, color: AppColors.primaryGreen, size: 28),
                          const SizedBox(width: 12),
                          Text(
                            "Export Report: ${sp.customIdentifier}",
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        "Generate official conservation health dossier and studbook pedigree certificate.",
                        style: TextStyle(color: Colors.grey[600], fontSize: 13),
                      ),
                      const SizedBox(height: 16),
                      ListTile(
                        leading: const CircleAvatar(
                          backgroundColor: Color(0xFFE8F5E9),
                          child: Icon(Icons.download, color: AppColors.primaryGreen),
                        ),
                        title: const Text("Download PDF Certificate", style: TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: const Text("A4 CITES / Veterinary formatted document"),
                        onTap: () {
                          Navigator.pop(context);
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text("Downloading SATRA_Report_${sp.customIdentifier}.pdf..."),
                              backgroundColor: AppColors.primaryGreen,
                            ),
                          );
                        },
                      ),
                      ListTile(
                        leading: const CircleAvatar(
                          backgroundColor: Color(0xFFFFF8E1),
                          child: Icon(Icons.share, color: AppColors.earthBrown),
                        ),
                        title: const Text("Share Sighting Telemetry Link", style: TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: const Text("Encrypted anti-poaching link for rangers"),
                        onTap: () {
                          Navigator.pop(context);
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text("Secure telemetry link copied to clipboard.")),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.edit),
            tooltip: "Edit Profile",
            onPressed: () {},
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: const [
            Tab(icon: Icon(Icons.compare), text: "Healing Slider"),
            Tab(icon: Icon(Icons.photo_library), text: "Photo Album"),
            Tab(icon: Icon(Icons.medical_information), text: "Clinical History"),
            Tab(icon: Icon(Icons.fingerprint), text: "ID & Notches"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Tab 1: Longitudinal Healing Progression Slider
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Specimen Quick Summary Card
              _buildSpecimenHeaderCard(sp),
              const SizedBox(height: 16),

              // Interactive Photo Comparison Slider
              PhotoComparisonSlider(
                beforeTitle: "Day 1: Intake",
                beforeSubtitle: "2026-03-12 • Vehicle Strike Fracture",
                afterTitle: "Day 45: Rehab",
                afterSubtitle: "2026-04-26 • Keratin Bridged",
                beforeChild: Container(
                  color: const Color(0xFF3E2723),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      const Icon(Icons.healing, size: 80, color: Colors.white24),
                      Container(
                        padding: const EdgeInsets.all(16),
                        child: const Text(
                          "Intake Photo:\nAcute 4cm Carapace Fissure across Vertebral scutes 3-4",
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                        ),
                      ),
                      Positioned(
                        bottom: 12,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(color: Colors.red[900], borderRadius: BorderRadius.circular(6)),
                          child: const Text("CRITICAL TRAUMA", style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                ),
                afterChild: Container(
                  color: const Color(0xFF1B5E20),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      const Icon(Icons.verified, size: 80, color: Colors.white24),
                      Container(
                        padding: const EdgeInsets.all(16),
                        child: const Text(
                          "Day 45 Photo:\nEpoxy wire-stabilization removed.\nDense secondary keratinization bridge formed.",
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                        ),
                      ),
                      Positioned(
                        bottom: 12,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(color: Colors.green[800], borderRadius: BorderRadius.circular(6)),
                          child: const Text("HEALED & STABLE", style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 16),

              // Veterinary Healing Notes
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.notes, color: AppColors.primaryGreen),
                          SizedBox(width: 8),
                          Text("Clinical Recovery Evaluation", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        "• Fracture Stabilization: Cerclage wire + medical dental acrylic resin successfully removed on Day 42.",
                        style: TextStyle(color: Colors.grey[800], fontSize: 13),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "• Weight Trend: Positive gain from 1,450g to 1,580g (+130g in 45 days).",
                        style: TextStyle(color: Colors.grey[800], fontSize: 13),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "• Release Readiness: Evaluated for soft-release enclosure conditioning.",
                        style: TextStyle(color: Colors.grey[800], fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          // Tab 2: Categorized Photo Album Gallery
          GridView.count(
            crossAxisCount: 2,
            padding: const EdgeInsets.all(16),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            children: [
              _buildPhotoCard("Dorsal Carapace", "2026-04-26", Icons.shield, Colors.brown[400]!),
              _buildPhotoCard("Ventral Plastron", "2026-04-26", Icons.splitscreen, Colors.brown[300]!),
              _buildPhotoCard("Head & Facial Scales", "2026-04-10", Icons.face, Colors.grey[700]!),
              _buildPhotoCard("Radiograph (X-Ray)", "2026-03-12", Icons.medical_services, Colors.blueGrey[800]!),
              _buildPhotoCard("Left Flank", "2026-04-01", Icons.arrow_back, Colors.brown[500]!),
              _buildPhotoCard("Right Flank", "2026-04-01", Icons.arrow_forward, Colors.brown[500]!),
            ],
          ),

          // Tab 3: Clinical Inspection History
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _buildHistoryCard("Day 45 Check", "2026-04-26", "Mass: 1,580g", "SCL: 216mm", "Jackson: 0.1568", "Score 4/5"),
              _buildHistoryCard("Week 4 Round", "2026-04-10", "Mass: 1,510g", "SCL: 215mm", "Jackson: 0.1519", "Score 3/5"),
              _buildHistoryCard("Week 2 Round", "2026-03-26", "Mass: 1,470g", "SCL: 215mm", "Jackson: 0.1479", "Score 3/5"),
              _buildHistoryCard("Intake Triage", "2026-03-12", "Mass: 1,450g", "SCL: 215mm", "Jackson: 0.1459", "Score 2/5 (Trauma)"),
            ],
          ),

          // Tab 4: ID Marks & Marginal Notches
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
                      const Text("Physical Transponder & Tags", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const Divider(),
                      Text("PIT Tag (Microchip): ${sp.pitTagNumber ?? 'None'}", style: const TextStyle(fontWeight: FontWeight.w600)),
                      Text("Sex: ${sp.sex} • Current Status: ${sp.status}"),
                      Text("Species: ${sp.species}"),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              ScuteNotchPicker(
                initialCode: sp.notchCode ?? "",
                readOnly: true,
                onNotchCodeChanged: (_) {},
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSpecimenHeaderCard(Specimen sp) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 28,
              backgroundColor: AppColors.primaryGreen.withOpacity(0.15),
              child: const Icon(Icons.cruelty_free, color: AppColors.primaryGreen, size: 32),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(sp.customIdentifier, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  Text(sp.species, style: const TextStyle(fontStyle: FontStyle.italic, color: Colors.grey)),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(color: AppColors.accentGold.withOpacity(0.3), borderRadius: BorderRadius.circular(6)),
                        child: Text(sp.status, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.earthBrown)),
                      ),
                      const SizedBox(width: 8),
                      Text("Notch: ${sp.notchCode ?? 'None'}", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPhotoCard(String label, String date, IconData icon, Color bg) {
    return Card(
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Container(
        color: bg,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Icon(icon, size: 54, color: Colors.white24),
            Positioned(
              bottom: 8,
              left: 8,
              right: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(6)),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
                    Text(date, style: const TextStyle(color: Colors.white70, fontSize: 9)),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryCard(String title, String date, String mass, String scl, String ratio, String bcs) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: ListTile(
        leading: const Icon(Icons.health_and_safety, color: AppColors.primaryGreen),
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            Text(date, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 2),
            Text("$mass • $scl • $ratio"),
            Text("BCS: $bcs", style: const TextStyle(color: AppColors.earthBrown, fontWeight: FontWeight.w600, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
