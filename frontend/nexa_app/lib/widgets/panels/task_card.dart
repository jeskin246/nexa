import 'package:flutter/material.dart';
import 'package:percent_indicator/linear_percent_indicator.dart';
import '../../core/theme.dart';
import '../../models/task.dart';
import '../common/glass_container.dart';

/// Active Task Card showing goal, progress percentage, step checklist, and controls.
class TaskCardWidget extends StatelessWidget {
  final AgentTask task;
  final VoidCallback onStopPressed;

  const TaskCardWidget({
    super.key,
    required this.task,
    required this.onStopPressed,
  });

  @override
  Widget build(BuildContext context) {
    final pct = (task.progress * 100).clamp(0, 100).toInt();

    return GlassContainer(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'ACTIVE TASK',
                style: TextStyle(
                  color: NexaTheme.accentCyan,
                  fontWeight: FontWeight.w700,
                  fontSize: 12,
                  letterSpacing: 1.2,
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close_rounded, size: 18, color: NexaTheme.textDim),
                onPressed: onStopPressed,
                tooltip: 'Stop Task',
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            task.goal,
            style: const TextStyle(
              color: NexaTheme.textPrimary,
              fontWeight: FontWeight.w600,
              fontSize: 15,
            ),
          ),
          const SizedBox(height: 14),

          // Progress Bar
          Row(
            children: [
              Expanded(
                child: LinearPercentIndicator(
                  lineHeight: 8.0,
                  percent: task.progress.clamp(0.0, 1.0),
                  padding: EdgeInsets.zero,
                  backgroundColor: NexaTheme.bgSecondary,
                  linearGradient: NexaTheme.coreGradient,
                  barRadius: const Radius.circular(4),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '$pct%',
                style: const TextStyle(
                  color: NexaTheme.accentCyan,
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),

          // Steps list
          if (task.steps.isNotEmpty) ...[
            ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 160),
              child: ListView.separated(
                shrinkWrap: true,
                itemCount: task.steps.length,
                separatorBuilder: (context, index) => const SizedBox(height: 6),
                itemBuilder: (context, idx) {
                  final step = task.steps[idx];
                  return _StepRow(step: step);
                },
              ),
            ),
          ],

          if (task.summary != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: NexaTheme.successGreen.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: NexaTheme.successGreen.withValues(alpha: 0.3)),
              ),
              child: Text(
                task.summary!,
                style: const TextStyle(color: NexaTheme.textPrimary, fontSize: 13),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _StepRow extends StatelessWidget {
  final TaskStep step;

  const _StepRow({required this.step});

  @override
  Widget build(BuildContext context) {
    IconData icon;
    Color color;

    switch (step.status) {
      case StepStatus.completed:
        icon = Icons.check_circle_rounded;
        color = NexaTheme.successGreen;
        break;
      case StepStatus.inProgress:
        icon = Icons.pending_rounded;
        color = NexaTheme.accentCyan;
        break;
      case StepStatus.failed:
        icon = Icons.cancel_rounded;
        color = NexaTheme.errorRed;
        break;
      case StepStatus.skipped:
        icon = Icons.remove_circle_outline_rounded;
        color = NexaTheme.textDim;
        break;
      case StepStatus.pending:
        icon = Icons.radio_button_unchecked_rounded;
        color = NexaTheme.textDim;
        break;
    }

    return Row(
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            step.description,
            style: TextStyle(
              color: step.status == StepStatus.completed
                  ? NexaTheme.textSecondary
                  : NexaTheme.textPrimary,
              fontSize: 13,
              decoration: step.status == StepStatus.completed
                  ? TextDecoration.lineThrough
                  : null,
            ),
          ),
        ),
      ],
    );
  }
}
