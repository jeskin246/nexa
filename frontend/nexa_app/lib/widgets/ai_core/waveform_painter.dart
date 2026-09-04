import 'dart:math';
import 'package:flutter/material.dart';
import '../../core/theme.dart';

/// Audio waveform visualizer for LISTENING state.
class WaveformPainter extends CustomPainter {
  final double animationValue;
  final Color color;

  WaveformPainter({
    required this.animationValue,
    this.color = NexaTheme.accentCyan,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 3.0
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = min(size.width, size.height) * 0.35;
    const barCount = 48;

    for (int i = 0; i < barCount; i++) {
      final angle = (i / barCount) * 2 * pi;
      final phase = animationValue * 2 * pi * 2 + i * 0.2;
      final barHeight = 8 + 20 * sin(phase).abs();

      final inner = Offset(
        center.dx + cos(angle) * (radius - barHeight / 2),
        center.dy + sin(angle) * (radius - barHeight / 2),
      );

      final outer = Offset(
        center.dx + cos(angle) * (radius + barHeight / 2),
        center.dy + sin(angle) * (radius + barHeight / 2),
      );

      canvas.drawLine(inner, outer, paint);
    }
  }

  @override
  bool shouldRepaint(covariant WaveformPainter oldDelegate) =>
      oldDelegate.animationValue != animationValue;
}
