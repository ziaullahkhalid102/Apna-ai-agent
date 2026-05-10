import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/agent_provider.dart';

class StreamViewer extends StatelessWidget {
  const StreamViewer({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AgentProvider>(
      builder: (context, agent, _) {
        if (!agent.isConnected) {
          return _buildDisconnected(context);
        }
        if (agent.currentFrame == null) {
          return _buildLoading();
        }
        return _buildStream(context, agent, agent.currentFrame!);
      },
    );
  }

  Widget _buildDisconnected(BuildContext context) {
    return Container(
      color: Colors.black,
      child: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off, color: Colors.white54, size: 48),
            SizedBox(height: 12),
            Text(
              'Not connected',
              style: TextStyle(color: Colors.white54, fontSize: 16),
            ),
            SizedBox(height: 4),
            Text(
              'Enter server URL to connect',
              style: TextStyle(color: Colors.white38, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoading() {
    return Container(
      color: Colors.black,
      child: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: Colors.tealAccent),
            SizedBox(height: 16),
            Text(
              'Waiting for stream...',
              style: TextStyle(color: Colors.white54),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStream(
      BuildContext context, AgentProvider agent, Uint8List frame) {
    return GestureDetector(
      onTapDown: (details) {
        if (agent.humanControl) {
          final box = context.findRenderObject() as RenderBox;
          final localPos = box.globalToLocal(details.globalPosition);
          final scaleX = 1280 / box.size.width;
          final scaleY = 720 / box.size.height;
          agent.sendTap(localPos.dx * scaleX, localPos.dy * scaleY);
        }
      },
      child: Stack(
        fit: StackFit.expand,
        children: [
          Image.memory(
            frame,
            fit: BoxFit.contain,
            gaplessPlayback: true,
          ),
          if (agent.humanControl)
            Positioned(
              top: 8,
              right: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.8),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.touch_app, color: Colors.white, size: 14),
                    SizedBox(width: 4),
                    Text('MANUAL',
                        style: TextStyle(color: Colors.white, fontSize: 11)),
                  ],
                ),
              ),
            ),
          Positioned(
            top: 8,
            left: 8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: agent.isConnected
                    ? Colors.green.withValues(alpha: 0.7)
                    : Colors.red.withValues(alpha: 0.7),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    agent.isConnected ? 'LIVE' : 'OFF',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
