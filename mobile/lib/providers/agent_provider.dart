import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';
import '../services/stream_service.dart';

class AgentProvider extends ChangeNotifier {
  late ApiService _api;
  late StreamService _stream;

  String _serverUrl = 'http://10.0.2.2:8000';
  String _wsUrl = 'ws://10.0.2.2:8000';
  bool _isConnected = false;
  bool _humanControl = false;
  Uint8List? _currentFrame;
  final List<ChatMessage> _messages = [];
  final List<AgentTask> _tasks = [];
  AgentTask? _currentTask;

  String get serverUrl => _serverUrl;
  bool get isConnected => _isConnected;
  bool get humanControl => _humanControl;
  Uint8List? get currentFrame => _currentFrame;
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  List<AgentTask> get tasks => List.unmodifiable(_tasks);
  AgentTask? get currentTask => _currentTask;

  AgentProvider() {
    _api = ApiService(baseUrl: _serverUrl);
    _stream = StreamService();
    _setupStreamListeners();
  }

  void _setupStreamListeners() {
    _stream.frameStream.listen((frame) {
      _currentFrame = frame;
      notifyListeners();
    });

    _stream.eventStream.listen((event) {
      final type = event['type'] ?? '';
      if (type == 'disconnected') {
        _isConnected = false;
        notifyListeners();
      } else if (type == 'task_completed' || type == 'task_failed') {
        _refreshCurrentTask();
      } else if (type == 'human_input_required') {
        final prompt = event['prompt'] ?? 'Human input needed';
        _addAgentMessage(
            '🔔 Human intervention required: $prompt\nPlease take over control.');
      } else if (type == 'step_updated') {
        _refreshCurrentTask();
      }
    });
  }

  Future<void> connect(String url) async {
    _serverUrl = url;
    _wsUrl = url.replaceFirst('http', 'ws');
    _api = ApiService(baseUrl: _serverUrl);

    try {
      await _api.getStatus();
      _stream.connectStream(_wsUrl);
      _isConnected = true;
      _addAgentMessage('Connected to server at $_serverUrl');
    } catch (e) {
      _isConnected = false;
      _addAgentMessage('Failed to connect: $e');
    }
    notifyListeners();
  }

  Future<void> sendCommand(String command) async {
    _messages.add(ChatMessage(text: command, isUser: true));
    notifyListeners();

    try {
      final result = await _api.createTask(command);
      final taskId = result['task_id'];
      _addAgentMessage('Task created (ID: ${taskId.substring(0, 8)}...) — executing...');

      _stream.connectTaskEvents(_wsUrl, taskId);
      await _refreshTask(taskId);
    } catch (e) {
      _addAgentMessage('Error: $e');
    }
    notifyListeners();
  }

  Future<void> toggleHumanControl() async {
    try {
      if (_humanControl) {
        await _api.disableHumanControl();
        _humanControl = false;
        _addAgentMessage('Agent resumed — human control disabled.');
      } else {
        await _api.enableHumanControl();
        _humanControl = true;
        _addAgentMessage('Human control enabled — you can interact with the browser.');
      }
    } catch (e) {
      _addAgentMessage('Error toggling control: $e');
    }
    notifyListeners();
  }

  Future<void> provideInput(Map<String, dynamic> data) async {
    if (_currentTask != null) {
      try {
        await _api.provideHumanInput(_currentTask!.id, data);
        _addAgentMessage('Input provided — agent resuming.');
      } catch (e) {
        _addAgentMessage('Error: $e');
      }
    }
    notifyListeners();
  }

  Future<void> cancelCurrentTask() async {
    if (_currentTask != null) {
      try {
        await _api.cancelTask(_currentTask!.id);
        _addAgentMessage('Task cancelled.');
      } catch (e) {
        _addAgentMessage('Error: $e');
      }
    }
    notifyListeners();
  }

  void sendTap(double x, double y) {
    if (_humanControl) {
      _stream.sendClick(x, y);
    }
  }

  Future<void> _refreshTask(String taskId) async {
    try {
      final data = await _api.getTask(taskId);
      _currentTask = AgentTask.fromJson(data);
      notifyListeners();
    } catch (_) {}
  }

  Future<void> _refreshCurrentTask() async {
    if (_currentTask != null) {
      await _refreshTask(_currentTask!.id);
    }
  }

  void _addAgentMessage(String text) {
    _messages.add(ChatMessage(text: text, isUser: false));
    notifyListeners();
  }

  @override
  void dispose() {
    _api.dispose();
    _stream.dispose();
    super.dispose();
  }
}
