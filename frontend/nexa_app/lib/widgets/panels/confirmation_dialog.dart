import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../common/glass_container.dart';
import '../common/glow_button.dart';

/// Permission confirmation dialog modal widget.
class ConfirmationDialogWidget extends StatelessWidget {
  final Map<String, dynamic> request;
  final ValueChanged<bool> onRespond;

  const ConfirmationDialogWidget({
    super.key,
    required this.request,
    required this.onRespond,
  });

  @override
  Widget build(BuildContext context) {
    final toolName = request['tool_name'] as String? ?? 'Tool';
    final description = request['description'] as String? ?? 'Execute action?';
    final params = request['parameters'] as Map<String, dynamic>? ?? {};

    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
      child: GlassContainer(
        width: 480,
        padding: const EdgeInsets.all(24),
        borderColor: NexaTheme.warningAmber,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: const [
                Icon(Icons.shield_outlined, color: NexaTheme.warningAmber, size: 24),
                SizedBox(width: 10),
                Text(
                  'CONFIRMATION REQUIRED',
                  style: TextStyle(
                    color: NexaTheme.warningAmber,
                    fontWeight: FontWeight.w800,
                    fontSize: 14,
                    letterSpacing: 1.2,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              description,
              style: const TextStyle(
                color: NexaTheme.textPrimary,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Tool: $toolName',
              style: const TextStyle(
                color: NexaTheme.textSecondary,
                fontSize: 13,
                fontFamily: 'monospace',
              ),
            ),
            if (params.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: NexaTheme.bgSecondary,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: NexaTheme.glassBorder),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: params.entries.map((e) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        '${e.key}: ${e.value}',
                        style: const TextStyle(
                          color: NexaTheme.textDim,
                          fontSize: 12,
                          fontFamily: 'monospace',
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: NexaTheme.textPrimary,
                    side: const BorderSide(color: NexaTheme.glassBorder),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  ),
                  onPressed: () => onRespond(false),
                  child: const Text('Deny'),
                ),
                const SizedBox(width: 12),
                GlowButton(
                  text: 'Approve & Continue',
                  color: NexaTheme.successGreen,
                  onPressed: () => onRespond(true),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
