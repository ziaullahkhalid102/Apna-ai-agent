import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/agent_provider.dart';
import '../widgets/stream_viewer.dart';
import '../widgets/chat_panel.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  double _dividerPosition = 0.4;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final streamHeight = constraints.maxHeight * _dividerPosition;
          final chatHeight =
              constraints.maxHeight * (1 - _dividerPosition) - 8;

          return Column(
            children: [
              SizedBox(
                height: streamHeight,
                child: const StreamViewer(),
              ),
              GestureDetector(
                onVerticalDragUpdate: (details) {
                  setState(() {
                    _dividerPosition += details.delta.dy / constraints.maxHeight;
                    _dividerPosition = _dividerPosition.clamp(0.2, 0.7);
                  });
                },
                child: Container(
                  height: 8,
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  child: Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade400,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                ),
              ),
              SizedBox(
                height: chatHeight,
                child: const ChatPanel(),
              ),
            ],
          );
        },
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      title: Row(
        children: [
          Icon(Icons.smart_toy, color: Colors.tealAccent.shade700, size: 24),
          const SizedBox(width: 8),
          const Text(
            'Apna AI Agent',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
          ),
        ],
      ),
      actions: [
        Consumer<AgentProvider>(
          builder: (context, agent, _) {
            return Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (agent.isConnected)
                  IconButton(
                    icon: Icon(
                      agent.humanControl
                          ? Icons.front_hand
                          : Icons.smart_toy_outlined,
                      color: agent.humanControl
                          ? Colors.orange
                          : Colors.tealAccent.shade700,
                    ),
                    onPressed: agent.toggleHumanControl,
                    tooltip: agent.humanControl
                        ? 'Resume agent'
                        : 'Take manual control',
                  ),
                Container(
                  margin: const EdgeInsets.only(right: 8),
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: agent.isConnected ? Colors.green : Colors.red,
                  ),
                ),
              ],
            );
          },
        ),
        IconButton(
          icon: const Icon(Icons.settings),
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            );
          },
        ),
      ],
    );
  }
}
