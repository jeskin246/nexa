import 'dart:math';
import 'package:flutter/material.dart';
import '../../core/theme.dart';

class Particle {
  double x;
  double y;
  double radius;
  double vx;
  double vy;
  double opacity;
  Color color;

  Particle({
    required this.x,
    required this.y,
    required this.radius,
    required this.vx,
    required this.vy,
    required this.opacity,
    required this.color,
  });
}

class ParticlePainter extends CustomPainter {
  final List<Particle> particles;
  final double animationValue;

  ParticlePainter({required this.particles, required this.animationValue});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);

    for (var particle in particles) {
      final paint = Paint()
        ..color = particle.color.withValues(alpha: particle.opacity)
        ..style = PaintingStyle.fill;

      final pos = Offset(
        center.dx + particle.x * (size.width / 2),
        center.dy + particle.y * (size.height / 2),
      );

      canvas.drawCircle(pos, particle.radius, paint);
    }
  }

  @override
  bool shouldRepaint(covariant ParticlePainter oldDelegate) => true;
}

class ParticleSystemWidget extends StatefulWidget {
  final int count;
  final Color baseColor;

  const ParticleSystemWidget({
    super.key,
    this.count = 30,
    this.baseColor = NexaTheme.accentCyan,
  });

  @override
  State<ParticleSystemWidget> createState() => _ParticleSystemWidgetState();
}

class _ParticleSystemWidgetState extends State<ParticleSystemWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  final List<Particle> _particles = [];
  final Random _rng = Random();

  @override
  void initState() {
    super.initState();
    _initParticles();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    )..repeat();

    _controller.addListener(_updateParticles);
  }

  void _initParticles() {
    _particles.clear();
    for (int i = 0; i < widget.count; i++) {
      final angle = _rng.nextDouble() * 2 * pi;
      final dist = 0.2 + _rng.nextDouble() * 0.7;
      _particles.add(
        Particle(
          x: cos(angle) * dist,
          y: sin(angle) * dist,
          radius: 1.5 + _rng.nextDouble() * 2.5,
          vx: (cos(angle + pi / 2) * 0.002 + (_rng.nextDouble() - 0.5) * 0.001),
          vy: (sin(angle + pi / 2) * 0.002 + (_rng.nextDouble() - 0.5) * 0.001),
          opacity: 0.2 + _rng.nextDouble() * 0.6,
          color: _rng.nextBool() ? NexaTheme.accentCyan : NexaTheme.accentPurple,
        ),
      );
    }
  }

  void _updateParticles() {
    for (var p in _particles) {
      p.x += p.vx;
      p.y += p.vy;

      // Wrap boundary
      final distSq = p.x * p.x + p.y * p.y;
      if (distSq > 0.9) {
        p.vx = -p.vx;
        p.vy = -p.vy;
      }
    }
    setState(() {});
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return CustomPainterWidget(
      painter: ParticlePainter(
        particles: _particles,
        animationValue: _controller.value,
      ),
    );
  }
}

class CustomPainterWidget extends StatelessWidget {
  final CustomPainter painter;

  const CustomPainterWidget({super.key, required this.painter});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: painter,
      child: const SizedBox.expand(),
    );
  }
}
