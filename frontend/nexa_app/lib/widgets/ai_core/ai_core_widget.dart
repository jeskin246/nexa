import 'dart:math';
import 'package:flutter/material.dart';
import '../../core/theme.dart';
import '../../models/agent_state.dart';
import 'neural_network_painter.dart';
import 'particle_system.dart';
import 'waveform_painter.dart';

/// Central NEXA AI Core Visualization Widget.
class AICoreWidget extends StatefulWidget {
  final AgentState state;
  final String message;
  final double size;

  const AICoreWidget({
    super.key,
    required this.state,
    required this.message,
    this.size = 280,
  });

  @override
  State<AICoreWidget> createState() => _AICoreWidgetState();
}

class _AICoreWidgetState extends State<AICoreWidget> with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late AnimationController _rotationController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);

    _rotationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 8),
    )..repeat();

    _pulseAnimation = Tween<double>(begin: 0.92, end: 1.08).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void didUpdateWidget(AICoreWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.state != widget.state) {
      switch (widget.state) {
        case AgentState.thinking:
        case AgentState.executing:
          _pulseController.duration = const Duration(milliseconds: 800);
          _rotationController.duration = const Duration(seconds: 3);
          break;
        case AgentState.planning:
          _pulseController.duration = const Duration(milliseconds: 1200);
          _rotationController.duration = const Duration(seconds: 5);
          break;
        default:
          _pulseController.duration = const Duration(milliseconds: 2000);
          _rotationController.duration = const Duration(seconds: 8);
          break;
      }
      _pulseController.repeat(reverse: true);
      _rotationController.repeat();
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _rotationController.dispose();
    super.dispose();
  }

  Color _getStateColor() {
    switch (widget.state) {
      case AgentState.idle:
        return NexaTheme.accentCyan;
      case AgentState.listening:
        return NexaTheme.accentCyan;
      case AgentState.thinking:
        return NexaTheme.accentPurple;
      case AgentState.planning:
        return NexaTheme.accentBlue;
      case AgentState.executing:
        return NexaTheme.accentCyan;
      case AgentState.observing:
        return NexaTheme.accentPink;
      case AgentState.waiting:
        return NexaTheme.warningAmber;
      case AgentState.success:
        return NexaTheme.successGreen;
      case AgentState.error:
        return NexaTheme.errorRed;
    }
  }

  IconData _getStateIcon() {
    switch (widget.state) {
      case AgentState.idle:
        return Icons.auto_awesome;
      case AgentState.listening:
        return Icons.mic;
      case AgentState.thinking:
        return Icons.psychology;
      case AgentState.planning:
        return Icons.account_tree;
      case AgentState.executing:
        return Icons.bolt;
      case AgentState.observing:
        return Icons.visibility;
      case AgentState.waiting:
        return Icons.help_outline;
      case AgentState.success:
        return Icons.check_circle_outline;
      case AgentState.error:
        return Icons.warning_amber_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getStateColor();

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: widget.size,
          height: widget.size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Ambient Particles
              ParticleSystemWidget(
                count: widget.state.isActive ? 45 : 25,
                baseColor: color,
              ),

              // State-specific CustomPainters
              if (widget.state == AgentState.listening)
                AnimatedBuilder(
                  animation: _rotationController,
                  builder: (context, _) => CustomPaint(
                    size: Size(widget.size, widget.size),
                    painter: WaveformPainter(
                      animationValue: _rotationController.value,
                      color: color,
                    ),
                  ),
                ),

              if (widget.state == AgentState.planning)
                AnimatedBuilder(
                  animation: _rotationController,
                  builder: (context, _) => CustomPaint(
                    size: Size(widget.size, widget.size),
                    painter: NeuralNetworkPainter(
                      animationValue: _rotationController.value,
                    ),
                  ),
                ),

              // Outer Rotating Ring
              AnimatedBuilder(
                animation: _rotationController,
                builder: (context, child) {
                  return Transform.rotate(
                    angle: _rotationController.value * 2 * pi,
                    child: Container(
                      width: widget.size * 0.85,
                      height: widget.size * 0.85,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: color.withValues(alpha: 0.3),
                          width: 1.5,
                        ),
                      ),
                    ),
                  );
                },
              ),

              // Inner Glowing Orb
              ScaleTransition(
                scale: _pulseAnimation,
                child: Container(
                  width: widget.size * 0.55,
                  height: widget.size * 0.55,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        color.withValues(alpha: 0.9),
                        color.withValues(alpha: 0.4),
                        Colors.transparent,
                      ],
                      stops: const [0.2, 0.7, 1.0],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: color.withValues(alpha: 0.5),
                        blurRadius: 35,
                        spreadRadius: 8,
                      ),
                    ],
                  ),
                  child: Center(
                    child: Icon(
                      _getStateIcon(),
                      size: widget.size * 0.22,
                      color: NexaTheme.bgDeep,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 16),

        // Status Label & Description
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          child: Column(
            key: ValueKey('${widget.state}_${widget.message}'),
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: color.withValues(alpha: 0.4)),
                ),
                child: Text(
                  widget.state.label.toUpperCase(),
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.5,
                    fontSize: 12,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                widget.message,
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: NexaTheme.textSecondary,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
