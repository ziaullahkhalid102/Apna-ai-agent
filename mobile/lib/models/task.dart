class TaskStep {
  final String id;
  final String action;
  final String description;
  final String status;
  final Map<String, dynamic>? result;
  final String? error;

  TaskStep({
    required this.id,
    required this.action,
    required this.description,
    required this.status,
    this.result,
    this.error,
  });

  factory TaskStep.fromJson(Map<String, dynamic> json) {
    return TaskStep(
      id: json['id'] ?? '',
      action: json['action'] ?? '',
      description: json['description'] ?? '',
      status: json['status'] ?? 'pending',
      result: json['result'],
      error: json['error'],
    );
  }
}

class AgentTask {
  final String id;
  final String command;
  final String status;
  final List<TaskStep> steps;
  final Map<String, dynamic>? result;
  final String? error;
  final String createdAt;
  final String? startedAt;
  final String? completedAt;

  AgentTask({
    required this.id,
    required this.command,
    required this.status,
    this.steps = const [],
    this.result,
    this.error,
    required this.createdAt,
    this.startedAt,
    this.completedAt,
  });

  factory AgentTask.fromJson(Map<String, dynamic> json) {
    return AgentTask(
      id: json['id'] ?? '',
      command: json['command'] ?? '',
      status: json['status'] ?? 'pending',
      steps: (json['steps'] as List<dynamic>?)
              ?.map((s) => TaskStep.fromJson(s))
              .toList() ??
          [],
      result: json['result'],
      error: json['error'],
      createdAt: json['created_at'] ?? '',
      startedAt: json['started_at'],
      completedAt: json['completed_at'],
    );
  }

  bool get isRunning => status == 'running';
  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';
  bool get isWaitingHuman => status == 'waiting_human';
}

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final String? taskId;

  ChatMessage({
    required this.text,
    required this.isUser,
    DateTime? timestamp,
    this.taskId,
  }) : timestamp = timestamp ?? DateTime.now();
}
