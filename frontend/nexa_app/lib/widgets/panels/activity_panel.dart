import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../common/glass_container.dart';

/// Real-time Activity Feed Panel showing live agent step execution status.
class ActivityPanel extends StatelessWidget {
  final List<Map<String, dynamic>> activities;

  const ActivityPanel({super.key, required this.activities});

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.monitor_heart_rounded, color: NexaTheme.accentCyan, size: 18),
              SizedBox(width: 8),
              Text(
                'AGENT ACTIVITY',
                style: TextStyle(
                  color: NexaTheme.textPrimary,
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                  letterSpacing: 1.2,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Divider(color: NexaTheme.glassBorder, height: 1),
          const SizedBox(height: 12),
          Expanded(
            child: activities.isEmpty
                ? const Center(
                    child: Text(
                      'No active tasks running',
                      style: TextStyle(color: NexaTheme.textDim, fontSize: 13),
                    ),
                  )
                : ListView.separated(
                    itemCount: activities.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final item = activities[index];
                      final type = item['type'] as String? ?? 'info';
                      final message = item['message'] as String? ?? '';

                      return _ActivityItemRow(type: type, message: message);
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

class _ActivityItemRow extends StatelessWidget {
  final String type;
  final String message;

  const _ActivityItemRow({required this.type, required this.message});

  Widget _getIcon() {
    switch (type) {
      case 'user':
        return const Icon(Icons.person_outline, size: 16, color: NexaTheme.accentBlue);
      case 'status':
        return const Icon(Icons.bolt, size: 16, color: NexaTheme.accentCyan);
      case 'plan':
        return const Icon(Icons.account_tree_outlined, size: 16, color: NexaTheme.accentPurple);
      case 'step':
        return const Icon(Icons.check_circle_outline, size: 16, color: NexaTheme.successGreen);
      case 'confirm_request':
        return const Icon(Icons.warning_amber_rounded, size: 16, color: NexaTheme.warningAmber);
      case 'complete':
        return const Icon(Icons.task_alt, size: 16, color: NexaTheme.successGreen);
      case 'error':
        return const Icon(Icons.error_outline, size: 16, color: NexaTheme.errorRed);
      default:
        return const Icon(Icons.circle_outlined, size: 14, color: NexaTheme.textDim);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 2),
          child: _getIcon(),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            message,
            style: const TextStyle(
              color: NexaTheme.textPrimary,
              fontSize: 13,
              height: 1.3,
            ),
          ),
        ),
      ],
    );
  }
}
