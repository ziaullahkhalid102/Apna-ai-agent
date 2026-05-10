import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl;
  final http.Client _client = http.Client();

  ApiService({required this.baseUrl});

  Future<Map<String, dynamic>> createTask(String command) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/tasks'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'command': command}),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to create task: ${response.statusCode}');
  }

  Future<Map<String, dynamic>> getTask(String taskId) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/v1/tasks/$taskId'),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get task: ${response.statusCode}');
  }

  Future<List<dynamic>> listTasks({int limit = 20}) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/v1/tasks?limit=$limit'),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['tasks'] ?? [];
    }
    throw Exception('Failed to list tasks: ${response.statusCode}');
  }

  Future<void> provideHumanInput(
      String taskId, Map<String, dynamic> inputData) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/tasks/$taskId/human-input'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'input_data': inputData}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to provide input: ${response.statusCode}');
    }
  }

  Future<void> cancelTask(String taskId) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/tasks/$taskId/cancel'),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to cancel task: ${response.statusCode}');
    }
  }

  Future<void> enableHumanControl() async {
    await _client.post(
      Uri.parse('$baseUrl/api/v1/browser/human-control/enable'),
    );
  }

  Future<void> disableHumanControl() async {
    await _client.post(
      Uri.parse('$baseUrl/api/v1/browser/human-control/disable'),
    );
  }

  Future<Map<String, dynamic>> getStatus() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/v1/status'),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get status: ${response.statusCode}');
  }

  Future<List<dynamic>> listModels() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/api/v1/llm/models'),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['models'] ?? [];
    }
    throw Exception('Failed to list models: ${response.statusCode}');
  }

  void dispose() {
    _client.close();
  }
}
