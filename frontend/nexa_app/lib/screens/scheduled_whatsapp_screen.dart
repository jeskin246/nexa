import 'package:flutter/material.dart';
import '../ui/system_automation_view.dart';

class ScheduledWhatsAppScreen extends StatelessWidget {
  const ScheduledWhatsAppScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0xFF0D0F18),
      body: SafeArea(
        child: SystemAutomationView(),
      ),
    );
  }
}
