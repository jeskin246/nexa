import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../common/glass_container.dart';

/// Top Telemetry Bar showing CPU, RAM, Disk, Active Window, and Time.
class SystemTelemetryBar extends StatelessWidget {
  final double cpuPercent;
  final double ramPercent;
  final double diskPercent;
  final String activeWindow;
  final bool isConnected;
  final VoidCallback onSettingsPressed;
  final VoidCallback? onAutoReplyPressed;

  const SystemTelemetryBar({
    super.key,
    required this.cpuPercent,
    required this.ramPercent,
    required this.diskPercent,
    required this.activeWindow,
    required this.isConnected,
    required this.onSettingsPressed,
    this.onAutoReplyPressed,
  });

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      borderRadius: 16,
      child: Row(
        children: [
          // Logo
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: isConnected ? NexaTheme.successGreen : NexaTheme.errorRed,
                  boxShadow: [
                    BoxShadow(
                      color: (isConnected ? NexaTheme.successGreen : NexaTheme.errorRed)
                          .withValues(alpha: 0.5),
                      blurRadius: 6,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 6),
              const Text(
                'NEXA',
                style: TextStyle(
                  color: NexaTheme.textPrimary,
                  fontWeight: FontWeight.w800,
                  fontSize: 13,
                  letterSpacing: 1.2,
                ),
              ),
            ],
          ),

          const SizedBox(width: 12),

          // Telemetry Gauges
          Expanded(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _TelemetryItem(
                    label: 'CPU',
                    value: '${cpuPercent.toInt()}%',
                    icon: Icons.memory_rounded,
                    color: cpuPercent > 80 ? NexaTheme.errorRed : NexaTheme.accentCyan,
                  ),
                  const SizedBox(width: 20),
                  _TelemetryItem(
                    label: 'RAM',
                    value: '${ramPercent.toInt()}%',
                    icon: Icons.pie_chart_outline_rounded,
                    color: ramPercent > 85 ? NexaTheme.warningAmber : NexaTheme.accentPurple,
                  ),
                  const SizedBox(width: 20),
                  _TelemetryItem(
                    label: 'DISK',
                    value: '${diskPercent.toInt()}%',
                    icon: Icons.storage_rounded,
                    color: NexaTheme.accentBlue,
                  ),
                  if (activeWindow.isNotEmpty) ...[
                    const SizedBox(width: 20),
                    Row(
                      children: [
                        const Icon(Icons.window_rounded, size: 14, color: NexaTheme.textDim),
                        const SizedBox(width: 6),
                        ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 180),
                          child: Text(
                            activeWindow,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: NexaTheme.textSecondary,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),

          if (onAutoReplyPressed != null)
            IconButton(
              icon: const Icon(Icons.bolt_rounded, size: 20, color: Color(0xFF00F2FE)),
              onPressed: onAutoReplyPressed,
              tooltip: 'NEXA Power',
            ),

          // Settings Icon
          IconButton(
            icon: const Icon(Icons.settings_outlined, size: 18, color: NexaTheme.textSecondary),
            onPressed: onSettingsPressed,
            tooltip: 'NEXA Settings',
          ),
        ],
      ),
    );
  }
}

class _TelemetryItem extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _TelemetryItem({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 6),
        Text(
          '$label: ',
          style: const TextStyle(color: NexaTheme.textDim, fontSize: 12),
        ),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.w700,
            fontSize: 12,
          ),
        ),
      ],
    );
  }
}
