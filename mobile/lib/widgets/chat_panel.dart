import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/agent_provider.dart';
import '../models/task.dart';

class ChatPanel extends StatefulWidget {
  const ChatPanel({super.key});

  @override
  State<ChatPanel> createState() => _ChatPanelState();
}

class _ChatPanelState extends State<ChatPanel> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _send(AgentProvider agent) {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    agent.sendCommand(text);
    _controller.clear();
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AgentProvider>(
      builder: (context, agent, _) {
        _scrollToBottom();
        return Column(
          children: [
            if (agent.currentTask != null) _buildTaskBar(agent),
            Expanded(child: _buildMessageList(agent)),
            _buildInputBar(agent),
          ],
        );
      },
    );
  }

  Widget _buildTaskBar(AgentProvider agent) {
    final task = agent.currentTask!;
    final completedSteps =
        task.steps.where((s) => s.status == 'completed').length;
    final progress =
        task.steps.isEmpty ? 0.0 : completedSteps / task.steps.length;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).dividerColor.withValues(alpha: 0.3),
          ),
        ),
      ),
      child: Row(
        children: [
          _buildStatusIcon(task.status),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  task.command,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 4),
                LinearProgressIndicator(
                  value: progress,
                  minHeight: 3,
                  backgroundColor: Colors.grey.shade300,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    task.isFailed ? Colors.red : Colors.tealAccent.shade700,
                  ),
                ),
              ],
            ),
          ),
          if (task.isRunning || task.isWaitingHuman)
            IconButton(
              icon: const Icon(Icons.cancel_outlined, size: 20),
              onPressed: agent.cancelCurrentTask,
              tooltip: 'Cancel task',
            ),
        ],
      ),
    );
  }

  Widget _buildStatusIcon(String status) {
    switch (status) {
      case 'running':
        return const SizedBox(
          width: 18,
          height: 18,
          child: CircularProgressIndicator(strokeWidth: 2),
        );
      case 'completed':
        return const Icon(Icons.check_circle, color: Colors.green, size: 18);
      case 'failed':
        return const Icon(Icons.error, color: Colors.red, size: 18);
      case 'waiting_human':
        return const Icon(Icons.front_hand, color: Colors.orange, size: 18);
      default:
        return const Icon(Icons.hourglass_empty, color: Colors.grey, size: 18);
    }
  }

  Widget _buildMessageList(AgentProvider agent) {
    if (agent.messages.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.smart_toy_outlined,
                size: 64, color: Colors.tealAccent.shade700),
            const SizedBox(height: 16),
            const Text(
              'Apna AI Agent',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Tell me what to do — I\'ll execute it live.',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 14),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemCount: agent.messages.length,
      itemBuilder: (context, index) {
        final msg = agent.messages[index];
        return _buildMessageBubble(msg);
      },
    );
  }

  Widget _buildMessageBubble(ChatMessage msg) {
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        decoration: BoxDecoration(
          color: msg.isUser
              ? Colors.tealAccent.shade700
              : Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: msg.isUser ? const Radius.circular(4) : null,
            bottomLeft: !msg.isUser ? const Radius.circular(4) : null,
          ),
        ),
        child: Text(
          msg.text,
          style: TextStyle(
            color: msg.isUser ? Colors.white : null,
            fontSize: 14,
          ),
        ),
      ),
    );
  }

  Widget _buildInputBar(AgentProvider agent) {
    return Container(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 8),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(
          top: BorderSide(
            color: Theme.of(context).dividerColor.withValues(alpha: 0.3),
          ),
        ),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                focusNode: _focusNode,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(agent),
                decoration: InputDecoration(
                  hintText: agent.isConnected
                      ? 'Enter a command...'
                      : 'Connect to server first...',
                  hintStyle: TextStyle(color: Colors.grey.shade500),
                  filled: true,
                  fillColor:
                      Theme.of(context).colorScheme.surfaceContainerHighest,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
                enabled: agent.isConnected,
              ),
            ),
            const SizedBox(width: 8),
            FloatingActionButton.small(
              onPressed:
                  agent.isConnected ? () => _send(agent) : null,
              backgroundColor: Colors.tealAccent.shade700,
              child: const Icon(Icons.send, size: 18, color: Colors.white),
            ),
          ],
        ),
      ),
    );
  }
}
