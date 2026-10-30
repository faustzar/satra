import 'package:flutter/material.dart';
import '../../../../core/constants/colors.dart';
import '../../models/photo_record.dart';

class PhotoMarkingInspectorModal extends StatefulWidget {
  final PhotoRecord photo;
  final ValueChanged<List<PhotoMarking>> onSaveMarkings;

  const PhotoMarkingInspectorModal({
    super.key,
    required this.photo,
    required this.onSaveMarkings,
  });

  @override
  State<PhotoMarkingInspectorModal> createState() => _PhotoMarkingInspectorModalState();
}

class _PhotoMarkingInspectorModalState extends State<PhotoMarkingInspectorModal> {
  late List<PhotoMarking> _pins;
  bool _showPins = true;
  String _selectedSchema = "sa_standard";

  @override
  void initState() {
    super.initState();
    _pins = List.from(widget.photo.markings);
  }

  void _addPin(Offset tapPosition, Size containerSize) {
    final xPct = (tapPosition.dx / containerSize.width) * 100;
    final yPct = (tapPosition.dy / containerSize.height) * 100;

    showDialog(
      context: context,
      builder: (ctx) {
        String selectedType = "V-Notch";
        final labelCtrl = TextEditingController(text: "M${_pins.length + 1}");

        return StatefulBuilder(
          builder: (context, setDlgState) {
            return AlertDialog(
              title: const Text("Tag Physical Mark Landmark", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text("Mark Classification:", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<String>(
                    value: selectedType,
                    decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
                    items: const [
                      DropdownMenuItem(value: "V-Notch", child: Text("V-Notch (Standard Marginal Wedge)")),
                      DropdownMenuItem(value: "U-Notch", child: Text("U-Notch (Rounded Punch)")),
                      DropdownMenuItem(value: "Micro-Drill", child: Text("Micro-Drill (Perforation Dot)")),
                      DropdownMenuItem(value: "Predation Scar", child: Text("Predation Scar (Canine / Claw Bite)")),
                      DropdownMenuItem(value: "Natural Scar", child: Text("Natural Scar / Scorch / Defect")),
                      DropdownMenuItem(value: "Epoxy Tag", child: Text("Epoxy / Paint Code")),
                    ],
                    onChanged: (v) {
                      if (v != null) setDlgState(() => selectedType = v);
                    },
                  ),
                  const SizedBox(height: 12),
                  const Text("Scute / Landmark Label:", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: labelCtrl,
                    decoration: const InputDecoration(border: OutlineInputBorder(), hintText: "e.g. M10L, R4, Jackal Puncture", isDense: true),
                  ),
                ],
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.primaryGreen, foregroundColor: Colors.white),
                  onPressed: () {
                    final newPin = PhotoMarking(
                      id: "pin-${DateTime.now().millisecondsSinceEpoch}",
                      type: selectedType,
                      scute: labelCtrl.text.trim().isEmpty ? "Marginal" : labelCtrl.text.trim(),
                      label: labelCtrl.text.trim(),
                      xPercent: xPct,
                      yPercent: yPct,
                    );
                    setState(() => _pins.add(newPin));
                    Navigator.pop(ctx);
                  },
                  child: const Text("Drop Pin"),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Color _getPinColor(String type) {
    switch (type) {
      case "V-Notch":
        return AppColors.fieldHighContrastYellow;
      case "U-Notch":
        return Colors.lightBlueAccent;
      case "Micro-Drill":
        return Colors.pinkAccent;
      case "Predation Scar":
        return Colors.redAccent;
      case "Natural Scar":
        return Colors.orangeAccent;
      case "Epoxy Tag":
        return Colors.purpleAccent;
      default:
        return AppColors.fieldHighContrastYellow;
    }
  }

  String _computeScore() {
    final notches = _pins.where((p) => p.type == "V-Notch" || p.type == "U-Notch").toList();
    if (notches.isEmpty) return "No Notches (0)";

    if (_selectedSchema == "sa_standard") {
      int sum = 0;
      for (int i = 0; i < notches.length; i++) {
        final vals = [1, 2, 4, 7, 10, 20, 40, 70];
        sum += vals[i % vals.length];
      }
      return "Specimen #$sum (SA Decimal Additive)";
    } else if (_selectedSchema == "cagle") {
      return notches.map((p) => p.label).join("-");
    } else {
      int bin = 0;
      for (int i = 0; i < notches.length; i++) {
        bin += (1 << i);
      }
      return "Binary #$bin";
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog.fullscreen(
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(
          backgroundColor: Colors.black,
          foregroundColor: Colors.white,
          title: Text("Photo Markings: ${widget.photo.photoType}"),
          actions: [
            IconButton(
              icon: Icon(_showPins ? Icons.visibility : Icons.visibility_off),
              tooltip: _showPins ? "Hide Pins" : "Show Pins",
              onPressed: () => setState(() => _showPins = !_showPins),
            ),
            IconButton(
              icon: const Icon(Icons.check),
              tooltip: "Save Markings",
              onPressed: () {
                widget.onSaveMarkings(_pins);
                Navigator.pop(context);
              },
            ),
          ],
        ),
        body: Column(
          children: [
            // Interactive Photo Canvas Area
            Expanded(
              flex: 3,
              child: LayoutBuilder(
                builder: (context, constraints) {
                  return GestureDetector(
                    onTapDown: (details) => _addPin(details.localPosition, Size(constraints.maxWidth, constraints.maxHeight)),
                    child: Stack(
                      children: [
                        // Background image / simulation
                        Container(
                          width: constraints.maxWidth,
                          height: constraints.maxHeight,
                          color: const Color(0xFF1E1B18),
                          child: const Center(
                            child: Icon(Icons.shield, size: 140, color: Colors.white12),
                          ),
                        ),

                        // Render Pinned Markings HUD
                        if (_showPins)
                          ..._pins.asMap().entries.map((entry) {
                            final idx = entry.key;
                            final pin = entry.value;
                            return Positioned(
                              left: (pin.xPercent / 100) * constraints.maxWidth - 14,
                              top: (pin.yPercent / 100) * constraints.maxHeight - 14,
                              child: GestureDetector(
                                onTap: () {
                                  showModalBottomSheet(
                                    context: context,
                                    builder: (ctx) => ListTile(
                                      leading: CircleAvatar(
                                        backgroundColor: _getPinColor(pin.type),
                                        child: Text("${idx + 1}", style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
                                      ),
                                      title: Text("${pin.type}: ${pin.label}"),
                                      subtitle: Text("Coordinates: ${pin.xPercent.toStringAsFixed(1)}%, ${pin.yPercent.toStringAsFixed(1)}%"),
                                      trailing: IconButton(
                                        icon: const Icon(Icons.delete, color: Colors.red),
                                        onPressed: () {
                                          setState(() => _pins.removeAt(idx));
                                          Navigator.pop(ctx);
                                        },
                                      ),
                                    ),
                                  );
                                },
                                child: Container(
                                  width: 28,
                                  height: 28,
                                  decoration: BoxDecoration(
                                    color: _getPinColor(pin.type),
                                    shape: BoxShape.circle,
                                    border: Border.all(color: Colors.white, width: 2),
                                    boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 4)],
                                  ),
                                  child: Center(
                                    child: Text(
                                      "${idx + 1}",
                                      style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 11),
                                    ),
                                  ),
                                ),
                              ),
                            );
                          }),

                        // Crosshair Guidance Banner
                        Positioned(
                          bottom: 12,
                          left: 16,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(color: Colors.black87, borderRadius: BorderRadius.circular(6)),
                            child: const Text("Tap anywhere on shell to drop an anatomical pin", style: TextStyle(color: Colors.white70, fontSize: 11)),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),

            // Bottom Inspector HUD
            Container(
              padding: const EdgeInsets.all(16),
              color: const Color(0xFF141210),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text("Active Scheme:", style: TextStyle(color: Colors.white70, fontSize: 12)),
                      DropdownButton<String>(
                        value: _selectedSchema,
                        dropdownColor: const Color(0xFF24201B),
                        style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                        items: const [
                          DropdownMenuItem(value: "sa_standard", child: Text("South African (1-2-4-7)")),
                          DropdownMenuItem(value: "cagle", child: Text("Cagle (L1-L12/R1-R12)")),
                          DropdownMenuItem(value: "binary", child: Text("Binary (1-2-4-8)")),
                        ],
                        onChanged: (v) {
                          if (v != null) setState(() => _selectedSchema = v);
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.black,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white24),
                    ),
                    child: Text(
                      _computeScore(),
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontFamily: "monospace",
                        color: AppColors.fieldHighContrastYellow,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    "Total Pinned: ${_pins.length} landmarks (${_pins.where((p) => p.type == 'Predation Scar').length} Predation Scars)",
                    style: const TextStyle(color: Colors.white60, fontSize: 11),
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
