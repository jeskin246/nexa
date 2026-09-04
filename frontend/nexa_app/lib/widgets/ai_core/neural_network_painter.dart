import 'dart:math';
import 'package:flutter/material.dart';
import '../../core/theme.dart';

/// Connected node network visualizer for PLANNING state.
class NeuralNetworkPainter extends CustomPainter {
  final double animationValue;

  NeuralNetworkPainter({required this.animationValue});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) * 0.38;
    const nodeCount = 12;

    final nodes = <Offset>[];
    for (int i = 0; i < nodeCount; i++) {
      final angle = (i / nodeCount) * 2 * pi + (animationValue * 2 * pi * 0.1);
      final r = radius * (0.6 + 0.4 * sin(animationValue * 2 * pi + i));
      nodes.add(Offset(
        center.dx + cos(angle) * r,
        center.dy + sin(angle) * r,
      ));
    }

    // Draw lines between nearby nodes
    final linePaint = Paint()
      ..color = NexaTheme.accentCyan.withValues(alpha: 0.3)
      ..strokeWidth = 1.2;

    for (int i = 0; i < nodeCount; i++) {
      for (int j = i + 1; j < nodeCount; j++) {
        final dist = (nodes[i] - nodes[j]).distance;
        if (dist < radius * 0.9) {
          linePaint.color = NexaTheme.accentCyan.withValues(
            alpha: (1 - dist / (radius * 0.9)) * 0.4,
          );
          canvas.drawLine(nodes[i], nodes[j], linePaint);
        }
      }
    }

    // Draw nodes
    final nodePaint = Paint()
      ..color = NexaTheme.accentPurple
      ..style = PaintingStyle.fill;

    for (var node in nodes) {
      canvas.drawCircle(node, 4.0, nodePaint);
    }
  }

  @override
  bool shouldRepaint(covariant NeuralNetworkPainter oldDelegate) =>
      oldDelegate.animationValue != animationValue;
}
