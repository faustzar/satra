import 'package:flutter/material.dart';
import '../../../../core/constants/colors.dart';

enum ScientificCameraAngle {
  carapace,
  plastron,
  head,
  caudal,
  lateral,
  injury,
}

class ScientificViewfinderOverlay extends StatelessWidget {
  final ScientificCameraAngle angle;
  final bool isPerpendicular;
  final double tiltDegrees;
  final VoidCallback onCapture;
  final ValueChanged<ScientificCameraAngle> onAngleChanged;

  const ScientificViewfinderOverlay({
    super.key,
    required this.angle,
    this.isPerpendicular = true,
    this.tiltDegrees = 89.5,
    required this.onCapture,
    required this.onAngleChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Silhouette Reticle & Grid
        Center(
          child: CustomPaint(
            size: const Size(260, 320),
            painter: ViewfinderReticlePainter(
              angle: angle,
              isPerpendicular: isPerpendicular,
            ),
          ),
        ),

        // Perpendicularity Gyro Sensor Badge
        Positioned(
          top: 16,
          left: 16,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: isPerpendicular
                  ? AppColors.primaryGreen.withOpacity(0.85)
                  : Colors.red[900]!.withOpacity(0.85),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white30),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isPerpendicular ? Icons.check_circle : Icons.screen_rotation,
                  color: Colors.white,
                  size: 16,
                ),
                const SizedBox(width: 6),
                Text(
                  isPerpendicular
                      ? "Perpendicular ($tiltDegrees° ±10°)"
                      : "Tilt Camera (Currently $tiltDegrees°)",
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ),

        // Camera Angle Selector Chips Bar
        Positioned(
          top: 60,
          left: 16,
          right: 16,
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildAngleChip(ScientificCameraAngle.carapace, "1. Carapace (Dorsal)", Icons.shield),
                _buildAngleChip(ScientificCameraAngle.plastron, "2. Plastron (Ventral)", Icons.splitscreen),
                _buildAngleChip(ScientificCameraAngle.head, "3. Head & Nuchal", Icons.face),
                _buildAngleChip(ScientificCameraAngle.caudal, "4. Caudal / Anal", Icons.arrow_downward),
                _buildAngleChip(ScientificCameraAngle.lateral, "5. Lateral Bridge", Icons.swap_horiz),
                _buildAngleChip(ScientificCameraAngle.injury, "6. Predation / Scars", Icons.medical_services),
              ],
            ),
          ),
        ),

        // Bottom Capture Controls
        Positioned(
          bottom: 24,
          left: 0,
          right: 0,
          child: Column(
            children: [
              Text(
                _getInstructionText(angle),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  shadows: [Shadow(blurRadius: 4, color: Colors.black)],
                ),
              ),
              const SizedBox(height: 12),
              GestureDetector(
                onTap: onCapture,
                child: Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 4),
                    color: isPerpendicular
                        ? AppColors.fieldHighContrastYellow
                        : Colors.white24,
                  ),
                  child: Center(
                    child: Icon(
                      Icons.camera_alt,
                      color: isPerpendicular ? Colors.black : Colors.white,
                      size: 32,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildAngleChip(ScientificCameraAngle chipAngle, String label, IconData icon) {
    final isSelected = angle == chipAngle;
    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: FilterChip(
        avatar: Icon(icon, size: 16, color: isSelected ? Colors.black : Colors.white70),
        label: Text(label),
        selected: isSelected,
        selectedColor: AppColors.fieldHighContrastYellow,
        backgroundColor: Colors.black54,
        labelStyle: TextStyle(
          color: isSelected ? Colors.black : Colors.white,
          fontSize: 11,
          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        ),
        onSelected: (_) => onAngleChanged(chipAngle),
      ),
    );
  }

  String _getInstructionText(ScientificCameraAngle a) {
    switch (a) {
      case ScientificCameraAngle.carapace:
        return "Align oval guide over carapace with Nuchal scute at top";
      case ScientificCameraAngle.plastron:
        return "Center plastron scute bridge horizontally between reticles";
      case ScientificCameraAngle.head:
        return "Macro focus on rhinotheca (beak) and prefrontal scales";
      case ScientificCameraAngle.caudal:
        return "Frame anal notch and tail curvature for sex determination";
      case ScientificCameraAngle.lateral:
        return "Keep camera parallel to shell bridge for height-to-length ratio";
      case ScientificCameraAngle.injury:
        return "Close-up macro of canine punctures, fractures, or worn notches";
    }
  }
}

class ViewfinderReticlePainter extends CustomPainter {
  final ScientificCameraAngle angle;
  final bool isPerpendicular;

  ViewfinderReticlePainter({
    required this.angle,
    required this.isPerpendicular,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = isPerpendicular
          ? AppColors.fieldHighContrastYellow.withOpacity(0.85)
          : Colors.red.withOpacity(0.85)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final center = Offset(size.width / 2, size.height / 2);

    switch (angle) {
      case ScientificCameraAngle.carapace:
      case ScientificCameraAngle.plastron:
        // Oval carapace/plastron contour
        final rect = Rect.fromCenter(center: center, width: size.width * 0.85, height: size.height * 0.9);
        canvas.drawOval(rect, paint);

        // Vertebral scute landmark ticks
        final tickPaint = Paint()
          ..color = Colors.white54
          ..strokeWidth = 1.0;
        canvas.drawLine(Offset(center.dx, rect.top), Offset(center.dx, rect.bottom), tickPaint);
        break;

      case ScientificCameraAngle.head:
        // Circular cranial target with crosshairs
        canvas.drawCircle(center, size.width * 0.35, paint);
        canvas.drawLine(Offset(center.dx - 20, center.dy), Offset(center.dx + 20, center.dy), paint);
        canvas.drawLine(Offset(center.dx, center.dy - 20), Offset(center.dx, center.dy + 20), paint);
        break;

      case ScientificCameraAngle.caudal:
      case ScientificCameraAngle.lateral:
      case ScientificCameraAngle.injury:
        // Rectangular macro boundary with corner brackets
        final r = Rect.fromCenter(center: center, width: size.width * 0.9, height: size.height * 0.7);
        canvas.drawRect(r, paint);
        break;
    }
  }

  @override
  bool shouldRepaint(covariant ViewfinderReticlePainter oldDelegate) {
    return oldDelegate.angle != angle || oldDelegate.isPerpendicular != isPerpendicular;
  }
}
