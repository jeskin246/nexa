/// Agent states matching the backend
enum AgentState {
  idle,
  listening,
  thinking,
  planning,
  executing,
  observing,
  waiting,
  success,
  error;

  static AgentState fromString(String s) {
    return AgentState.values.firstWhere(
      (e) => e.name == s,
      orElse: () => AgentState.idle,
    );
  }

  String get label {
    switch (this) {
      case AgentState.idle:
        return 'Ready';
      case AgentState.listening:
        return 'Listening';
      case AgentState.thinking:
        return 'Thinking';
      case AgentState.planning:
        return 'Planning';
      case AgentState.executing:
        return 'Executing';
      case AgentState.observing:
        return 'Observing';
      case AgentState.waiting:
        return 'Waiting';
      case AgentState.success:
        return 'Complete';
      case AgentState.error:
        return 'Error';
    }
  }

  bool get isActive =>
      this == AgentState.thinking ||
      this == AgentState.planning ||
      this == AgentState.executing ||
      this == AgentState.observing;
}
