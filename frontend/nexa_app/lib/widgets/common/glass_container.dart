import 'dart:ui';
import 'package:flutter/material.dart';
import '../../core/theme.dart';

/// Reusable glassmorphism panel container widget.
class GlassContainer extends StatelessWidget {
  final Widget child;
  final double borderRadius;
  final EdgeInsetsGeometry padding;
  final EdgeInsetsGeometry margin;
  final Color? borderColor;
  final Color? backgroundColor;
  final double blur;
  final double? width;
  final double? height;

  const GlassContainer({
    super.key,
    required this.child,
    this.borderRadius = 16,
    this.padding = const EdgeInsets.all(16),
    this.margin = EdgeInsets.zero,
    this.borderColor,
    this.backgroundColor,
    this.blur = 12,
    this.width,
    this.height,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      margin: margin,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: backgroundColor ?? const Color(0x15ffffff),
              borderRadius: BorderRadius.circular(borderRadius),
              border: Border.all(
                color: borderColor ?? NexaTheme.glassBorder,
                width: 1,
              ),
              gradient: NexaTheme.panelGradient,
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}
