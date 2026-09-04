import 'package:flutter/material.dart';
import '../ui/auto_reply_screen.dart';
import 'home_screen.dart';

/// NEXA Main Navigation Shell combining the Original GUI Home OS Control Center
/// and the NEXA Power (Auto-Reply) module.
class MainShellScreen extends StatefulWidget {
  final int initialIndex;
  const MainShellScreen({super.key, this.initialIndex = 0});

  @override
  State<MainShellScreen> createState() => _MainShellScreenState();
}

class _MainShellScreenState extends State<MainShellScreen> {
  late int _currentIndex;

  final List<Widget> _pages = const [
    HomeScreen(),
    AutoReplyScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF0F121C),
          border: const Border(
            top: BorderSide(color: Color(0xFF232A3E), width: 1),
          ),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF00F2FE).withValues(alpha: 0.08),
              blurRadius: 12,
              spreadRadius: 1,
            )
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() {
              _currentIndex = index;
            });
          },
          backgroundColor: const Color(0xFF0F121C),
          selectedItemColor: const Color(0xFF00F2FE),
          unselectedItemColor: Colors.white38,
          selectedFontSize: 12,
          unselectedFontSize: 11,
          selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold),
          type: BottomNavigationBarType.fixed,
          elevation: 0,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.developer_board_rounded),
              activeIcon: Icon(Icons.developer_board_rounded, color: Color(0xFF00F2FE)),
              label: 'NEXA OS Home',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.bolt_rounded),
              activeIcon: Icon(Icons.bolt_rounded, color: Color(0xFF00F2FE)),
              label: 'NEXA Power',
            ),
          ],
        ),
      ),
    );
  }
}
