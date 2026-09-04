import 'dart:async';
import 'package:flutter/services.dart';

class NexoNotificationService {
  static const MethodChannel _methodChannel =
      MethodChannel('com.nexa.nexa_app/notification_listener');
  static const EventChannel _eventChannel =
      EventChannel('com.nexa.nexa_app/notification_events');

  static Future<bool> isNotificationPermissionGranted() async {
    try {
      final bool result =
          await _methodChannel.invokeMethod('isNotificationPermissionGranted');
      return result;
    } on PlatformException catch (_) {
      return false;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> openNotificationPermissionSettings() async {
    try {
      final bool result = await _methodChannel
          .invokeMethod('openNotificationPermissionSettings');
      return result;
    } on PlatformException catch (_) {
      return false;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> sendDirectReply(
      String notificationKey, String replyText) async {
    try {
      final bool result = await _methodChannel.invokeMethod('sendDirectReply', {
        'notificationKey': notificationKey,
        'replyText': replyText,
      });
      return result;
    } on PlatformException catch (_) {
      return false;
    } catch (_) {
      return false;
    }
  }

  static Stream<Map<String, dynamic>>? _stream;

  static Stream<Map<String, dynamic>> get notificationStream {
    _stream ??= _eventChannel
        .receiveBroadcastStream()
        .map((dynamic event) => Map<String, dynamic>.from(event as Map));
    return _stream!;
  }
}
