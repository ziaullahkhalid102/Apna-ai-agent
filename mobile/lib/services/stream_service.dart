import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:web_socket_channel/web_socket_channel.dart';

class StreamService {
  WebSocketChannel? _channel;
  final StreamController<Uint8List> _frameController =
      StreamController<Uint8List>.broadcast();
  final StreamController<Map<String, dynamic>> _eventController =
      StreamController<Map<String, dynamic>>.broadcast();
  bool _connected = false;

  Stream<Uint8List> get frameStream => _frameController.stream;
  Stream<Map<String, dynamic>> get eventStream => _eventController.stream;
  bool get isConnected => _connected;

  void connectStream(String wsUrl) {
    _disconnect();
    try {
      _channel = WebSocketChannel.connect(Uri.parse('$wsUrl/ws/stream'));
      _connected = true;
      _channel!.stream.listen(
        (data) {
          try {
            final message = jsonDecode(data);
            if (message['type'] == 'frame') {
              final bytes = base64Decode(message['data']);
              _frameController.add(bytes);
            } else {
              _eventController.add(message);
            }
          } catch (_) {}
        },
        onDone: () {
          _connected = false;
          _eventController.add({'type': 'disconnected'});
        },
        onError: (error) {
          _connected = false;
          _eventController.add({'type': 'error', 'message': error.toString()});
        },
      );
    } catch (e) {
      _connected = false;
    }
  }

  void connectTaskEvents(String wsUrl, String taskId) {
    try {
      final channel =
          WebSocketChannel.connect(Uri.parse('$wsUrl/ws/tasks/$taskId'));
      channel.stream.listen(
        (data) {
          try {
            final message = jsonDecode(data);
            _eventController.add(message);
          } catch (_) {}
        },
        onDone: () {},
        onError: (_) {},
      );
    } catch (_) {}
  }

  void sendInput(Map<String, dynamic> input) {
    if (_connected && _channel != null) {
      _channel!.sink.add(jsonEncode(input));
    }
  }

  void sendClick(double x, double y) {
    sendInput({'type': 'mouse_click', 'x': x, 'y': y});
  }

  void sendKey(String key) {
    sendInput({'type': 'keyboard', 'key': key});
  }

  void _disconnect() {
    _channel?.sink.close();
    _channel = null;
    _connected = false;
  }

  void dispose() {
    _disconnect();
    _frameController.close();
    _eventController.close();
  }
}
