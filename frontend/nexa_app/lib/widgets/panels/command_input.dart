import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../common/glass_container.dart';

/// Futuristic Command Input Bar widget with voice support and emergency stop.
class CommandInputBar extends StatefulWidget {
  final ValueChanged<String> onSubmit;
  final VoidCallback onVoicePressed;
  final VoidCallback onStopPressed;
  final bool isWorking;
  final bool isListening;
  final TextEditingController? controller;

  const CommandInputBar({
    super.key,
    required this.onSubmit,
    required this.onVoicePressed,
    required this.onStopPressed,
    required this.isWorking,
    this.isListening = false,
    this.controller,
  });

  @override
  State<CommandInputBar> createState() => _CommandInputBarState();
}

class _CommandInputBarState extends State<CommandInputBar> {
  late TextEditingController _controller;
  final _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _controller = widget.controller ?? TextEditingController();
  }

  void _handleSubmit() {
    final text = _controller.text.trim();
    if (text.isNotEmpty) {
      widget.onSubmit(text);
      _controller.clear();
    }
  }

  @override
  void dispose() {
    if (widget.controller == null) {
      _controller.dispose();
    }
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GlassContainer(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      borderRadius: 24,
      borderColor: widget.isListening
          ? NexaTheme.accentCyan
          : (widget.isWorking ? NexaTheme.accentPurple : null),
      child: Row(
        children: [
          // Voice Button
          IconButton(
            icon: Icon(
              widget.isListening ? Icons.mic : Icons.mic_none_rounded,
              color: widget.isListening ? NexaTheme.accentCyan : NexaTheme.textSecondary,
            ),
            tooltip: 'Voice Command',
            onPressed: widget.onVoicePressed,
          ),

          const SizedBox(width: 8),

          // Text Field
          Expanded(
            child: TextField(
              controller: _controller,
              focusNode: _focusNode,
              onSubmitted: (_) => _handleSubmit(),
              style: const TextStyle(color: NexaTheme.textPrimary, fontSize: 15),
              decoration: InputDecoration(
                hintText: widget.isListening
                    ? 'Listening...'
                    : 'Ask NEXA anything...',
                hintStyle: TextStyle(
                  color: widget.isListening
                      ? NexaTheme.accentCyan.withValues(alpha: 0.7)
                      : NexaTheme.textDim,
                ),
                border: InputBorder.none,
                enabledBorder: InputBorder.none,
                focusedBorder: InputBorder.none,
                filled: false,
                contentPadding: EdgeInsets.zero,
              ),
            ),
          ),

          const SizedBox(width: 8),

          // Action Button (Send or Stop)
          if (widget.isWorking)
            IconButton(
              icon: const Icon(Icons.stop_circle_rounded, color: NexaTheme.errorRed, size: 28),
              tooltip: 'Emergency Stop Agent',
              onPressed: widget.onStopPressed,
            )
          else
            Container(
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: NexaTheme.coreGradient,
              ),
              child: IconButton(
                icon: const Icon(Icons.arrow_upward_rounded, color: NexaTheme.bgDeep, size: 20),
                tooltip: 'Start Agent Task',
                onPressed: _handleSubmit,
              ),
            ),
        ],
      ),
    );
  }
}
