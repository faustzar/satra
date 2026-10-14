import 'package:flutter/material.dart';
import '../../../../core/constants/colors.dart';

class ScuteNotchPicker extends StatefulWidget {
  final String? initialCode;
  final ValueChanged<String> onNotchCodeChanged;
  final bool readOnly;

  const ScuteNotchPicker({
    super.key,
    this.initialCode,
    required this.onNotchCodeChanged,
    this.readOnly = false,
  });

  @override
  State<ScuteNotchPicker> createState() => _ScuteNotchPickerState();
}

class _ScuteNotchPickerState extends State<ScuteNotchPicker> {
  final Set<String> _selectedNotches = {};

  final List<String> _leftMarginals = [
    'L1', 'L2', 'L3', 'L4', 'L5', 'L6',
    'L7', 'L8', 'L9', 'L10', 'L11', 'L12'
  ];

  final List<String> _rightMarginals = [
    'R1', 'R2', 'R3', 'R4', 'R5', 'R6',
    'R7', 'R8', 'R9', 'R10', 'R11', 'R12'
  ];

  @override
  void initState() {
    super.initState();
    if (widget.initialCode != null && widget.initialCode!.isNotEmpty) {
      final parts = widget.initialCode!.split('-');
      for (final part in parts) {
        final trimmed = part.trim();
        if (trimmed.isNotEmpty) {
          _selectedNotches.add(trimmed);
        }
      }
    }
  }

  void _toggleNotch(String scuteId) {
    if (widget.readOnly) return;
    setState(() {
      if (_selectedNotches.contains(scuteId)) {
        _selectedNotches.remove(scuteId);
      } else {
        _selectedNotches.add(scuteId);
      }
    });

    final sorted = _selectedNotches.toList()..sort((a, b) {
      final aIsL = a.startsWith('L');
      final bIsL = b.startsWith('L');
      if (aIsL && !bIsL) return -1;
      if (!aIsL && bIsL) return 1;
      final aNum = int.tryParse(a.substring(1)) ?? 0;
      final bNum = int.tryParse(b.substring(1)) ?? 0;
      return aNum.compareTo(bNum);
    });

    final formattedCode = sorted.join('-');
    widget.onNotchCodeChanged(formattedCode);
  }

  void _clearNotches() {
    if (widget.readOnly) return;
    setState(() => _selectedNotches.clear());
    widget.onNotchCodeChanged('');
  }

  Widget _buildScuteButton(String id, {bool isLeft = true}) {
    final isSelected = _selectedNotches.contains(id);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.0),
      child: InkWell(
        onTap: () => _toggleNotch(id),
        borderRadius: BorderRadius.circular(6),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          width: 44,
          height: 28,
          decoration: BoxDecoration(
            color: isSelected
                ? AppColors.fieldHighContrastYellow
                : const Color(0xFFE0E0E0),
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(isLeft ? 8 : 2),
              bottomLeft: Radius.circular(isLeft ? 8 : 2),
              topRight: Radius.circular(isLeft ? 2 : 8),
              bottomRight: Radius.circular(isLeft ? 2 : 8),
            ),
            border: Border.all(
              color: isSelected ? AppColors.earthBrown : Colors.grey[400]!,
              width: isSelected ? 2 : 1,
            ),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: AppColors.fieldHighContrastYellow.withOpacity(0.5),
                      blurRadius: 4,
                      offset: const Offset(0, 1),
                    )
                  ]
                : [],
          ),
          child: Center(
            child: Text(
              id,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: isSelected ? Colors.black : Colors.black87,
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final codeString = _selectedNotches.isEmpty ? "No notches marked" : _selectedNotches.join('-');

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.shield, color: AppColors.primaryGreen),
                    SizedBox(width: 8),
                    Text(
                      "Marginal Scute Notch Code",
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                  ],
                ),
                if (!widget.readOnly && _selectedNotches.isNotEmpty)
                  TextButton.icon(
                    onPressed: _clearNotches,
                    icon: const Icon(Icons.clear, size: 16),
                    label: const Text("Clear", style: TextStyle(fontSize: 12)),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              "Tap marginal scutes (L1–L12, R1–R12) to record physical file notches.",
              style: TextStyle(color: Colors.grey[600], fontSize: 12),
            ),
            const SizedBox(height: 12),

            // Visual Carapace Shell Diagram
            Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
              decoration: BoxDecoration(
                color: const Color(0xFFF4F1EA),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.brown[200]!),
              ),
              child: Column(
                children: [
                  // Nuchal / Cervical Scute (Top Center)
                  Container(
                    width: 50,
                    height: 20,
                    decoration: BoxDecoration(
                      color: Colors.brown[300],
                      borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
                      border: Border.all(color: Colors.brown[600]!),
                    ),
                    child: const Center(
                      child: Text(
                        "Nuchal",
                        style: TextStyle(fontSize: 9, color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),

                  // Shell Body: Left Marginals | Center Vertebral/Costal | Right Marginals
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Left Marginals Column
                      Column(
                        children: _leftMarginals.map((id) => _buildScuteButton(id, isLeft: true)).toList(),
                      ),

                      const SizedBox(width: 8),

                      // Center Carapace Vertebral & Pleural Scutes Representation
                      Container(
                        width: 140,
                        height: 380,
                        decoration: BoxDecoration(
                          color: const Color(0xFF8D6E63),
                          borderRadius: const BorderRadius.all(Radius.elliptical(70, 190)),
                          border: Border.all(color: const Color(0xFF4E342E), width: 2),
                        ),
                        child: CustomPaint(
                          painter: VertebralScutePainter(),
                          child: const Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                              children: [
                                Text("V1", style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                                Text("V2", style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                                Text("V3", style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                                Text("V4", style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                                Text("V5", style: TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.bold)),
                              ],
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(width: 8),

                      // Right Marginals Column
                      Column(
                        children: _rightMarginals.map((id) => _buildScuteButton(id, isLeft: false)).toList(),
                      ),
                    ],
                  ),

                  // Supracaudal Scute (Bottom Center)
                  Container(
                    width: 60,
                    height: 22,
                    decoration: BoxDecoration(
                      color: Colors.brown[300],
                      borderRadius: const BorderRadius.vertical(bottom: Radius.circular(8)),
                      border: Border.all(color: Colors.brown[600]!),
                    ),
                    child: const Center(
                      child: Text(
                        "Supracaudal",
                        style: TextStyle(fontSize: 9, color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Real-Time Generated Code Badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: _selectedNotches.isEmpty ? Colors.grey[200] : const Color(0xFFFFF9C4),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _selectedNotches.isEmpty ? Colors.grey[400]! : AppColors.accentGold,
                  width: 1.5,
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("Selected Notch Code:", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                  Text(
                    codeString,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                      color: _selectedNotches.isEmpty ? Colors.grey[700] : AppColors.earthBrown,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class VertebralScutePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF3E2723)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    final h = size.height;
    final w = size.width;

    // Draw vertebral horizontal division lines
    for (int i = 1; i < 5; i++) {
      final y = h * (i / 5.0);
      canvas.drawLine(Offset(10, y), Offset(w - 10, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
