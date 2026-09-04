import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:window_manager/window_manager.dart';
import 'core/constants.dart';
import 'core/theme.dart';
import 'core/websocket_service.dart';
import 'manager/auto_reply_manager.dart';
import 'manager/system_automation_manager.dart';
import 'screens/main_shell_screen.dart';
import 'services/agent_service.dart';
import 'services/scheduled_whatsapp_service.dart';
import 'services/system_monitor_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Desktop window configuration
  if (!kIsWeb && (Platform.isWindows || Platform.isLinux || Platform.isMacOS)) {
    try {
      await windowManager.ensureInitialized();
      WindowOptions windowOptions = const WindowOptions(
        size: Size(1280, 800),
        minimumSize: Size(NexaConstants.minWindowWidth, NexaConstants.minWindowHeight),
        center: true,
        backgroundColor: Colors.transparent,
        skipTaskbar: false,
        titleBarStyle: TitleBarStyle.normal,
        title: 'NEXA — Agentic AI Personal OS Assistant',
      );
      windowManager.waitUntilReadyToShow(windowOptions, () async {
        await windowManager.show();
        await windowManager.focus();
      });
    } catch (e) {
      debugPrint('[NEXA WindowManager] Init skipped: $e');
    }
  }

  runApp(const NexoApp());
}

class NexoApp extends StatelessWidget {
  const NexoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AutoReplyManager()),
        ChangeNotifierProvider(create: (_) => SystemAutomationManager()),
        ChangeNotifierProvider(create: (_) => ScheduledWhatsAppService()),
        ChangeNotifierProvider(create: (_) {
          final ws = WebSocketService();
          ws.connect();
          return ws;
        }),
        ChangeNotifierProxyProvider<WebSocketService, AgentService>(
          create: (ctx) => AgentService(ctx.read<WebSocketService>()),
          update: (ctx, ws, previous) => previous ?? AgentService(ws),
        ),
        ChangeNotifierProxyProvider<WebSocketService, SystemMonitorService>(
          create: (ctx) => SystemMonitorService(ctx.read<WebSocketService>()),
          update: (ctx, ws, previous) => previous ?? SystemMonitorService(ws),
        ),
      ],
      child: MaterialApp(
        title: NexaConstants.appName,
        debugShowCheckedModeBanner: false,
        theme: NexaTheme.darkTheme,
        home: const MainShellScreen(),
      ),
    );
  }
}
