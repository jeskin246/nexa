package com.nexa.nexa_app

import android.app.KeyguardManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.PowerManager
import android.util.Log

object NexaDeviceStateManager {
    private const val TAG = "NexaDeviceStateManager"

    var isScreenOnState: Boolean = true
    var isLockedState: Boolean = false
    var isUserPresentState: Boolean = true

    fun init(context: Context) {
        try {
            val filter = IntentFilter().apply {
                addAction(Intent.ACTION_SCREEN_ON)
                addAction(Intent.ACTION_SCREEN_OFF)
                addAction(Intent.ACTION_USER_PRESENT)
            }

            val receiver = object : BroadcastReceiver() {
                override fun onReceive(ctx: Context?, intent: Intent?) {
                    if (intent == null || ctx == null) return
                    try {
                        when (intent.action) {
                            Intent.ACTION_SCREEN_ON -> {
                                isScreenOnState = true
                                Log.i(TAG, "Device State Event: SCREEN_ON")
                            }
                            Intent.ACTION_SCREEN_OFF -> {
                                isScreenOnState = false
                                isUserPresentState = false
                                Log.i(TAG, "Device State Event: SCREEN_OFF")
                            }
                            Intent.ACTION_USER_PRESENT -> {
                                isUserPresentState = true
                                isLockedState = false
                                Log.i(TAG, "Device State Event: USER_PRESENT (Device Authenticated)")
                                NexaTaskService.onDeviceUnlocked(ctx)
                            }
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "Error in NexaDeviceStateManager onReceive: ${e.message}", e)
                    }
                }
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                context.applicationContext.registerReceiver(
                    receiver,
                    filter,
                    Context.RECEIVER_NOT_EXPORTED
                )
            } else {
                context.applicationContext.registerReceiver(receiver, filter)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error registering NexaDeviceStateManager receiver: ${e.message}", e)
        }

        isScreenOnState = isScreenOn(context)
        isLockedState = isDeviceLocked(context)
        isUserPresentState = !isLockedState
    }

    fun isScreenOn(context: Context): Boolean {
        val pm = context.getSystemService(Context.POWER_SERVICE) as? PowerManager
        return pm?.isInteractive ?: true
    }

    fun isDeviceLocked(context: Context): Boolean {
        val kgm = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        return kgm?.isKeyguardLocked ?: false
    }

    fun isDeviceAuthenticated(context: Context): Boolean {
        val kgm = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        return if (kgm != null) {
            !kgm.isKeyguardLocked
        } else {
            true
        }
    }

    fun isUserUnlocked(context: Context): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            val um = context.getSystemService(Context.USER_SERVICE) as? android.os.UserManager
            um?.isUserUnlocked ?: true
        } else {
            true
        }
    }

    fun getDeviceStateSummary(context: Context): Map<String, Any> {
        return mapOf(
            "isScreenOn" to isScreenOn(context),
            "isDeviceLocked" to isDeviceLocked(context),
            "isDeviceAuthenticated" to isDeviceAuthenticated(context),
            "isUserUnlocked" to isUserUnlocked(context),
            "timestamp" to System.currentTimeMillis()
        )
    }
}
