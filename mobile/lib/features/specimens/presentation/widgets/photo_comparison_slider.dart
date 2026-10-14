import 'package:flutter/material.dart';
import '../../../../core/constants/colors.dart';

class PhotoComparisonSlider extends StatefulWidget {
  final String beforeTitle;
  final String beforeSubtitle;
  final String afterTitle;
  final String afterSubtitle;
  final Widget beforeChild;
  final Widget afterChild;
  final double initialPosition; // 0.0 to 1.0

  const PhotoComparisonSlider({
    super.key,
    required this.beforeTitle,
    required this.beforeSubtitle,
    required this.afterTitle,
    required this.afterSubtitle,
    required this.beforeChild,
    required this.afterChild,
    this.initialPosition = 0.5,
  });

  @override
  State<PhotoComparisonSlider> createState() => _PhotoComparisonSliderState();
}

class _PhotoComparisonSliderState extends State<PhotoComparisonSlider> {
  late double _dividerPosition; // 0.0 (all after) to 1.0 (all before)
  bool _isSideBySide = false;

  @override
  void initState() {
    super.initState();
    _dividerPosition = widget.initialPosition;
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header with Mode Switch
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.compare, color: AppColors.primaryGreen),
                    SizedBox(width: 8),
                    Text(
                      "Longitudinal Healing Progression",
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                    ),
                  ],
                ),
                IconButton(
                  tooltip: _isSideBySide ? "Switch to Split Wipe Slider" : "Switch to Side-by-Side View",
                  icon: Icon(
                    _isSideBySide ? Icons.view_day : Icons.view_column,
                    color: AppColors.earthBrown,
                  ),
                  onPressed: () {
                    setState(() => _isSideBySide = !_isSideBySide);
                  },
                ),
              ],
            ),
          ),

          // Side-by-Side View Mode
          if (_isSideBySide)
            Padding(
              padding: const EdgeInsets.all(12.0),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: SizedBox(height: 220, child: widget.beforeChild),
                        ),
                        const SizedBox(height: 6),
                        Text(widget.beforeTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                        Text(widget.beforeSubtitle, style: TextStyle(color: Colors.grey[600], fontSize: 11)),
                      ],
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: SizedBox(height: 220, child: widget.afterChild),
                        ),
                        const SizedBox(height: 6),
                        Text(widget.afterTitle, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.primaryGreen)),
                        Text(widget.afterSubtitle, style: TextStyle(color: Colors.grey[600], fontSize: 11)),
                      ],
                    ),
                  ),
                ],
              ),
            )
          else
            // Interactive Wipe / Split-Screen Drag Slider
            LayoutBuilder(
              builder: (context, constraints) {
                final totalWidth = constraints.maxWidth;
                final totalHeight = 260.0;
                final dividerX = totalWidth * _dividerPosition;

                return GestureDetector(
                  onHorizontalDragUpdate: (details) {
                    setState(() {
                      _dividerPosition = (_dividerPosition + details.delta.dx / totalWidth).clamp(0.02, 0.98);
                    });
                  },
                  child: SizedBox(
                    width: totalWidth,
                    height: totalHeight,
                    child: Stack(
                      children: [
                        // Layer 1: After Image (Full background)
                        Positioned.fill(
                          child: widget.afterChild,
                        ),

                        // Layer 2: Before Image (Clipped to dividerX)
                        Positioned(
                          left: 0,
                          top: 0,
                          bottom: 0,
                          width: dividerX,
                          child: ClipRect(
                            child: OverflowBox(
                              maxWidth: totalWidth,
                              maxHeight: totalHeight,
                              minWidth: totalWidth,
                              minHeight: totalHeight,
                              alignment: Alignment.centerLeft,
                              child: widget.beforeChild,
                            ),
                          ),
                        ),

                        // Left Badge: Before
                        Positioned(
                          left: 12,
                          top: 12,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.black.withOpacity(0.75),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.white38),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  widget.beforeTitle,
                                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                                ),
                                Text(
                                  widget.beforeSubtitle,
                                  style: const TextStyle(color: Colors.white70, fontSize: 10),
                                ),
                              ],
                            ),
                          ),
                        ),

                        // Right Badge: After
                        Positioned(
                          right: 12,
                          top: 12,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppColors.primaryGreen.withOpacity(0.85),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.white38),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(
                                  widget.afterTitle,
                                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                                ),
                                Text(
                                  widget.afterSubtitle,
                                  style: const TextStyle(color: Colors.white70, fontSize: 10),
                                ),
                              ],
                            ),
                          ),
                        ),

                        // Vertical Divider Line
                        Positioned(
                          left: dividerX - 1.5,
                          top: 0,
                          bottom: 0,
                          width: 3,
                          child: Container(
                            color: Colors.white,
                            child: Container(
                              color: AppColors.fieldHighContrastYellow.withOpacity(0.9),
                            ),
                          ),
                        ),

                        // Center Draggable Handle Pill
                        Positioned(
                          left: dividerX - 18,
                          top: (totalHeight / 2) - 18,
                          child: Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: AppColors.fieldHighContrastYellow,
                              shape: BoxShape.circle,
                              border: Border.all(color: Colors.black87, width: 2),
                              boxShadow: const [
                                BoxShadow(
                                  color: Colors.black45,
                                  blurRadius: 6,
                                  offset: Offset(0, 2),
                                )
                              ],
                            ),
                            child: const Center(
                              child: Icon(
                                Icons.unfold_more,
                                size: 20,
                                color: Colors.black,
                              ),
                            ),
                          ),
                        ),

                        // Bottom Help Hint
                        Positioned(
                          bottom: 8,
                          left: 0,
                          right: 0,
                          child: Center(
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.black54,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Text(
                                "◀ Drag slider left/right to compare healing progression ▶",
                                style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
        ],
      ),
    );
  }
}
