import 'package:flutter/material.dart';
import '../../core/theme.dart';

/// Animated glowing action button widget.
class GlowButton extends StatefulWidget {
  final String text;
  final IconData? icon;
  final VoidCallback? onPressed;
  final Color color;
  final bool isLoading;
  final double height;

  const GlowButton({
    super.key,
    required this.text,
    this.icon,
    this.onPressed,
    this.color = NexaTheme.accentCyan,
    this.isLoading = false,
    this.height = 48,
  });

  @override
  State<GlowButton> createState() => _GlowButtonState();
}

class _GlowButtonState extends State<GlowButton> with SingleTickerProviderStateMixin {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        height: widget.height,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          boxShadow: _isHovered && widget.onPressed != null
              ? NexaTheme.glowShadow(widget.color, blur: 25)
              : [
                  BoxShadow(
                    color: widget.color.withValues(alpha: 0.2),
                    blurRadius: 10,
                  ),
                ],
        ),
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: widget.onPressed != null ? widget.color : Colors.grey.shade800,
            foregroundColor: NexaTheme.bgDeep,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20),
          ),
          onPressed: widget.isLoading ? null : widget.onPressed,
          child: widget.isLoading
              ? SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: NexaTheme.bgDeep,
                  ),
                )
              : Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (widget.icon != null) ...[
                      Icon(widget.icon, size: 18, color: NexaTheme.bgDeep),
                      const SizedBox(width: 8),
                    ],
                    Text(
                      widget.text,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}
