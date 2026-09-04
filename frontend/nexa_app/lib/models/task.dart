/// Task step status
enum StepStatus { pending, inProgress, completed, failed, skipped }

/// A single step in a task
class TaskStep {
  final int index;
  final String description;
  final String? toolName;
  StepStatus status;
  String? result;
  String? error;

  TaskStep({
    required this.index,
    required this.description,
    this.toolName,
    this.status = StepStatus.pending,
    this.result,
    this.error,
  });

  factory TaskStep.fromJson(Map<String, dynamic> json) {
    return TaskStep(
      index: json['index'] ?? 0,
      description: json['description'] ?? '',
      toolName: json['tool_name'],
      status: parseStatus(json['status'] ?? 'pending'),
      result: json['result'],
      error: json['error'],
    );
  }

  static StepStatus parseStatus(String s) {
    switch (s) {
      case 'in_progress':
        return StepStatus.inProgress;
      case 'completed':
        return StepStatus.completed;
      case 'failed':
        return StepStatus.failed;
      case 'skipped':
        return StepStatus.skipped;
      default:
        return StepStatus.pending;
    }
  }
}

/// An active task being processed by the agent
class AgentTask {
  final String taskId;
  final String goal;
  final List<TaskStep> steps;
  double progress;
  String status;
  String? summary;
  DateTime createdAt;

  AgentTask({
    required this.taskId,
    required this.goal,
    this.steps = const [],
    this.progress = 0,
    this.status = 'created',
    this.summary,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();
}
