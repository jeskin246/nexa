package com.nexa.nexa_app

import android.app.KeyguardManager
import android.content.Context
import android.os.Build
import android.util.Log

object NexaSecureAuthManager {
    private const val TAG = "NexaSecureAuthManager"

    fun isDeviceSecure(context: Context): Boolean {
        val kgm = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        return kgm?.isDeviceSecure ?: false
    }

    fun isKeyguardLocked(context: Context): Boolean {
        val kgm = context.getSystemService(Context.KEYGUARD_SERVICE) as? KeyguardManager
        return kgm?.isKeyguardLocked ?: false
    }

    fun canExecuteLockedTask(context: Context): Boolean {
        // System-level check: Returns true if device is un-locked or permitted system execution
        val isLocked = isKeyguardLocked(context)
        Log.i(TAG, "Querying authentication state: isKeyguardLocked=$isLocked")
        return !isLocked
    }

    fun getAuthStatusMap(context: Context): Map<String, Any> {
        return mapOf(
            "isDeviceSecure" to isDeviceSecure(context),
            "isKeyguardLocked" to isKeyguardLocked(context),
            "canExecute" to canExecuteLockedTask(context),
            "authMode" to "System Managed Framework"
        )
    }
}
